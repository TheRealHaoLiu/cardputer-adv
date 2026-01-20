#
# Small ftp server for ESP8266 Micropython
# Based on the work of chrisgp - Christopher Popp and pfalcon - Paul Sokolovsky
#
# The server accepts passive mode only. It runs in background.
# Start the server with:
#
# import uftpd
# uftpd.start([port = 21][, verbose = level])
#
# port is the port number (default 21)
# verbose controls the level of printed activity messages, values 0, 1, 2
#
# Copyright (c) 2016 Christopher Popp (initial ftp server framework)
# Copyright (c) 2016 Paul Sokolovsky (background execution control structure)
# Copyright (c) 2016 Robert Hammelrath (putting the pieces together and a
# few extensions)
# Copyright (c) 2020 Jan Wieck Use separate FTP servers per socket for STA + AP mode
# Copyright (c) 2021 JD Smith Use a preallocated buffer and improve error handling.
# Distributed under MIT License
#
# Modified for Cardputer: Added read-only mode, path protection, and authentication
#
import errno
import gc
import socket
import sys
from time import localtime, sleep_ms

import network
import uos
from micropython import alloc_emergency_exception_buf

# constant definitions
_CHUNK_SIZE = const(1024)
_SO_REGISTER_HANDLER = const(20)
_COMMAND_TIMEOUT = const(300)
_DATA_TIMEOUT = const(100)
_DATA_PORT = const(13333)

# Global variables
ftpsockets = []
datasocket = None
client_list = []
verbose_l = 0
client_busy = False

# Cardputer extensions: read-only mode, authentication, protected paths
read_only = False  # When True, reject write commands on /flash and /sd
auth_enabled = False  # When True, require valid credentials
auth_user = "ftp"  # Default username
auth_password = "cardputer"  # Default password
protected_paths = ["/system"]  # Always read-only regardless of read_only flag

_month_name = (
    "",
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
)


def set_read_only(enabled):
    """Enable or disable read-only mode for /flash and /sd."""
    global read_only
    read_only = enabled


def get_read_only():
    """Get current read-only mode state."""
    return read_only


def set_auth(enabled, user=None, password=None):
    """Enable or disable authentication, optionally set credentials."""
    global auth_enabled, auth_user, auth_password
    auth_enabled = enabled
    if user is not None:
        auth_user = user
    if password is not None:
        auth_password = password


def get_auth():
    """Get current authentication state."""
    return auth_enabled


def is_path_protected(path):
    """Check if path is in a protected (always read-only) directory."""
    for protected in protected_paths:
        if path == protected or path.startswith(protected + "/"):
            return True
    return False


def is_write_allowed(path):
    """Check if write operations are allowed for the given path."""
    # Protected paths are always read-only
    if is_path_protected(path):
        return False
    # If read_only mode is enabled, no writes to /flash or /sd
    return not read_only


class FTP_client:
    def __init__(self, ftpsocket, local_addr):
        self.command_client, self.remote_addr = ftpsocket.accept()
        self.remote_addr = self.remote_addr[0]
        self.command_client.settimeout(_COMMAND_TIMEOUT)
        log_msg(1, "FTP Command connection from:", self.remote_addr)
        self.command_client.setsockopt(
            socket.SOL_SOCKET, _SO_REGISTER_HANDLER, self.exec_ftp_command
        )
        self.command_client.sendall(f"220 Hello, this is the {sys.platform}.\r\n")
        self.cwd = "/"
        self.fromname = None
        self.logged_in = False  # Track login state for authentication
        self.act_data_addr = self.remote_addr
        self.DATA_PORT = 20
        self.active = True
        self.pasv_data_addr = local_addr

    def send_list_data(self, path, data_client, full):
        try:
            for fname in uos.listdir(path):
                data_client.sendall(self.make_description(path, fname, full))
        except Exception:
            path, pattern = self.split_path(path)
            try:
                for fname in uos.listdir(path):
                    if self.fncmp(fname, pattern):
                        data_client.sendall(self.make_description(path, fname, full))
            except Exception:
                pass

    def make_description(self, path, fname, full):
        global _month_name
        if full:
            stat = uos.stat(self.get_absolute_path(path, fname))
            file_permissions = "drwxr-xr-x" if (stat[0] & 0o170000 == 0o040000) else "-rw-r--r--"
            file_size = stat[6]
            tm = stat[7] & 0xFFFFFFFF
            tm = localtime(tm if tm < 0x80000000 else tm - 0x100000000)
            if tm[0] != localtime()[0]:
                description = f"{file_permissions} 1 owner group {file_size:>10} {_month_name[tm[1]]} {tm[2]:2} {tm[0]:>5} {fname}\r\n"
            else:
                description = f"{file_permissions} 1 owner group {file_size:>10} {_month_name[tm[1]]} {tm[2]:2} {tm[3]:02}:{tm[4]:02} {fname}\r\n"
        else:
            description = fname + "\r\n"
        return description

    def send_file_data(self, path, data_client):
        buffer = bytearray(_CHUNK_SIZE)
        mv = memoryview(buffer)
        with open(path, "rb") as file:
            bytes_read = file.readinto(buffer)
            while bytes_read > 0:
                data_client.write(mv[0:bytes_read])
                bytes_read = file.readinto(buffer)
            data_client.close()

    def save_file_data(self, path, data_client, mode):
        buffer = bytearray(_CHUNK_SIZE)
        mv = memoryview(buffer)
        with open(path, mode) as file:
            bytes_read = data_client.readinto(buffer)
            while bytes_read > 0:
                file.write(mv[0:bytes_read])
                bytes_read = data_client.readinto(buffer)
            data_client.close()

    def get_absolute_path(self, cwd, payload):
        if payload.startswith("/"):
            cwd = "/"
        for token in payload.split("/"):
            if token == "..":
                cwd = self.split_path(cwd)[0]
            elif token != "." and token != "":
                if cwd == "/":
                    cwd += token
                else:
                    cwd = cwd + "/" + token
        return cwd

    def split_path(self, path):
        tail = path.split("/")[-1]
        head = path[: -(len(tail) + 1)]
        return ("/" if head == "" else head, tail)

    def fncmp(self, fname, pattern):
        pi = 0
        si = 0
        while pi < len(pattern) and si < len(fname):
            if (fname[si] == pattern[pi]) or (pattern[pi] == "?"):
                si += 1
                pi += 1
            else:
                if pattern[pi] == "*":
                    if pi == len(pattern.rstrip("*?")):
                        return True
                    while si < len(fname):
                        if self.fncmp(fname[si:], pattern[pi + 1 :]):
                            return True
                        else:
                            si += 1
                    return False
                else:
                    return False
        return pi == len(pattern.rstrip("*")) and si == len(fname)

    def open_dataclient(self):
        if self.active:
            data_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            data_client.settimeout(_DATA_TIMEOUT)
            data_client.connect((self.act_data_addr, self.DATA_PORT))
            log_msg(1, "FTP Data connection with:", self.act_data_addr)
        else:
            data_client, data_addr = datasocket.accept()
            log_msg(1, "FTP Data connection with:", data_addr[0])
        return data_client

    def exec_ftp_command(self, cl):
        global datasocket
        global client_busy
        global auth_enabled, auth_user, auth_password

        try:
            gc.collect()

            try:
                data = cl.readline().decode("utf-8").rstrip("\r\n")
            except OSError:
                data = ""

            if len(data) <= 0:
                log_msg(1, "*** No data, assume QUIT")
                close_client(cl)
                return

            if client_busy:
                cl.sendall("400 Device busy.\r\n")
                return
            client_busy = True

            command = data.split()[0].upper()
            payload = data[len(command) :].lstrip()
            path = self.get_absolute_path(self.cwd, payload)
            log_msg(1, f"Command={command}, Payload={payload}")

            # Check authentication for commands that require login
            if auth_enabled and not self.logged_in and command not in ("USER", "PASS", "QUIT"):
                cl.sendall("530 Not logged in.\r\n")
                client_busy = False
                return

            if command == "USER":
                if auth_enabled:
                    self._auth_user = payload
                    cl.sendall("331 Password required.\r\n")
                else:
                    self.logged_in = True
                    cl.sendall("230 Logged in.\r\n")
            elif command == "PASS":
                if auth_enabled:
                    if (
                        hasattr(self, "_auth_user")
                        and self._auth_user == auth_user
                        and payload == auth_password
                    ):
                        self.logged_in = True
                        cl.sendall("230 Logged in.\r\n")
                    else:
                        cl.sendall("530 Login incorrect.\r\n")
                else:
                    self.logged_in = True
                    cl.sendall("230 Logged in.\r\n")
            elif command == "SYST":
                cl.sendall("215 UNIX Type: L8\r\n")
            elif command in ("TYPE", "NOOP", "ABOR"):
                cl.sendall("200 OK\r\n")
            elif command == "QUIT":
                cl.sendall("221 Bye.\r\n")
                close_client(cl)
            elif command == "PWD" or command == "XPWD":
                cl.sendall(f'257 "{self.cwd}"\r\n')
            elif command == "CWD" or command == "XCWD":
                try:
                    if (uos.stat(path)[0] & 0o170000) == 0o040000:
                        self.cwd = path
                        cl.sendall("250 OK\r\n")
                    else:
                        cl.sendall("550 Fail\r\n")
                except Exception:
                    cl.sendall("550 Fail\r\n")
            elif command == "PASV":
                cl.sendall(
                    "227 Entering Passive Mode ({},{},{}).\r\n".format(
                        self.pasv_data_addr.replace(".", ","), _DATA_PORT >> 8, _DATA_PORT % 256
                    )
                )
                self.active = False
            elif command == "PORT":
                items = payload.split(",")
                if len(items) >= 6:
                    self.act_data_addr = ".".join(items[:4])
                    if self.act_data_addr == "127.0.1.1":
                        self.act_data_addr = self.remote_addr
                    self.DATA_PORT = int(items[4]) * 256 + int(items[5])
                    cl.sendall("200 OK\r\n")
                    self.active = True
                else:
                    cl.sendall("504 Fail\r\n")
            elif command == "LIST" or command == "NLST":
                if payload.startswith("-"):
                    option = payload.split()[0].lower()
                    path = self.get_absolute_path(self.cwd, payload[len(option) :].lstrip())
                else:
                    option = ""
                try:
                    data_client = self.open_dataclient()
                    cl.sendall("150 Directory listing:\r\n")
                    self.send_list_data(path, data_client, command == "LIST" or "l" in option)
                    cl.sendall("226 Done.\r\n")
                    data_client.close()
                except Exception:
                    cl.sendall("550 Fail\r\n")
                    if data_client is not None:
                        data_client.close()
            elif command == "RETR":
                try:
                    data_client = self.open_dataclient()
                    cl.sendall("150 Opened data connection.\r\n")
                    self.send_file_data(path, data_client)
                    data_client = None
                    cl.sendall("226 Done.\r\n")
                except Exception:
                    cl.sendall("550 Fail\r\n")
                    if data_client is not None:
                        data_client.close()
            elif command == "STOR" or command == "APPE":
                # Check write permission
                if not is_write_allowed(path):
                    if is_path_protected(path):
                        cl.sendall("550 Path is protected (read-only).\r\n")
                    else:
                        cl.sendall("550 Server is in read-only mode.\r\n")
                else:
                    try:
                        data_client = self.open_dataclient()
                        cl.sendall("150 Opened data connection.\r\n")
                        self.save_file_data(path, data_client, "wb" if command == "STOR" else "ab")
                        data_client = None
                        cl.sendall("226 Done.\r\n")
                    except Exception:
                        cl.sendall("550 Fail\r\n")
                        if data_client is not None:
                            data_client.close()
            elif command == "SIZE":
                try:
                    cl.sendall(f"213 {uos.stat(path)[6]}\r\n")
                except Exception:
                    cl.sendall("550 Fail\r\n")
            elif command == "MDTM":
                try:
                    tm = localtime(uos.stat(path)[8])
                    cl.sendall("213 {:04d}{:02d}{:02d}{:02d}{:02d}{:02d}\r\n".format(*tm[0:6]))
                except Exception:
                    cl.sendall("550 Fail\r\n")
            elif command == "STAT":
                if payload == "":
                    cl.sendall(
                        f"211-Connected to ({self.remote_addr})\r\n"
                        f"    Data address ({self.pasv_data_addr})\r\n"
                        "    TYPE: Binary STRU: File MODE: Stream\r\n"
                        f"    Session timeout {_COMMAND_TIMEOUT}\r\n"
                        f"211 Client count is {len(client_list)}\r\n"
                    )
                else:
                    cl.sendall("213-Directory listing:\r\n")
                    self.send_list_data(path, cl, True)
                    cl.sendall("213 Done.\r\n")
            elif command == "DELE":
                # Check write permission
                if not is_write_allowed(path):
                    if is_path_protected(path):
                        cl.sendall("550 Path is protected (read-only).\r\n")
                    else:
                        cl.sendall("550 Server is in read-only mode.\r\n")
                else:
                    try:
                        uos.remove(path)
                        cl.sendall("250 OK\r\n")
                    except Exception:
                        cl.sendall("550 Fail\r\n")
            elif command == "RNFR":
                # Check write permission for rename source
                if not is_write_allowed(path):
                    if is_path_protected(path):
                        cl.sendall("550 Path is protected (read-only).\r\n")
                    else:
                        cl.sendall("550 Server is in read-only mode.\r\n")
                else:
                    try:
                        uos.stat(path)
                        self.fromname = path
                        cl.sendall("350 Rename from\r\n")
                    except Exception:
                        cl.sendall("550 Fail\r\n")
            elif command == "RNTO":
                # Check write permission for rename destination
                if not is_write_allowed(path):
                    if is_path_protected(path):
                        cl.sendall("550 Path is protected (read-only).\r\n")
                    else:
                        cl.sendall("550 Server is in read-only mode.\r\n")
                else:
                    try:
                        uos.rename(self.fromname, path)
                        cl.sendall("250 OK\r\n")
                    except Exception:
                        cl.sendall("550 Fail\r\n")
                    self.fromname = None
            elif command == "CDUP" or command == "XCUP":
                self.cwd = self.get_absolute_path(self.cwd, "..")
                cl.sendall("250 OK\r\n")
            elif command == "RMD" or command == "XRMD":
                # Check write permission
                if not is_write_allowed(path):
                    if is_path_protected(path):
                        cl.sendall("550 Path is protected (read-only).\r\n")
                    else:
                        cl.sendall("550 Server is in read-only mode.\r\n")
                else:
                    try:
                        uos.rmdir(path)
                        cl.sendall("250 OK\r\n")
                    except Exception:
                        cl.sendall("550 Fail\r\n")
            elif command == "MKD" or command == "XMKD":
                # Check write permission
                if not is_write_allowed(path):
                    if is_path_protected(path):
                        cl.sendall("550 Path is protected (read-only).\r\n")
                    else:
                        cl.sendall("550 Server is in read-only mode.\r\n")
                else:
                    try:
                        uos.mkdir(path)
                        cl.sendall("250 OK\r\n")
                    except Exception:
                        cl.sendall("550 Fail\r\n")
            elif command == "SITE":
                # Disabled for security
                cl.sendall("502 SITE command disabled.\r\n")
            else:
                cl.sendall("502 Unsupported command.\r\n")
        except OSError as err:
            if verbose_l > 0:
                log_msg(1, "Exception in exec_ftp_command:")
                sys.print_exception(err)
            if err.errno in (errno.ECONNABORTED, errno.ENOTCONN):
                close_client(cl)
        except Exception as err:
            log_msg(1, f"Exception in exec_ftp_command: {err}")
        client_busy = False


def log_msg(level, *args):
    global verbose_l
    if verbose_l >= level:
        print(*args)


def close_client(cl):
    cl.setsockopt(socket.SOL_SOCKET, _SO_REGISTER_HANDLER, None)
    cl.close()
    for i, client in enumerate(client_list):
        if client.command_client == cl:
            del client_list[i]
            break


def accept_ftp_connect(ftpsocket, local_addr):
    try:
        client_list.append(FTP_client(ftpsocket, local_addr))
    except Exception:
        log_msg(1, "Attempt to connect failed")
        try:
            temp_client, temp_addr = ftpsocket.accept()
            temp_client.close()
        except Exception:
            pass


def num_ip(ip):
    items = ip.split(".")
    return int(items[0]) << 24 | int(items[1]) << 16 | int(items[2]) << 8 | int(items[3])


def stop():
    global ftpsockets, datasocket
    global client_list
    global client_busy

    for client in client_list:
        client.command_client.setsockopt(socket.SOL_SOCKET, _SO_REGISTER_HANDLER, None)
        client.command_client.close()
    del client_list
    client_list = []  # noqa: F841 - reassigning global
    client_busy = False
    for sock in ftpsockets:
        sock.setsockopt(socket.SOL_SOCKET, _SO_REGISTER_HANDLER, None)
        sock.close()
    ftpsockets = []
    if datasocket is not None:
        datasocket.close()
        datasocket = None


def start(port=21, verbose=0, splash=True):
    global ftpsockets, datasocket
    global verbose_l
    global client_list
    global client_busy

    alloc_emergency_exception_buf(100)
    verbose_l = verbose
    client_list = []
    client_busy = False

    for interface in [network.AP_IF, network.STA_IF]:
        wlan = network.WLAN(interface)
        if not wlan.active():
            continue

        ifconfig = wlan.ifconfig()
        addr = socket.getaddrinfo(ifconfig[0], port)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(addr[0][4])
        sock.listen(1)
        sock.setsockopt(
            socket.SOL_SOCKET,
            _SO_REGISTER_HANDLER,
            lambda s, ip=ifconfig[0]: accept_ftp_connect(s, ip),
        )
        ftpsockets.append(sock)
        if splash:
            print(f"FTP server started on {ifconfig[0]}:{port}")

    datasocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    datasocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    datasocket.bind(("0.0.0.0", _DATA_PORT))
    datasocket.listen(1)
    datasocket.settimeout(10)


def restart(port=21, verbose=0, splash=True):
    stop()
    sleep_ms(200)
    start(port, verbose, splash)

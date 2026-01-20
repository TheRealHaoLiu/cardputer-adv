"""
FTP Server - Remote File Transfer
==================================

An FTP server that allows remote file access from any FTP client.
Supports all WiFi modes (STA, AP, STA+AP) and provides SD card access.

FEATURES:
    - Access /flash, /sd (if present), and /system (read-only)
    - Read-only mode toggle to protect files
    - Optional authentication

STORAGE:
    /flash  - Internal flash storage [RW or RO based on toggle]
    /sd     - MicroSD card if inserted [RW or RO based on toggle]
    /system - System files [Always RO - protected]

CONTROLS:
    R   = Toggle Read-Only mode (for /flash and /sd)
    A   = Toggle Authentication (login required)
    ESC = Exit to launcher

FTP CLIENT EXAMPLES:
    ftp <device-ip>
    FileZilla: Connect to <device-ip>, port 21
    Mobile: Any FTP file manager app
"""

import asyncio
import os
import sys

for path in ["/flash/lib", "/remote/lib"]:
    if path not in sys.path:
        sys.path.insert(0, path)

import machine
from app_base import AppBase
from M5 import Lcd, Widgets

# Screen dimensions
SCREEN_W = 240
SCREEN_H = 135

# SD Card pins for Cardputer
SD_SCK = 40
SD_MISO = 39
SD_MOSI = 14
SD_CS = 12
SD_FREQ = 1000000

# NVS keys for FTP settings
NVS_NAMESPACE = "ftp"
NVS_KEY_READONLY = "readonly"
NVS_KEY_AUTH = "auth"
NVS_KEY_USERNAME = "user"
NVS_KEY_PASSWORD = "pass"

# Default credentials
DEFAULT_USERNAME = "ftp"
DEFAULT_PASSWORD = "cardputer"

# View modes
VIEW_MAIN = 0
VIEW_EDIT_CREDS = 1

# Edit fields
FIELD_USERNAME = 0
FIELD_PASSWORD = 1


class FTPServerApp(AppBase):
    """FTP server app with multi-storage support and configurable modes."""

    def __init__(self):
        super().__init__()
        self.name = "FTP Server"
        self._wifi = None
        self._sd = None  # SDCard object
        self._sd_mounted = False
        self._sd_available = False
        self._ftp_running = False
        self._read_only = False
        self._auth_enabled = False
        self._sta_ip = None
        self._ap_ip = None
        self._sta_ssid = None
        self._ap_ssid = None
        self._wifi_mode = "off"  # "off", "sta", "ap", "sta+ap"
        # Credential settings
        self._username = DEFAULT_USERNAME
        self._password = DEFAULT_PASSWORD
        # Credential editing state
        self._view = VIEW_MAIN
        self._edit_field = FIELD_USERNAME
        self._edit_user = ""
        self._edit_pass = ""

    def _get_wifi(self):
        """Get WiFiManager instance."""
        if self._wifi is None:
            try:
                from wifi_manager import get_wifi_manager

                self._wifi = get_wifi_manager()
            except Exception as e:
                print(f"[ftp] WiFi manager error: {e}")
        return self._wifi

    def _load_settings(self):
        """Load saved settings from NVS."""
        try:
            import esp32

            nvs = esp32.NVS(NVS_NAMESPACE)

            try:
                self._read_only = nvs.get_i32(NVS_KEY_READONLY) == 1
            except OSError:
                self._read_only = False

            try:
                self._auth_enabled = nvs.get_i32(NVS_KEY_AUTH) == 1
            except OSError:
                self._auth_enabled = False

            # Load credentials (stored as blobs)
            try:
                buf = bytearray(32)
                length = nvs.get_blob(NVS_KEY_USERNAME, buf)
                self._username = buf[:length].decode("utf-8")
            except OSError:
                self._username = DEFAULT_USERNAME

            try:
                buf = bytearray(32)
                length = nvs.get_blob(NVS_KEY_PASSWORD, buf)
                self._password = buf[:length].decode("utf-8")
            except OSError:
                self._password = DEFAULT_PASSWORD

            print(f"[ftp] Settings loaded: RO={self._read_only}, " f"Auth={self._auth_enabled}")
        except Exception as e:
            print(f"[ftp] Load settings error: {e}")

    def _save_settings(self):
        """Save current settings to NVS."""
        try:
            import esp32

            nvs = esp32.NVS(NVS_NAMESPACE)
            nvs.set_i32(NVS_KEY_READONLY, 1 if self._read_only else 0)
            nvs.set_i32(NVS_KEY_AUTH, 1 if self._auth_enabled else 0)
            nvs.commit()
            print("[ftp] Settings saved")
        except Exception as e:
            print(f"[ftp] Save settings error: {e}")

    def _save_credentials(self):
        """Save credentials to NVS."""
        try:
            import esp32

            nvs = esp32.NVS(NVS_NAMESPACE)
            nvs.set_blob(NVS_KEY_USERNAME, self._username.encode("utf-8"))
            nvs.set_blob(NVS_KEY_PASSWORD, self._password.encode("utf-8"))
            nvs.commit()
            print(f"[ftp] Credentials saved: {self._username}")
        except Exception as e:
            print(f"[ftp] Save credentials error: {e}")

    def _detect_wifi_mode(self):
        """Detect current WiFi mode and get IPs."""
        wifi = self._get_wifi()
        if not wifi:
            self._wifi_mode = "off"
            return

        sta_active = wifi.sta_is_enabled()
        sta_connected = wifi.sta_is_connected()
        ap_active = wifi.ap_is_enabled()

        self._sta_ip = wifi.sta_get_ip() if sta_connected else None
        self._ap_ip = wifi.ap_get_ip() if ap_active else None
        self._sta_ssid = wifi.sta_get_ssid() if sta_connected else None
        self._ap_ssid = wifi.ap_get_ssid() if ap_active else None

        if sta_active and ap_active:
            self._wifi_mode = "sta+ap"
        elif ap_active:
            self._wifi_mode = "ap"
        elif sta_active:
            self._wifi_mode = "sta"
        else:
            self._wifi_mode = "off"

        print(f"[ftp] WiFi mode: {self._wifi_mode}, STA={self._sta_ip}, AP={self._ap_ip}")

    def _check_sd_available(self):
        """Check if SD card is available (try mount/unmount)."""
        try:
            sd = machine.SDCard(
                slot=3,
                sck=machine.Pin(SD_SCK),
                miso=machine.Pin(SD_MISO),
                mosi=machine.Pin(SD_MOSI),
                cs=machine.Pin(SD_CS),
                freq=SD_FREQ,
            )
            try:
                os.mount(sd, "/sd")
                os.umount("/sd")
            except OSError:
                try:  # noqa: SIM105 - contextlib not available in MicroPython
                    os.umount("/sd")
                except OSError:
                    pass
            sd.deinit()
            self._sd_available = True
        except OSError:
            self._sd_available = False

        print(f"[ftp] SD available: {self._sd_available}")

    def _mount_sd(self):
        """Mount the SD card."""
        if self._sd_mounted:
            return True

        try:
            self._sd = machine.SDCard(
                slot=3,
                sck=machine.Pin(SD_SCK),
                miso=machine.Pin(SD_MISO),
                mosi=machine.Pin(SD_MOSI),
                cs=machine.Pin(SD_CS),
                freq=SD_FREQ,
            )
            try:
                os.mount(self._sd, "/sd")
            except OSError:
                try:  # noqa: SIM105 - contextlib not available in MicroPython
                    os.umount("/sd")
                except OSError:
                    pass
                os.mount(self._sd, "/sd")

            self._sd_mounted = True
            print("[ftp] SD card mounted")
            return True
        except Exception as e:
            print(f"[ftp] SD mount error: {e}")
            if self._sd:
                try:  # noqa: SIM105 - contextlib not available in MicroPython
                    self._sd.deinit()
                except Exception:
                    pass
                self._sd = None
            return False

    def _unmount_sd(self):
        """Unmount the SD card."""
        if not self._sd_mounted:
            return

        try:  # noqa: SIM105 - contextlib not available in MicroPython
            os.umount("/sd")
        except OSError:
            pass

        if self._sd:
            try:  # noqa: SIM105 - contextlib not available in MicroPython
                self._sd.deinit()
            except Exception:
                pass
            self._sd = None

        self._sd_mounted = False
        print("[ftp] SD card unmounted")

    def _start_ftp(self):
        """Start the FTP server."""
        if self._ftp_running:
            return True

        try:
            import uftpd

            # Apply settings
            uftpd.set_read_only(self._read_only)
            uftpd.set_auth(self._auth_enabled, self._username, self._password)

            # Start server
            uftpd.start(port=21, verbose=1, splash=False)
            self._ftp_running = True
            print("[ftp] FTP server started")
            return True
        except Exception as e:
            print(f"[ftp] FTP start error: {e}")
            return False

    def _stop_ftp(self):
        """Stop the FTP server."""
        if not self._ftp_running:
            return

        try:
            import uftpd

            uftpd.stop()
        except Exception as e:
            print(f"[ftp] FTP stop error: {e}")

        self._ftp_running = False
        print("[ftp] FTP server stopped")

    def _toggle_readonly(self):
        """Toggle read-only mode."""
        self._read_only = not self._read_only
        self._save_settings()

        # Update running server
        if self._ftp_running:
            try:
                import uftpd

                uftpd.set_read_only(self._read_only)
            except Exception:
                pass

        print(f"[ftp] Read-only: {self._read_only}")
        self._draw_ui()

    def _toggle_auth(self):
        """Toggle authentication."""
        self._auth_enabled = not self._auth_enabled
        self._save_settings()

        # Update running server
        if self._ftp_running:
            try:
                import uftpd

                uftpd.set_auth(self._auth_enabled, self._username, self._password)
            except Exception:
                pass

        print(f"[ftp] Auth: {self._auth_enabled}")
        self._draw_ui()

    def _enter_cred_edit(self):
        """Enter credential editing mode."""
        self._view = VIEW_EDIT_CREDS
        self._edit_field = FIELD_USERNAME
        self._edit_user = self._username
        self._edit_pass = self._password
        self._draw_cred_edit_ui()

    def _save_cred_edit(self):
        """Save edited credentials and exit edit mode."""
        self._username = self._edit_user if self._edit_user else DEFAULT_USERNAME
        self._password = self._edit_pass if self._edit_pass else DEFAULT_PASSWORD
        self._save_credentials()

        # Update running server if auth is enabled
        if self._ftp_running and self._auth_enabled:
            try:
                import uftpd

                uftpd.set_auth(self._auth_enabled, self._username, self._password)
            except Exception:
                pass

        self._view = VIEW_MAIN
        self._draw_ui()

    def _cancel_cred_edit(self):
        """Cancel credential editing and return to main view."""
        self._view = VIEW_MAIN
        self._draw_ui()

    def on_launch(self):
        """Initialize app state."""
        print("[ftp] Launching FTP Server...")
        self._load_settings()
        self._detect_wifi_mode()
        self._check_sd_available()

    def on_view(self):
        """Draw the initial UI."""
        if self._view == VIEW_EDIT_CREDS:
            self._draw_cred_edit_ui()
        else:
            self._draw_ui()

    def _draw_cred_edit_ui(self):
        """Draw credential editing screen."""
        Lcd.fillScreen(Lcd.COLOR.BLACK)
        Lcd.setFont(Widgets.FONTS.ASCII7)
        Lcd.setTextSize(1)

        # Title
        Lcd.setTextColor(Lcd.COLOR.CYAN, Lcd.COLOR.BLACK)
        Lcd.setCursor(10, 5)
        Lcd.print("FTP Credentials")

        # Username field
        y = 22
        Lcd.setTextColor(Lcd.COLOR.WHITE, Lcd.COLOR.BLACK)
        Lcd.setCursor(10, y)
        Lcd.print("Username:")

        box_y = y + 12
        border_color = Lcd.COLOR.WHITE if self._edit_field == FIELD_USERNAME else Lcd.COLOR.DARKGREY
        Lcd.fillRect(10, box_y, SCREEN_W - 20, 16, Lcd.COLOR.DARKGREY)
        Lcd.drawRect(10, box_y, SCREEN_W - 20, 16, border_color)
        Lcd.setTextColor(Lcd.COLOR.WHITE, Lcd.COLOR.DARKGREY)
        Lcd.setCursor(14, box_y + 4)
        user_display = self._edit_user + ("_" if self._edit_field == FIELD_USERNAME else "")
        Lcd.print(user_display[:28])

        # Password field
        y = 55
        Lcd.setTextColor(Lcd.COLOR.WHITE, Lcd.COLOR.BLACK)
        Lcd.setCursor(10, y)
        Lcd.print("Password:")

        box_y = y + 12
        border_color = Lcd.COLOR.WHITE if self._edit_field == FIELD_PASSWORD else Lcd.COLOR.DARKGREY
        Lcd.fillRect(10, box_y, SCREEN_W - 20, 16, Lcd.COLOR.DARKGREY)
        Lcd.drawRect(10, box_y, SCREEN_W - 20, 16, border_color)
        Lcd.setTextColor(Lcd.COLOR.WHITE, Lcd.COLOR.DARKGREY)
        Lcd.setCursor(14, box_y + 4)
        pass_display = "*" * len(self._edit_pass) + (
            "_" if self._edit_field == FIELD_PASSWORD else ""
        )
        Lcd.print(pass_display[:28])

        # Instructions
        Lcd.setTextColor(Lcd.COLOR.DARKGREY, Lcd.COLOR.BLACK)
        Lcd.setCursor(10, SCREEN_H - 25)
        Lcd.print("[Enter] Save  [ESC] Cancel")
        Lcd.setCursor(10, SCREEN_H - 12)
        Lcd.print("[Up/Down] Switch  [Bksp] Delete")

    def _draw_ui(self):
        """Draw the complete UI."""
        Lcd.fillScreen(Lcd.COLOR.BLACK)
        Lcd.setFont(Widgets.FONTS.ASCII7)
        Lcd.setTextSize(1)

        # Title bar with mode indicators
        self._draw_title_bar()

        # Main content based on WiFi state
        if self._wifi_mode == "off":
            self._draw_wifi_error()
        else:
            self._draw_connection_info()

        # Footer with controls
        self._draw_footer()

    def _draw_title_bar(self):
        """Draw title bar with status indicators."""
        y = 3

        # Title
        Lcd.setTextColor(Lcd.COLOR.CYAN, Lcd.COLOR.BLACK)
        Lcd.setCursor(5, y)
        Lcd.print("FTP Server")

        # Mode indicators on the right
        x = SCREEN_W - 5

        # Auth indicator
        auth_str = "Lock" if self._auth_enabled else "Open"
        auth_color = Lcd.COLOR.YELLOW if self._auth_enabled else Lcd.COLOR.GREEN
        Lcd.setTextColor(auth_color, Lcd.COLOR.BLACK)
        x -= len(f"[{auth_str}]") * 6
        Lcd.setCursor(x, y)
        Lcd.print(f"[{auth_str}]")

        # RO/RW indicator
        x -= 8
        rw_str = "RO" if self._read_only else "RW"
        rw_color = Lcd.COLOR.YELLOW if self._read_only else Lcd.COLOR.GREEN
        Lcd.setTextColor(rw_color, Lcd.COLOR.BLACK)
        x -= len(f"[{rw_str}]") * 6
        Lcd.setCursor(x, y)
        Lcd.print(f"[{rw_str}]")

    def _draw_wifi_error(self):
        """Draw WiFi disabled error."""
        Lcd.setTextColor(Lcd.COLOR.RED, Lcd.COLOR.BLACK)
        Lcd.setCursor(50, 45)
        Lcd.print("WiFi disabled")

        Lcd.setTextColor(Lcd.COLOR.DARKGREY, Lcd.COLOR.BLACK)
        Lcd.setCursor(30, 65)
        Lcd.print("Enable WiFi in Settings")

    def _draw_connection_info(self):
        """Draw connection information based on WiFi mode."""
        y = 20

        # Connection info
        if self._wifi_mode == "sta":
            Lcd.setTextColor(Lcd.COLOR.WHITE, Lcd.COLOR.BLACK)
            Lcd.setCursor(5, y)
            ssid = self._sta_ssid or "Not connected"
            Lcd.print(f"WiFi: {ssid[:20]}")

            if self._sta_ip:
                Lcd.setTextColor(Lcd.COLOR.GREEN, Lcd.COLOR.BLACK)
                Lcd.setCursor(5, y + 14)
                Lcd.print(f"Connect to: {self._sta_ip}:21")
            else:
                Lcd.setTextColor(Lcd.COLOR.YELLOW, Lcd.COLOR.BLACK)
                Lcd.setCursor(5, y + 14)
                Lcd.print("Not connected to network")

        elif self._wifi_mode == "ap":
            Lcd.setTextColor(Lcd.COLOR.WHITE, Lcd.COLOR.BLACK)
            Lcd.setCursor(5, y)
            Lcd.print(f"AP: {self._ap_ssid[:20]}")

            Lcd.setTextColor(Lcd.COLOR.GREEN, Lcd.COLOR.BLACK)
            Lcd.setCursor(5, y + 14)
            Lcd.print(f"Connect to: {self._ap_ip}:21")

        elif self._wifi_mode == "sta+ap":
            if self._sta_ip:
                Lcd.setTextColor(Lcd.COLOR.GREEN, Lcd.COLOR.BLACK)
                Lcd.setCursor(5, y)
                Lcd.print(f"WiFi: {self._sta_ip}:21")
            else:
                Lcd.setTextColor(Lcd.COLOR.YELLOW, Lcd.COLOR.BLACK)
                Lcd.setCursor(5, y)
                Lcd.print("WiFi: Not connected")

            Lcd.setTextColor(Lcd.COLOR.GREEN, Lcd.COLOR.BLACK)
            Lcd.setCursor(5, y + 14)
            Lcd.print(f"AP:   {self._ap_ip}:21")

        # Auth info if enabled
        if self._auth_enabled:
            Lcd.setTextColor(Lcd.COLOR.DARKGREY, Lcd.COLOR.BLACK)
            Lcd.setCursor(5, y + 32)
            Lcd.print(f"Login: {self._username} / {self._password}")

        # Storage info
        y_storage = y + 50
        Lcd.setTextColor(Lcd.COLOR.WHITE, Lcd.COLOR.BLACK)
        Lcd.setCursor(5, y_storage)

        flash_mode = "RO" if self._read_only else "RW"
        Lcd.print(f"/flash [{flash_mode}]")

        if self._sd_mounted:
            sd_mode = "RO" if self._read_only else "RW"
            Lcd.setCursor(85, y_storage)
            Lcd.print(f"/sd [{sd_mode}]")
        elif self._sd_available:
            Lcd.setTextColor(Lcd.COLOR.YELLOW, Lcd.COLOR.BLACK)
            Lcd.setCursor(85, y_storage)
            Lcd.print("/sd [--]")
        else:
            Lcd.setTextColor(Lcd.COLOR.DARKGREY, Lcd.COLOR.BLACK)
            Lcd.setCursor(85, y_storage)
            Lcd.print("/sd [N/A]")

        Lcd.setTextColor(Lcd.COLOR.DARKGREY, Lcd.COLOR.BLACK)
        Lcd.setCursor(155, y_storage)
        Lcd.print("/system [RO]")

    def _draw_footer(self):
        """Draw footer with controls."""
        y = SCREEN_H - 12

        Lcd.setTextColor(Lcd.COLOR.DARKGREY, Lcd.COLOR.BLACK)
        Lcd.setCursor(5, y)

        # Show what each key will toggle TO
        r_label = "[R]W" if self._read_only else "[R]O"
        a_label = "[A]Open" if self._auth_enabled else "[A]Lock"

        Lcd.print(f"{r_label} {a_label} [C]red")

        Lcd.setCursor(SCREEN_W - 55, y)
        Lcd.print("[ESC] Exit")

    async def _kb_event_handler(self, event, fw):
        """Handle keyboard events."""
        from keycode import KeyCode

        key = event.key

        # Handle credential editing mode
        if self._view == VIEW_EDIT_CREDS:
            event.status = self._handle_cred_edit_key(key)
            return

        # Main view keys
        if key == ord("r") or key == ord("R"):
            self._toggle_readonly()
            event.status = True
        elif key == ord("a") or key == ord("A"):
            self._toggle_auth()
            event.status = True
        elif key == ord("c") or key == ord("C"):
            self._enter_cred_edit()
            event.status = True

    def _handle_cred_edit_key(self, key):
        """Handle keyboard input in credential editing mode."""
        from keycode import KEY_NAV_DOWN, KEY_NAV_UP, KeyCode

        # ESC cancels editing
        if key == KeyCode.KEYCODE_ESC:
            self._cancel_cred_edit()
            return True

        # Up/Down switches between fields
        if key in (KEY_NAV_UP, KEY_NAV_DOWN):
            if self._edit_field == FIELD_USERNAME:
                self._edit_field = FIELD_PASSWORD
            else:
                self._edit_field = FIELD_USERNAME
            self._draw_cred_edit_ui()
            return True

        # Enter saves credentials
        if key == KeyCode.KEYCODE_ENTER:
            self._save_cred_edit()
            return True

        # Backspace deletes character
        if key == KeyCode.KEYCODE_BACKSPACE:
            if self._edit_field == FIELD_USERNAME:
                if self._edit_user:
                    self._edit_user = self._edit_user[:-1]
                    self._draw_cred_edit_ui()
            else:
                if self._edit_pass:
                    self._edit_pass = self._edit_pass[:-1]
                    self._draw_cred_edit_ui()
            return True

        # Printable characters (ASCII 32-126)
        if 32 <= key <= 126:
            if self._edit_field == FIELD_USERNAME:
                if len(self._edit_user) < 20:
                    self._edit_user += chr(key)
                    self._draw_cred_edit_ui()
            else:
                if len(self._edit_pass) < 20:
                    self._edit_pass += chr(key)
                    self._draw_cred_edit_ui()
            return True

        return True

    async def on_run(self):
        """Main run loop - start FTP server and idle."""
        # Mount SD if available
        if self._sd_available:
            self._mount_sd()
            self._draw_ui()

        # Start FTP server if WiFi is available
        if self._wifi_mode != "off" and (self._sta_ip or self._ap_ip) and self._start_ftp():
            # Update display to show server is running
            self._draw_ui()

        # Idle loop
        while True:
            await asyncio.sleep_ms(100)

    def on_hide(self):
        """Stop server when hiding."""
        self._stop_ftp()
        self._unmount_sd()

    def on_exit(self):
        """Clean up on exit."""
        self._stop_ftp()
        self._unmount_sd()


# Export for framework discovery
App = FTPServerApp

# Allow direct execution
if __name__ == "__main__":
    import M5

    M5.begin()
    Lcd.setRotation(1)
    Lcd.setBrightness(80)

    from framework import Framework

    fw = Framework()
    fw.install(FTPServerApp())
    fw.start()

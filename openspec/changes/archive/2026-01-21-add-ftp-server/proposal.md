# Change: Add FTP Server App

## Why

Users need a way to transfer files to/from the Cardputer remotely without physically connecting via USB. An FTP server allows browsing, uploading, downloading, renaming, and deleting files using any standard FTP client (FileZilla, WinSCP, phone file managers, command line).

## What Changes

- Add `lib/uftpd.py` - FTP server library from robert-hh/FTP-Server-for-ESP8266-ESP32-and-PYBD
- Add `apps/ftp_server_app.py` - App that connects to WiFi and starts FTP server
- Register app in `apps/manifest.json`

## Impact

- Affected specs: New `ftp-server` capability
- Affected code:
  - `lib/uftpd.py` (new library)
  - `apps/ftp_server_app.py` (new app)
  - `apps/manifest.json` (register app)

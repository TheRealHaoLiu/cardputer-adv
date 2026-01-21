# Implementation Tasks

## 1. Add FTP Library

- [x] 1.1 Download `uftpd.py` from robert-hh/FTP-Server-for-ESP8266-ESP32-and-PYBD
- [x] 1.2 Add to `lib/uftpd.py`
- [x] 1.3 Modify library to support read-only mode flag
- [x] 1.4 Test library imports correctly on device

## 2. Create FTP Server App

- [x] 2.1 Create `apps/ftp_server_app.py` with AppBase lifecycle
- [x] 2.2 Check WiFi state using WiFiManager (don't modify, just read)
- [x] 2.3 Start FTP server on port 21 with `uftpd.start()` if any interface active
- [x] 2.4 Stop FTP server on app exit with `uftpd.stop()`
- [x] 2.5 Add to `apps/manifest.json`

## 3. SD Card Support

- [x] 3.1 Detect SD card presence on launch
- [x] 3.2 Mount SD card to /sd if present (reuse logic from file_browser.py)
- [x] 3.3 Unmount SD card on app exit
- [x] 3.4 Display SD card status on LCD (available/not available)
- [x] 3.5 Handle SD card mount failures gracefully

## 4. Read-Only Mode

- [x] 4.1 Add read-only flag to modified uftpd.py
- [x] 4.2 Reject write commands (STOR, DELE, MKD, RMD, RNFR, APPE) on /flash and /sd when read-only
- [x] 4.3 Always reject write commands on /system (regardless of RO/RW mode)
- [x] 4.4 Implement R key handler to toggle read-only mode
- [x] 4.5 Display current mode on LCD (RO/RW indicator)
- [x] 4.6 Default to read-write mode on launch

## 5. Optional Authentication

- [x] 5.1 Add authentication flag and credential validation to modified uftpd.py
- [x] 5.2 Implement A key handler to toggle authentication on/off
- [x] 5.3 Store password in NVS (default: username "ftp", password "cardputer")
- [x] 5.4 Display auth status on LCD (Open/Locked indicator)
- [x] 5.5 Default to open (no auth) on launch

## 6. Connection Status Display

- [x] 6.1 Detect current WiFi mode (Off, STA, AP, STA+AP)
- [x] 6.2 Display STA mode: Show SSID and "Connect to: {IP}:21"
- [x] 6.3 Display AP mode: Show "AP: {SSID}" and "Connect to: 192.168.4.1:21"
- [x] 6.4 Display STA+AP mode: Show both connection options
- [x] 6.5 Display WiFi Off: Show error message directing to Settings
- [x] 6.6 Handle STA enabled but not connected state
- [x] 6.7 Show SD card, RO/RW, and auth status in display

## 7. Testing

- [x] 7.1 Test with STA mode connected - verify can FTP via STA IP
- [x] 7.2 Test with AP mode - verify can FTP via 192.168.4.1
- [x] 7.3 Test with STA+AP mode - verify both IPs work
- [x] 7.4 Test with WiFi off - verify error message shown
- [x] 7.5 Test SD card mount/unmount and browsing /sd
- [x] 7.6 Test /system always read-only
- [x] 7.7 Test read-only mode toggle with R key
- [x] 7.8 Test authentication toggle with A key
- [x] 7.9 Test file upload/download on /flash and /sd
- [x] 7.10 Test with FileZilla and mobile FTP app

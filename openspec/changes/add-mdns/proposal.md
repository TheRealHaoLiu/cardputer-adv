# Change: Add mDNS Service Discovery

## Why

Currently, users must know the Cardputer's IP address to connect to services like FTP. IP addresses can change when the device reconnects to WiFi, making it inconvenient to access. mDNS (multicast DNS) allows the device to be discovered via a friendly hostname like `cardputer.local`, which is standard on modern networks.

## What Changes

- Add new `mdns` capability that provides mDNS hostname registration and service advertisement
- Create a reusable mDNS library module that apps can use to advertise their services
- FTP server can optionally advertise `_ftp._tcp` service via mDNS
- Device becomes discoverable as `cardputer.local` (or configurable hostname)

## Impact

- Affected specs: New `mdns` capability, optional enhancement to `ftp-server`
- Affected code:
  - New `lib/mdns_service.py` - mDNS wrapper module
  - `apps/ftp_server.py` - Add optional mDNS advertisement
  - `apps/settings_app.py` - Add hostname configuration (optional)

# Tasks: Add mDNS Service Discovery

## 1. Research & Validation

- [ ] 1.1 Verify MicroPython firmware has mDNS support (check `network.mDNS` or `mdns` module)
- [ ] 1.2 Test basic mDNS hostname registration on hardware
- [ ] 1.3 Test service advertisement (`_ftp._tcp`) on hardware
- [ ] 1.4 Verify discovery works from macOS/Linux/Windows clients

## 2. mDNS Library Implementation

- [ ] 2.1 Create `lib/mdns_service.py` wrapper module
- [ ] 2.2 Implement `start(hostname)` to register hostname
- [ ] 2.3 Implement `add_service(name, service_type, port)` to advertise services
- [ ] 2.4 Implement `remove_service(name)` to stop advertising
- [ ] 2.5 Implement `stop()` to unregister hostname
- [ ] 2.6 Add error handling for missing mDNS support in firmware

## 3. FTP Server Integration

- [ ] 3.1 Import mDNS service module in FTP server app
- [ ] 3.2 Register `cardputer.local` hostname on FTP server start
- [ ] 3.3 Advertise `_ftp._tcp` service on port 21
- [ ] 3.4 Update LCD display to show mDNS hostname
- [ ] 3.5 Stop mDNS service on app exit

## 4. Testing

- [ ] 4.1 Test hostname resolution (`ping cardputer.local`)
- [ ] 4.2 Test FTP connection via hostname (`ftp cardputer.local`)
- [ ] 4.3 Test service discovery (`dns-sd -B _ftp._tcp`)
- [ ] 4.4 Test behavior when WiFi disconnects/reconnects

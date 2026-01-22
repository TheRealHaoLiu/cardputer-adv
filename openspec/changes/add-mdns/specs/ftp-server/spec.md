## ADDED Requirements

### Requirement: mDNS Service Discovery

The FTP server app SHALL advertise itself via mDNS when available, allowing clients to discover and connect using a friendly hostname.

#### Scenario: Register hostname on start

- **WHEN** the FTP server app launches
- **AND** WiFi STA interface is connected
- **AND** mDNS module is available in firmware
- **THEN** the app registers `cardputer.local` hostname via mDNS

#### Scenario: Advertise FTP service

- **WHEN** the FTP server is running
- **AND** mDNS is active
- **THEN** the app advertises `_ftp._tcp` service on port 21
- **AND** clients can discover the service via mDNS-SD

#### Scenario: Display mDNS hostname

- **WHEN** the FTP server is running
- **AND** mDNS is active
- **THEN** the LCD displays "cardputer.local:21" in addition to IP address

#### Scenario: Stop mDNS on exit

- **WHEN** user exits the FTP server app
- **THEN** the mDNS hostname and service advertisement are stopped

#### Scenario: Graceful fallback without mDNS

- **WHEN** the FTP server app launches
- **AND** mDNS module is not available in firmware
- **THEN** the app continues to function normally
- **AND** displays only IP address (no hostname)

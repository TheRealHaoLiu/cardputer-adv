# mdns Specification

## Purpose

Provides mDNS (multicast DNS) hostname registration and service discovery, allowing the Cardputer to be accessed via a friendly `.local` hostname instead of requiring users to know the IP address.

## ADDED Requirements

### Requirement: mDNS Hostname Registration

The system SHALL provide an mDNS service module that registers a hostname on the local network.

#### Scenario: Register default hostname

- **WHEN** an app calls `mdns_service.start()` without arguments
- **AND** WiFi STA interface is connected
- **THEN** the device registers as `cardputer.local`
- **AND** clients on the same network can resolve `cardputer.local` to the device IP

#### Scenario: Register custom hostname

- **WHEN** an app calls `mdns_service.start(hostname="mydevice")`
- **AND** WiFi STA interface is connected
- **THEN** the device registers as `mydevice.local`

#### Scenario: Stop hostname registration

- **WHEN** an app calls `mdns_service.stop()`
- **THEN** the mDNS hostname is unregistered
- **AND** clients can no longer resolve the hostname

#### Scenario: WiFi not connected

- **WHEN** an app calls `mdns_service.start()`
- **AND** WiFi STA interface is not connected
- **THEN** the function returns False
- **AND** no hostname is registered

### Requirement: mDNS Service Advertisement

The system SHALL allow apps to advertise network services via mDNS-SD (service discovery).

#### Scenario: Advertise FTP service

- **WHEN** an app calls `mdns_service.add_service("Cardputer FTP", "_ftp._tcp", 21)`
- **THEN** the service is advertised via mDNS
- **AND** clients can discover it using `dns-sd -B _ftp._tcp`

#### Scenario: Advertise HTTP service

- **WHEN** an app calls `mdns_service.add_service("Cardputer Web", "_http._tcp", 80)`
- **THEN** the service is advertised via mDNS
- **AND** clients can discover it using `dns-sd -B _http._tcp`

#### Scenario: Remove service advertisement

- **WHEN** an app calls `mdns_service.remove_service("Cardputer FTP")`
- **THEN** the service is no longer advertised
- **AND** clients no longer see it in service discovery

### Requirement: Graceful Degradation

The mDNS module SHALL handle missing firmware support gracefully.

#### Scenario: Firmware lacks mDNS support

- **WHEN** the firmware does not include mDNS module
- **AND** an app calls `mdns_service.start()`
- **THEN** the function returns False
- **AND** logs a warning message
- **AND** the app continues to function without mDNS

#### Scenario: Check mDNS availability

- **WHEN** an app calls `mdns_service.is_available()`
- **THEN** returns True if firmware supports mDNS
- **AND** returns False otherwise

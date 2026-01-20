## ADDED Requirements

### Requirement: WiFi Boot Connect
The system SHALL automatically connect to WiFi on boot when WiFi is enabled and credentials are saved.

#### Scenario: Auto-connect on boot with saved credentials
- **WHEN** the device boots
- **AND** WiFi is enabled (wifi_on = 1 in NVS)
- **AND** credentials are saved in NVS
- **THEN** the system SHALL attempt to connect to the saved network

#### Scenario: No connect when WiFi disabled
- **WHEN** the device boots
- **AND** WiFi is disabled (wifi_on = 0 in NVS)
- **THEN** the system SHALL NOT attempt to connect to WiFi

#### Scenario: No connect when no credentials
- **WHEN** the device boots
- **AND** WiFi is enabled
- **AND** no credentials are saved
- **THEN** the system SHALL NOT attempt to connect

## MODIFIED Requirements

### Requirement: WiFi Tab - WiFi Toggle
The WiFi tab SHALL allow users to enable or disable the WiFi radio. The WiFi state SHALL be persisted to NVS and restored on boot.

#### Scenario: User disables WiFi
- **WHEN** user toggles WiFi to OFF
- **THEN** the WiFi radio SHALL be deactivated
- **AND** network list SHALL be cleared
- **AND** connection info SHALL show "Disabled"
- **AND** wifi_on SHALL be set to 0 in NVS

#### Scenario: User enables WiFi
- **WHEN** user toggles WiFi to ON
- **THEN** the WiFi radio SHALL be activated
- **AND** wifi_on SHALL be set to 1 in NVS

#### Scenario: WiFi state persists
- **WHEN** user toggles WiFi state
- **AND** device is rebooted
- **THEN** the WiFi state SHALL match the saved setting

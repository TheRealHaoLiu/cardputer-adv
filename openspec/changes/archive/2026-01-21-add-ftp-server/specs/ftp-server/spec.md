## ADDED Requirements

### Requirement: FTP Server App

The system SHALL provide an FTP server application that allows users to transfer files to/from the device remotely using any standard FTP client.

#### Scenario: App launches and starts FTP server

- **WHEN** user launches the FTP Server app
- **AND** at least one WiFi interface (STA or AP) is active
- **THEN** the app starts an FTP server on port 21 bound to all interfaces
- **AND** displays connection information on the LCD

#### Scenario: App exits cleanly

- **WHEN** user presses ESC to exit the app
- **THEN** the FTP server stops accepting connections
- **AND** any active transfers are terminated

### Requirement: Connection Status Display

The FTP server app SHALL display clear connection information based on the current WiFi mode.

#### Scenario: Display in STA mode

- **WHEN** the FTP server is running
- **AND** WiFi mode is STA (station only)
- **AND** device is connected to a network
- **THEN** the LCD displays the network name (SSID)
- **AND** displays "Connect to: {STA_IP}:21"

#### Scenario: Display in AP mode

- **WHEN** the FTP server is running
- **AND** WiFi mode is AP (access point only)
- **THEN** the LCD displays "AP: {AP_SSID}"
- **AND** displays "Connect to: 192.168.4.1:21"

#### Scenario: Display in STA+AP mode

- **WHEN** the FTP server is running
- **AND** WiFi mode is STA+AP (both active)
- **THEN** the LCD displays both connection options
- **AND** shows "WiFi: {STA_IP}:21" if STA is connected
- **AND** shows "AP: 192.168.4.1:21"

#### Scenario: Display when STA not connected

- **WHEN** the FTP server is running
- **AND** WiFi mode is STA or STA+AP
- **AND** STA is not connected to any network
- **THEN** the LCD indicates STA is not connected
- **AND** shows AP connection info if AP is active

#### Scenario: WiFi disabled

- **WHEN** user launches the FTP Server app
- **AND** WiFi mode is Off (no interfaces active)
- **THEN** the LCD displays "WiFi disabled"
- **AND** instructs user to enable WiFi in Settings

### Requirement: File Transfer Operations

The FTP server SHALL support standard file transfer operations.

#### Scenario: Download file from device

- **WHEN** user requests a file via FTP RETR command
- **THEN** the server sends the file contents to the client

#### Scenario: Upload file to device

- **WHEN** user sends a file via FTP STOR command
- **THEN** the server saves the file to the specified path

#### Scenario: List directory contents

- **WHEN** user requests directory listing via FTP LIST command
- **THEN** the server returns the files and directories at the current path

#### Scenario: Navigate directories

- **WHEN** user changes directory via FTP CWD command
- **THEN** the server changes the current working directory

### Requirement: File Management Operations

The FTP server SHALL support file management operations.

#### Scenario: Delete file

- **WHEN** user deletes a file via FTP DELE command
- **THEN** the server removes the specified file

#### Scenario: Rename file

- **WHEN** user renames a file via FTP RNFR/RNTO commands
- **THEN** the server renames the file to the new name

#### Scenario: Create directory

- **WHEN** user creates a directory via FTP MKD command
- **THEN** the server creates the new directory

#### Scenario: Remove directory

- **WHEN** user removes a directory via FTP RMD command
- **THEN** the server removes the specified directory

### Requirement: WiFi Integration

The FTP server app SHALL use the current WiFi configuration without modifying it.

#### Scenario: Use existing WiFi state

- **WHEN** the app launches
- **THEN** it uses whatever WiFi interfaces are already active (STA, AP, or both)
- **AND** does not attempt to change WiFi mode or connect to networks

#### Scenario: STA connected on launch

- **WHEN** the app launches
- **AND** STA interface is active and connected
- **THEN** the FTP server is accessible via the STA IP address

#### Scenario: AP active on launch

- **WHEN** the app launches
- **AND** AP interface is active
- **THEN** the FTP server is accessible via the AP IP address (192.168.4.1)

#### Scenario: No network available

- **WHEN** the app launches
- **AND** no WiFi interfaces are active
- **THEN** the app displays an error directing user to enable WiFi in Settings
- **AND** the FTP server is not started

### Requirement: SD Card Support

The FTP server app SHALL mount and expose the SD card filesystem when available.

#### Scenario: SD card mounted on launch

- **WHEN** the app launches
- **AND** an SD card is inserted
- **THEN** the app mounts the SD card to /sd
- **AND** the /sd directory is accessible via FTP

#### Scenario: SD card not inserted

- **WHEN** the app launches
- **AND** no SD card is inserted
- **THEN** the app continues without SD card access
- **AND** only /flash is accessible via FTP

#### Scenario: SD card unmounted on exit

- **WHEN** user exits the app
- **AND** SD card was mounted
- **THEN** the app unmounts the SD card cleanly

#### Scenario: Display SD card status

- **WHEN** the FTP server is running
- **THEN** the LCD indicates whether SD card is available
- **AND** shows storage paths accessible via FTP

### Requirement: Read-Only Mode

The FTP server app SHALL support a read-only mode that prevents file modifications on /flash and /sd.

#### Scenario: Toggle read-only mode

- **WHEN** user presses R key while FTP server is running
- **THEN** read-only mode is toggled on or off for /flash and /sd
- **AND** the LCD updates to show current mode (RO or RW)

#### Scenario: Default mode on launch

- **WHEN** the app launches
- **THEN** read-only mode is OFF (read-write access to /flash and /sd)

#### Scenario: Write commands rejected in read-only mode

- **WHEN** read-only mode is ON
- **AND** client attempts STOR, DELE, MKD, RMD, RNFR, or APPE command on /flash or /sd
- **THEN** the server rejects the command with an error response
- **AND** the filesystem is not modified

#### Scenario: Read commands allowed in read-only mode

- **WHEN** read-only mode is ON
- **AND** client attempts RETR, LIST, NLST, or CWD command
- **THEN** the server processes the command normally

#### Scenario: System directory always read-only

- **WHEN** client attempts any write command on /system
- **THEN** the server rejects the command regardless of RO/RW mode
- **AND** the /system filesystem is never modified

### Requirement: Optional Authentication

The FTP server app SHALL support optional password authentication that can be toggled on or off.

#### Scenario: Toggle authentication

- **WHEN** user presses A key while FTP server is running
- **THEN** authentication mode is toggled on or off
- **AND** the LCD updates to show current auth status

#### Scenario: Default authentication state

- **WHEN** the app launches
- **THEN** authentication is OFF (open access)

#### Scenario: Authentication enabled

- **WHEN** authentication is ON
- **AND** client connects and provides USER/PASS commands
- **THEN** the server validates credentials against stored password
- **AND** rejects connection if credentials are invalid

#### Scenario: Authentication disabled

- **WHEN** authentication is OFF
- **AND** client connects
- **THEN** the server accepts any username/password or none

#### Scenario: Display authentication status

- **WHEN** the FTP server is running
- **THEN** the LCD shows auth status (Open or Locked)
- **AND** shows password hint when auth is enabled

#### Scenario: Default credentials

- **WHEN** authentication is enabled
- **AND** no custom password is configured
- **THEN** the default username is "ftp"
- **AND** the default password is "cardputer"

#### Scenario: Password storage

- **WHEN** a password is configured
- **THEN** it is stored in NVS namespace for persistence across reboots

# Change: Add WiFi auto-connect on boot

## Why
When WiFi is enabled in settings and credentials are saved, users expect the device to automatically connect to WiFi on boot. Currently, WiFi must be manually connected each time the device restarts.

## What Changes
- boot.py checks if WiFi is enabled (saved state in NVS)
- If enabled and credentials exist, boot.py connects to saved network
- WiFi tab saves on/off state to NVS when toggled
- NVS key `wifi_on` in `settings` namespace stores WiFi enabled state (0=off, 1=on)

## Impact
- Affected specs: settings-app (WiFi tab)
- Affected code: boot.py, apps/settings/wifi_tab.py

# Tasks: Add USB Mass Storage Support

## Phase 1: Firmware Preparation

- [ ] Add esp-usb component to firmware dependencies
- [ ] Enable `CONFIG_TINYUSB_MSC_ENABLED=y` in sdkconfig.board
- [ ] Verify CDC (serial/REPL) still works after enabling MSC
- [ ] Test build compiles without errors

## Phase 2: Core Implementation

- [ ] Create `modusb_msc.c` - MicroPython C module for USB MSC
- [ ] Implement `usb_msc.mount_sdcard()` function
  - Unmount SD from Python VFS
  - Initialize SDMMC via ESP-IDF
  - Call esp-usb `storage_sdmmc_open_medium()`
  - Mount to USB via `tinyusb_msc_storage_mount()`
- [ ] Implement `usb_msc.unmount()` function
  - Unmount from USB
  - Remount SD to Python VFS
- [ ] Implement `usb_msc.is_mounted()` status check
- [ ] Add module to firmware build (CMakeLists.txt)

## Phase 3: USB Stack Integration

- [ ] Investigate USB descriptor requirements for CDC+MSC composite
- [ ] Decide: composite device vs mode-switching
- [ ] If mode-switching: implement USB stack reset between modes
- [ ] If composite: update USB descriptors for both interfaces

## Phase 4: Python App

- [ ] Create `apps/usb_storage_app.py`
- [ ] Display status on LCD (Mounted/Unmounted)
- [ ] Handle key press to toggle mount state
- [ ] Show instructions ("Press any key to unmount")
- [ ] Add to app manifest

## Phase 5: Testing

- [ ] Test mount/unmount cycle
- [ ] Test file copy from computer to SD
- [ ] Test file copy from SD to computer
- [ ] Measure actual transfer speeds
- [ ] Test eject handling (proper vs surprise removal)
- [ ] Test REPL availability in different modes
- [ ] Test on macOS, Windows, Linux

## Phase 6: Documentation

- [ ] Update CLAUDE.md with new workflow
- [ ] Document USB storage app usage
- [ ] Add troubleshooting notes (eject before unmount, etc.)

## Stretch Goals

- [ ] Expose internal flash as second LUN
- [ ] Auto-mount on boot option
- [ ] LED/display indicator during transfers

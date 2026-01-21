# Change: Add USB Mass Storage Support

## Why

Current firmware upload workflow is painfully slow:
- Serial transfer via mpremote: ~11.5 KB/s (6MB file = ~9 minutes)
- Only alternative is physically removing SD card

USB Mass Storage (MSC) would allow the Cardputer to appear as a USB drive, enabling:
- Fast file transfers at USB 2.0 Full Speed (~1.5 MB/s, ~130x faster)
- Drag-and-drop firmware updates
- Direct access to SD card contents from computer
- No need to physically remove the SD card

## Research Findings

### MicroPython Status
- `machine.USBDevice` exists on ESP32-S3 but is low-level
- No built-in MSC support (`BUILTIN_CDC_MSC` not available)
- MicroPython GitHub issue [#8426](https://github.com/micropython/micropython/issues/8426) open since 2022
- Other ports (RP2, STM32) have `msc_disk.c` but ESP32 does not

### CircuitPython Approach
- Uses shared `usb_msc_flash.c` across all ports
- Goes through VFS/blockdev abstraction
- Supports multiple LUNs (internal flash + SD card)

### ESP-IDF/esp-usb Solution (Recommended)
The [esp-usb](https://github.com/espressif/esp-usb) component provides a complete, production-ready MSC stack:

**Files:**
- `tinyusb_msc.c` - TinyUSB callback implementations with thread-safe locking
- `storage_sdmmc.c` - SD card storage backend
- `storage_spiflash.c` - SPI flash storage backend (optional)

**Key Features:**
- Thread-safe with mutex/semaphore protection
- Deferred writes handled in USB task context
- Supports up to 2 LUNs
- Already tested with ESP32-S3

## Implementation Path

### Option A: Use esp-usb Component (Recommended)

1. **Add esp-usb component to firmware build**
   ```yaml
   # idf_component.yml
   dependencies:
     espressif/esp_tinyusb: "^1.0.0"
   ```

2. **Enable MSC in sdkconfig.board**
   ```
   CONFIG_TINYUSB_MSC_ENABLED=y
   CONFIG_TINYUSB_CDC_ENABLED=y  # Keep serial/REPL
   ```

3. **Create MicroPython module** (`modusb_msc.c`)
   - Wrap esp-usb functions for Python access
   - Handle SD card init/mount coordination

4. **Python API**
   ```python
   import usb_msc

   # Mount SD card as USB drive (disables Python access to SD)
   usb_msc.mount_sdcard()

   # Check status
   usb_msc.is_mounted()  # True/False

   # Unmount and return SD to Python
   usb_msc.unmount()
   ```

### Option B: Native MicroPython Implementation

1. **Create `ports/esp32/msc_disk.c`** (~200 lines)
   - Implement TinyUSB callbacks
   - Use ESP-IDF SDMMC driver directly

2. **Enable in board config**
   ```c
   #define MICROPY_HW_USB_MSC (1)
   ```

3. **Wire into build** (CMakeLists.txt)

Option A is recommended because:
- Less code to write and maintain
- Already tested and production-ready
- Thread-safety handled correctly
- Matches ESP-IDF examples

## Technical Considerations

### USB Conflict Resolution
MicroPython initializes USB for CDC (serial/REPL). Options:
1. **Composite device** - CDC + MSC simultaneously (requires descriptor changes)
2. **Mode switching** - Disable CDC when MSC active, reset USB stack
3. **Use esp-usb exclusively** - Replace MicroPython's USB init entirely

Composite device (option 1) is cleanest but most complex. Mode switching (option 2) is simplest to implement.

### SD Card Locking
When MSC is active:
- Python cannot access `/sd` (would corrupt filesystem)
- Must unmount from Python before USB takes over
- On unmount, host should "eject" before Python remounts

### Speed Expectations
- USB 2.0 Full Speed: 12 Mbps theoretical = ~1.5 MB/s
- Realistic with overhead: ~800 KB/s to 1 MB/s
- 6MB firmware upload: ~6-8 seconds vs ~9 minutes via serial

## Impact

- **Affected firmware:** Custom MicroPython build
- **New files:**
  - `modusb_msc.c` - Python bindings
  - Board config changes
- **Dependencies:** esp-usb component

## UX Flow

1. User launches "USB Storage" app from menu (or runs `usb_msc.mount_sdcard()`)
2. Device unmounts SD from Python, initializes MSC
3. Computer sees new USB drive with SD card contents
4. User copies files, then "ejects" drive on computer
5. User presses key or calls `usb_msc.unmount()`
6. Device returns to normal, SD accessible from Python again

## Risks

- **USB stack conflicts** - May need significant refactoring of USB init
- **Filesystem corruption** - If user unplugs without ejecting
- **REPL unavailable** - During MSC mode if using mode-switching approach

## References

- [esp-usb repository](https://github.com/espressif/esp-usb)
- [ESP-IDF tusb_msc example](https://github.com/espressif/esp-idf/tree/master/examples/peripherals/usb/device/tusb_msc)
- [ESP-IDF composite MSC+CDC example](https://github.com/espressif/esp-idf/tree/master/examples/peripherals/usb/device/tusb_composite_msc_serialdevice)
- [MicroPython USB MSC issue #8426](https://github.com/micropython/micropython/issues/8426)
- [CircuitPython USB MSC implementation](https://github.com/adafruit/circuitpython/blob/main/supervisor/shared/usb/usb_msc_flash.c)
- [TinyUSB MSC device docs](https://docs.tinyusb.org/en/latest/reference/class/msc.html)

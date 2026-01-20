#!/bin/bash
# Deploy to Cardputer ADV flash storage
#
# WARNING: This replaces ALL of the following on the device:
#   - /flash/main.py
#   - /flash/lib/* (framework, app_base, etc.)
#   - /flash/apps/* (all app files)
#
# Any changes made directly on the device will be lost!

set -e

# Find the device
DEVICE=$(ls /dev/tty.usbmodem* 2>/dev/null | head -1)
if [ -z "$DEVICE" ]; then
    echo "Error: No device found at /dev/tty.usbmodem*"
    exit 1
fi

echo "Deploying to $DEVICE"
echo ""
echo "WARNING: This will replace /flash/main.py, /flash/lib/*, and /flash/apps/*"
echo ""

# Python code for cleanup (single line to avoid quoting issues)
CLEANUP_CODE='import os
def rmtree(p):
 try:
  for f in os.listdir(p):
   fp=p+"/"+f
   try:os.remove(fp)
   except:rmtree(fp)
  os.rmdir(p)
 except:pass
rmtree("/flash/lib");os.mkdir("/flash/lib");print("Cleared /flash/lib")
rmtree("/flash/apps");os.mkdir("/flash/apps");print("Cleared /flash/apps")'

DONE_CODE='import os;print("Done!");print("Lib:",os.listdir("/flash/lib"));print("Apps:",os.listdir("/flash/apps"))'

# Use a single mpremote session with chained commands
uv run mpremote connect "$DEVICE" \
    exec "$CLEANUP_CODE" \
    + fs cp -r lib/ :/flash/lib/ \
    + fs cp -r apps/ :/flash/apps/ \
    + fs cp main.py :/flash/main.py \
    + exec "$DONE_CODE"

echo ""
echo "Reset device to run standalone, or use 'uv run poe run' for development."

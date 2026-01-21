# sdcard.py - SD card mount/unmount utilities
import os

from machine import Pin, SDCard

# Cardputer ADV SD card pins
SD_SCK = 40
SD_MISO = 39
SD_MOSI = 14
SD_CS = 12
SD_FREQ = 1000000

_sd = None


def mount():
    """Mount SD card at /sd"""
    global _sd
    _sd = SDCard(
        slot=3,
        sck=Pin(SD_SCK),
        miso=Pin(SD_MISO),
        mosi=Pin(SD_MOSI),
        cs=Pin(SD_CS),
        freq=SD_FREQ,
    )
    os.mount(_sd, "/sd")
    print("SD mounted at /sd")


def unmount():
    """Unmount SD card"""
    global _sd
    os.umount("/sd")
    _sd = None
    print("SD unmounted")

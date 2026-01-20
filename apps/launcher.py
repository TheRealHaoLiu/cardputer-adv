"""
Launcher App - Home Screen Menu
================================

The launcher is the home screen that displays all installed apps.
Users navigate with keyboard and press Enter to launch an app.
Pressing ESC from any app returns here.

HOW IT WORKS:
-------------
1. Framework calls on_view() - we scan manifests and draw the menu
2. Framework routes keyboard events to _kb_event_handler()
3. User navigates with ;/. keys and selects with Enter
4. For apps: we call fw.get_or_load_app() then fw.launch_app()
5. For submenus: we descend into the submenu
6. ESC in submenu: return to parent menu
7. ESC at root: no-op (launcher is home screen)

CONTROLS:
---------
- ; (semicolon) or UP arrow = Move selection up
- . (period) or DOWN arrow = Move selection down
- Enter = Launch selected app or enter submenu
- ESC = Go back one level (in submenus) or no-op (at root)
- r = Reload apps (dev mode only)

The launcher excludes itself from the app list (you can't launch the launcher).
Apps are loaded lazily - only when selected, not on every ESC.
"""

import os
import sys

# =============================================================================
# IMPORTS
# =============================================================================
from M5 import Lcd, Widgets

# Path setup for standalone mode
for lib_path in ["/flash/lib", "/remote/lib"]:
    if lib_path not in sys.path:
        sys.path.insert(0, lib_path)

from app_base import AppBase

# Import KeyCode for arrow key constants
# Falls back to a local definition if not available in firmware
try:
    from unit import KeyCode
except ImportError:

    class KeyCode:
        KEYCODE_ESC = 0x1B
        KEYCODE_ENTER = 0x0D
        KEYCODE_UP = 0x26
        KEYCODE_DOWN = 0x28


# =============================================================================
# RUN MODE DETECTION
# =============================================================================
# Detect if we're running from mounted files (development) or flash (deployed).
# This is shown in the UI to help during development.

try:
    os.stat("/remote/main.py")
    RUN_MODE = "remote"  # Files mounted from computer
except OSError:
    RUN_MODE = "flash"  # Files deployed to device


# =============================================================================
# LAYOUT CONSTANTS
# =============================================================================
# These control the visual layout of the menu.
# Adjust these if you want more/fewer items visible.

MENU_START_Y = 22  # Y position where menu items start (below title)
MENU_ITEM_H = 22  # Height of each menu item in pixels
VISIBLE_ITEMS = 4  # How many items fit on screen at once


# =============================================================================
# LAUNCHER APP CLASS
# =============================================================================


class LauncherApp(AppBase):
    """
    The launcher app - displays a hierarchical menu of all apps.

    This is both the "home screen" and an app itself.
    The framework treats it specially - ESC always returns here.
    """

    def __init__(self):
        super().__init__()
        self.name = "Launcher"

        # Menu state
        # _selected: Index of currently highlighted item
        # _scroll_offset: Index of first visible item (for scrolling)
        self._selected = 0
        self._scroll_offset = 0

        # Hierarchical menu state
        # _menu_stack: Stack of (registry, selected, scroll) for parent menus
        # _current_registry: The registry dict for current menu level
        self._menu_stack = []
        self._current_registry = None

    def on_view(self):
        """
        Set up display and draw the menu.

        Called when:
        - Launcher first starts (on boot)
        - Returning from another app (after ESC)
        """
        # Scan apps (uses manifest.json, no imports)
        if self._fw:
            self._fw.scan_apps()
            # Start at root level
            self._current_registry = self._fw.get_app_registry()
            # Reset to root if returning from an app
            self._menu_stack = []

        Lcd.fillScreen(Lcd.COLOR.BLACK)
        Lcd.setFont(Widgets.FONTS.ASCII7)
        Lcd.setTextSize(2)
        Lcd.setTextColor(Lcd.COLOR.WHITE, Lcd.COLOR.BLACK)
        self._draw_menu()

    def _get_menu_entries(self):
        """
        Get list of entries for current menu level.

        Returns a list of tuples: (type, key, display_name, data)
        - type: "app" or "submenu"
        - key: module name or submenu directory name
        - display_name: what to show in menu
        - data: the full entry dict
        """
        if not self._current_registry:
            return []

        entries = []

        # Add submenus first (folders at top)
        for key, submenu in self._current_registry.get("submenus", {}).items():
            entries.append(("submenu", key, submenu["name"], submenu))

        # Add apps
        for app in self._current_registry.get("apps", []):
            entries.append(("app", app["path"], app["name"], app))

        return entries

    def _draw_menu(self):
        """
        Draw the menu on screen.

        This handles:
        - Title bar with run mode indicator and breadcrumb
        - Scrollable list of apps/submenus with ">" cursor
        - Folder indicator for submenus
        - Scroll indicators (^ and v) when there are more items
        - Key hints at the bottom
        """
        entries = self._get_menu_entries()

        # Handle empty menu
        if not entries:
            Lcd.fillScreen(Lcd.COLOR.BLACK)
            Lcd.setCursor(10, 50)
            Lcd.print("No apps found")
            Lcd.setTextSize(1)
            Lcd.setCursor(10, 80)
            Lcd.print("Add manifest.json")
            return

        # Keep selection within bounds
        if self._selected >= len(entries):
            self._selected = len(entries) - 1
        if self._selected < 0:
            self._selected = 0

        # Adjust scroll to keep selection visible
        if self._selected < self._scroll_offset:
            self._scroll_offset = self._selected
        elif self._selected >= self._scroll_offset + VISIBLE_ITEMS:
            self._scroll_offset = self._selected - VISIBLE_ITEMS + 1

        # Clear screen and draw title
        Lcd.fillScreen(Lcd.COLOR.BLACK)
        Lcd.setFont(Widgets.FONTS.ASCII7)
        Lcd.setTextSize(2)
        Lcd.setTextColor(Lcd.COLOR.WHITE, Lcd.COLOR.BLACK)
        Lcd.setCursor(0, 0)

        # Show breadcrumb if in submenu, otherwise "Cardputer"
        if self._menu_stack:
            # Show current submenu name with back indicator
            current_name = self._current_registry.get("name", "Menu")
            Lcd.print(f"< {current_name}")
        else:
            Lcd.print("Cardputer")

        # Show run mode indicator
        Lcd.setTextSize(1)
        if RUN_MODE == "remote":
            Lcd.setTextColor(Lcd.COLOR.CYAN, Lcd.COLOR.BLACK)
        else:
            Lcd.setTextColor(Lcd.COLOR.GREEN, Lcd.COLOR.BLACK)
        Lcd.setCursor(200, 5)
        Lcd.print(RUN_MODE)

        # Draw visible menu items
        Lcd.setTextSize(2)
        Lcd.setTextColor(Lcd.COLOR.WHITE, Lcd.COLOR.BLACK)

        for i in range(VISIBLE_ITEMS):
            idx = self._scroll_offset + i
            if idx >= len(entries):
                break

            entry_type, key, display_name, data = entries[idx]
            y = MENU_START_Y + i * MENU_ITEM_H
            Lcd.setCursor(10, y)

            # ">" cursor indicates selected item
            prefix = "> " if idx == self._selected else "  "

            # Add folder indicator for submenus
            if entry_type == "submenu":
                Lcd.print(f"{prefix}{display_name}/")
            else:
                Lcd.print(f"{prefix}{display_name}")

        # Draw scroll indicators if there are items above/below
        Lcd.setTextSize(1)
        if self._scroll_offset > 0:
            Lcd.setCursor(225, MENU_START_Y)
            Lcd.print("^")  # More items above
        if self._scroll_offset + VISIBLE_ITEMS < len(entries):
            Lcd.setCursor(225, MENU_START_Y + (VISIBLE_ITEMS - 1) * MENU_ITEM_H + 10)
            Lcd.print("v")  # More items below

        # Draw key hints at bottom
        Lcd.setCursor(0, 125)
        if RUN_MODE == "remote":
            Lcd.print("Ent=Sel ;/.=Nav r=Rld")
        else:
            Lcd.print("Enter=Select  ;/.=Nav")

    async def _kb_event_handler(self, event, fw):
        """
        Handle keyboard input for menu navigation.

        Parameters:
        -----------
        event : KeyEvent
            - event.key: The key code (ASCII or KeyCode constant)
            - event.status: Set to True if you handled the event
        fw : Framework
            The framework instance (for launching apps, etc.)
        """
        key = event.key
        entries = self._get_menu_entries()

        # Handle reload key in dev mode
        if key == ord("r") and RUN_MODE == "remote":
            event.status = True
            await self._do_reload(fw)
            return

        # Handle ESC for submenu navigation
        if key == KeyCode.KEYCODE_ESC:
            if self._menu_stack:
                # In submenu - go back to parent
                event.status = True
                parent_registry, parent_selected, parent_scroll = self._menu_stack.pop()
                self._current_registry = parent_registry
                self._selected = parent_selected
                self._scroll_offset = parent_scroll
                self._draw_menu()
                return
            # At root - let framework handle (no-op for launcher)
            return

        if not entries:
            return

        # Enter - launch app or enter submenu
        if key == KeyCode.KEYCODE_ENTER:
            event.status = True
            entry_type, key_name, display_name, data = entries[self._selected]

            if entry_type == "submenu":
                # Enter submenu
                self._menu_stack.append(
                    (self._current_registry, self._selected, self._scroll_offset)
                )
                self._current_registry = data
                self._selected = 0
                self._scroll_offset = 0
                self._draw_menu()
            else:
                # Launch app
                await self._launch_app(fw, data["path"], display_name)
            return

        # Up navigation: ; (semicolon) or UP arrow
        if key == 59 or key == KeyCode.KEYCODE_UP:
            event.status = True
            self._selected = (self._selected - 1) % len(entries)
            self._draw_menu()
            return

        # Down navigation: . (period) or DOWN arrow
        if key == 46 or key == KeyCode.KEYCODE_DOWN:
            event.status = True
            self._selected = (self._selected + 1) % len(entries)
            self._draw_menu()
            return

    async def _launch_app(self, fw, module_path, display_name):
        """
        Load and launch an app.

        Shows loading indicator, loads the app, then launches it.
        Shows error if loading fails.
        """
        # Show loading indicator
        Lcd.fillScreen(Lcd.COLOR.BLACK)
        Lcd.setFont(Widgets.FONTS.ASCII7)
        Lcd.setTextSize(2)
        Lcd.setTextColor(Lcd.COLOR.WHITE, Lcd.COLOR.BLACK)
        Lcd.setCursor(10, 50)
        Lcd.print("Loading...")
        Lcd.setTextSize(1)
        Lcd.setCursor(10, 80)
        Lcd.print(display_name)

        # Load the app
        app = fw.get_or_load_app(module_path)

        if app:
            await fw.launch_app(app)
        else:
            # Show error
            Lcd.fillScreen(Lcd.COLOR.BLACK)
            Lcd.setTextSize(2)
            Lcd.setTextColor(Lcd.COLOR.RED, Lcd.COLOR.BLACK)
            Lcd.setCursor(10, 50)
            Lcd.print("Load failed!")
            Lcd.setTextSize(1)
            Lcd.setTextColor(Lcd.COLOR.WHITE, Lcd.COLOR.BLACK)
            Lcd.setCursor(10, 80)
            Lcd.print(module_path)
            Lcd.setCursor(10, 100)
            Lcd.print("Press any key...")

            # Wait for keypress or timeout (5 seconds)
            import asyncio

            import M5

            timeout_ms = 5000
            waited_ms = 0
            while waited_ms < timeout_ms:
                M5.update()
                if fw._kb:
                    fw._kb.tick()
                    if fw._kb.is_pressed():
                        fw._kb.get_key()  # Clear key buffer
                        break
                await asyncio.sleep_ms(50)
                waited_ms += 50

            self._draw_menu()

    async def _do_reload(self, fw):
        """
        Reload all apps (dev mode hot-reload).
        """
        # Show reloading indicator
        Lcd.fillScreen(Lcd.COLOR.BLACK)
        Lcd.setFont(Widgets.FONTS.ASCII7)
        Lcd.setTextSize(2)
        Lcd.setTextColor(Lcd.COLOR.CYAN, Lcd.COLOR.BLACK)
        Lcd.setCursor(10, 50)
        Lcd.print("Reloading...")

        # Clear caches and rescan
        fw.clear_app_cache()
        fw.scan_apps(force=True)

        # Reset to root menu
        self._current_registry = fw.get_app_registry()
        self._menu_stack = []
        self._selected = 0
        self._scroll_offset = 0

        # Brief pause so user sees the message
        import asyncio

        await asyncio.sleep_ms(300)

        # Redraw menu
        self._draw_menu()

    async def on_run(self):
        """
        Background task - the launcher just idles.

        The launcher doesn't need to do anything in the background.
        All interaction happens through _kb_event_handler().
        """
        import asyncio

        while True:
            await asyncio.sleep_ms(100)

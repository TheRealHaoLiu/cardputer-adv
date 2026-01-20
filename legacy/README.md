# Legacy Code

This directory contains the original implementation before the app framework refactor.

## Why the Switch?

### Problems with the Legacy Approach

1. **Monolithic main.py** - Everything lived in one 500+ line file: hardware init, app registry, menu drawing, keyboard handling, app loading. Hard to navigate and maintain.

2. **Manual App Registry** - Apps had to be explicitly registered in `APP_REGISTRY` with their module path, class name, and description. Adding a new app meant editing main.py.

3. **No Lifecycle Management** - Apps were just classes that got instantiated. No formal lifecycle (init, view, run, pause, resume). Each app reimplemented everything.

4. **Tight Coupling** - The launcher knew too much about app internals. Apps had to follow implicit conventions with no base class to guide them.

5. **No Framework Abstraction** - Keyboard polling, event routing, and screen management were scattered throughout the code rather than centralized.

### What the New Framework Provides

1. **Separation of Concerns**
   - `boot.py` - Hardware init and WiFi
   - `lib/framework.py` - Event loop, keyboard routing, app management
   - `apps/` - Each app in its own file, inheriting from `AppBase`

2. **Auto-Discovery** - Drop a new `.py` file in `apps/` and it appears in the launcher. No registry to maintain.

3. **App Lifecycle** - Clear lifecycle methods: `on_install()`, `on_view()`, `on_run()`, `on_key()`, `on_exit()`. Apps know what to implement.

4. **Base Class** - `AppBase` provides common functionality and documents the interface apps should follow.

5. **Centralized Event Loop** - The Framework handles keyboard polling and routes events to the active app. Apps just implement `on_key()`.

## Files

- `main.py` - The original monolithic entry point
- `apps/` - The original app implementations (before AppBase refactor)

## Running Legacy Code

The legacy code is preserved for reference but is not actively maintained. If you need to run it:

```bash
# From project root
poe run legacy/main.py
```

Note: Some legacy apps may not work without modification since the codebase has evolved.

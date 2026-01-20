# Explore UIFlow2 Widget Module

## Summary

Research and document the UIFlow2 widget module from uiflow-micropython source code to understand available widgets beyond the `Label` class already in use.

## Motivation

The project currently uses:
- `Widgets.FONTS` - Font constants (ASCII7, DejaVu12, DejaVu18)
- `widgets.Label` - Text labels with alignment, wrapping, and auto-clear

However, the widget module contains additional classes (`Image`, `Base`, `Button`) that haven't been explored. Understanding these could:
- Simplify image display in apps
- Provide patterns for creating custom widgets
- Enable touch-based UI for future touchscreen support

## Scope

**In Scope:**
- Document `Base`, `Image`, `Button`, `Label` classes from uiflow-micropython
- Create a reference guide in `openspec/specs/widgets/`
- Test Image widget functionality on Cardputer ADV

**Out of Scope:**
- Creating new custom widgets (future work)
- Touch event handling (Cardputer has keyboard, not touchscreen)
- Modifying the UIFlow2 widget source

## Source Location

```
~/projects/src/github.com/m5stack/uiflow-micropython/m5stack/modules/widgets/
├── __init__.py   # Lazy loading exports
├── base.py       # Base widget class
├── button.py     # Button widget (stub)
├── image.py      # Image display widget
└── label.py      # Text label widget
```

## Key Findings (Pre-research)

### Base Class (`base.py`)
- Position/size management (`x`, `y`, `w`, `h`)
- Parent reference for drawing target (Lcd or canvas)
- Event handler support with hit detection (`_is_select`)
- Abstract `_draw()` method

### Image Class (`image.py`)
- Sprite-based rendering for efficiency
- Image source loading with scaling
- Auto-cleanup via `__del__`
- Direct-to-parent fallback mode

### Button Class (`button.py`)
- Empty stub extending Base
- No implementation (placeholder)

### Label Class (`label.py`)
- Already documented in `legacy_apps/demo_widgets.py`
- Alignment: LEFT, CENTER, RIGHT
- Long text modes: WRAP, DOT truncation

## Deliverables

1. **Widget Reference Spec** - `openspec/specs/widgets/spec.md`
2. **Image Widget Demo** - Test image loading on device (optional)

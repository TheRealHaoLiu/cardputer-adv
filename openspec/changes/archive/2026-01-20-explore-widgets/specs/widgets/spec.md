# Widgets Module Reference

UIFlow2 provides a `widgets` module with reusable UI components for MicroPython applications.

## ADDED Requirements

### Requirement: Widget Base Class Documentation

The project documentation SHALL describe the Base class as the foundation for all widgets.

**API:**
```python
from widgets import Base

class Base:
    def __init__(self, parent) -> None
    def set_pos(self, x, y)      # Set position
    def set_size(self, w, h)     # Set dimensions
    def set_x(self, x) / set_y(self, y)
    def get_x() / get_y()        # Note: get_y is misspelled as get_() in source
    def set_width(self, w) / set_height(self, h)
    def add_event(self, handler) # Add touch event handler
    def handle(self, x, y)       # Process touch at coordinates
    def _draw()                  # Override in subclass
```

**Properties:**
- `_x`, `_y` - Position coordinates
- `_w`, `_h` - Dimensions
- `_parent` - Drawing target (Lcd or canvas)
- `_buf` - Optional buffer
- `_event_handler` - Touch callback

#### Scenario: Custom widget extends Base
Given a custom widget class extending Base
When the widget overrides `_draw()`
Then it can render custom content to `_parent`

---

### Requirement: Image Widget Documentation

The project documentation SHALL describe the Image widget for displaying images with optional sprite buffering.

**API:**
```python
from widgets import Image
import M5

img = Image(use_sprite=True, parent=M5.Lcd)
img.set_size(100, 100)      # Required before set_src
img.set_src("path/to/image.png")
img.set_pos(10, 10)
img.set_scale(1.0, 1.0)     # X and Y scale factors
img.refresh()               # Force redraw
img.clear(color)            # Clear with color
```

**Sprite Mode (default):**
- Creates offscreen canvas for efficient updates
- Image decoded once, pushed on position changes
- Auto-cleanup via `__del__`

**Direct Mode (`use_sprite=False`):**
- Draws directly to parent
- Re-decodes image on every draw
- Lower memory usage

#### Scenario: Display image with sprite buffering
Given an Image widget with `use_sprite=True`
When `set_size()` is called before `set_src()`
Then image is decoded into sprite buffer
And position updates only push the buffer (fast)

#### Scenario: Display image without buffering
Given an Image widget with `use_sprite=False`
When `set_pos()` is called
Then image is re-decoded and drawn directly (slow, but less memory)

---

### Requirement: Label Widget Documentation

The project documentation SHALL describe the Label widget for displaying text with alignment and long-text handling.

**API:**
```python
from widgets import Label
import M5

label = Label(
    text="Hello",
    x=10, y=10,
    w=100, h=20,           # Max dimensions for wrapping
    size=1.0,              # Text scale
    font_align=Label.LEFT_ALIGNED,  # or CENTER_ALIGNED, RIGHT_ALIGNED
    fg_color=0xFFFFFF,
    bg_color=0x000000,
    font=M5.Lcd.FONTS.DejaVu12,
    parent=M5.Lcd
)
label.set_text("New text")
label.set_text_color(fg, bg)
label.set_long_mode(Label.LONG_DOT)  # or LONG_WARP
label.set_pos(x, y)
```

**Alignment Constants:**
- `Label.LEFT_ALIGNED` (0)
- `Label.CENTER_ALIGNED` (1)
- `Label.RIGHT_ALIGNED` (2)

**Long Text Modes:**
- `Label.LONG_WARP` (0) - Wrap text to multiple lines
- `Label.LONG_DOT` (1) - Truncate with "..." in middle
- `Label.LONG_CLIP` (2) - Defined but not implemented

#### Scenario: Update label text with auto-clear
Given a Label widget displaying "Hello"
When `set_text("World")` is called
Then the previous text area is cleared with bg_color
And the new text is drawn

#### Scenario: Long text with dot truncation
Given a Label with `w=100` and `LONG_DOT` mode
When text exceeds 100 pixels width
Then text is displayed as "start...end"

---

### Requirement: Button Widget Status

The project documentation SHALL note that the Button widget is a stub with no implementation.

```python
from widgets import Button

class Button(Base):
    def __init__(self, parent) -> None:
        super().__init__(parent)
    # No additional methods
```

#### Scenario: Button is placeholder only
Given a Button widget instance
When any Base methods are called
Then they work as inherited from Base
But no button-specific behavior exists

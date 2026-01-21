# Cardputer ADV Troubleshooting

## When mpremote Can't Connect

If your code is blocking mpremote from connecting:

### Step 1: Use screen instead of mpremote

```bash
screen /dev/tty.usbmodem2101 115200
```

### Step 2: Interrupt the running program

Press **Ctrl+C** several times until you see:
```
KeyboardInterrupt:
raw REPL; CTRL-B to exit
>
```

### Step 3: Enter normal REPL

Press **Ctrl+B** to exit raw REPL. You should see:
```
MicroPython v1.25.0 on ...; M5STACK Cardputer with ESP32-S3-FN8
Type "help()" for more information.
>>>
```

### Step 4: Exit screen

Press **Ctrl+A**, then **K**, then **Y** to confirm.

### Step 5: Reconnect with mpremote

```bash
mpremote connect /dev/tty.usbmodem2101 mount . + repl
```

---

## REPL Modes

| Mode | How to Enter | Prompt | Use |
|------|--------------|--------|-----|
| Normal REPL | Ctrl+B from raw REPL | `>>>` | Interactive Python |
| Raw REPL | Ctrl+A from normal REPL | `>` | Machine-to-machine (mpremote uses this) |

---

## Quick Reference

| Action | Keys |
|--------|------|
| Interrupt running code | Ctrl+C |
| Enter raw REPL | Ctrl+A |
| Exit raw REPL to normal | Ctrl+B |
| Soft reset | Ctrl+D |
| Exit screen | Ctrl+A, K, Y |
| Exit mpremote repl | Ctrl+] or Ctrl+X |

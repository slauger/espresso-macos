# Espresso - Project Context for Claude Code

## What This Project Does

**espresso** is a macOS tool that keeps Citrix Viewer sessions alive and monitors for Microsoft Teams notifications.

## Architecture

Clean separation of concerns:

- **`espresso/core.py`** (`EspressoCore`): Keepalive via keyboard input (focuses window, sends Control key, restores focus)
- **`espresso/audio_monitor.py`** (`AudioMonitor`): Audio monitoring for Teams calls/notifications
- **`espresso/screen_monitor.py`** (`ScreenMonitor`): Screen capture + OCR for visual notifications
- **`espresso/gui.py`** (`EspressoApp`): macOS menu bar app (rumps) that orchestrates everything

## Key Technical Details

### Keepalive Method
- Focuses Citrix Viewer window temporarily (~300ms)
- Sends Control key (key code 59) via AppleScript
- Restores previous app focus immediately
- No longer uses mouse movement (was disruptive)

### Screen Monitoring
- Captures Citrix window screenshots using macOS Quartz API
- Color-based detection for Teams notification blue (#464775)
- OCR via macOS Vision Framework
- Filters OCR output to show only sender + message

### Configuration
- `~/.espresso/config.json` - main config
- Supports autostart for keepalive, audio, and screen monitoring
- See `examples/` for config templates

## Important Files

- `docs/DEVELOPMENT.md` - Detailed development history and troubleshooting
- `docs/AUDIO_FINGERPRINTING.md` - Audio fingerprinting docs
- `docs/SCREEN_MONITORING.md` - Screen monitoring implementation details
- `tools/` - Utility scripts (learn_sound.py, identify_sound.py, setup-autostart.sh)
- `tests/` - Test scripts

## Installation

```bash
pip install -e .
brew install cliclick  # (optional, was used for mouse movement)
```

## Usage

```bash
espresso-gui  # Launch menu bar app
espresso  # CLI version
```

## Current State

Everything works:
✅ Keepalive (focus + keyboard)
✅ Audio monitoring
✅ Screen monitoring with OCR
✅ GUI with autostart
✅ Smart notifications (foreground detection)

## Development Notes

- Project was recently cleaned up (tests moved to tests/, tools to tools/, docs to docs/)
- Removed unused code (cliclick mouse movement, unused helper methods)
- Removed `pixels` parameter (no longer needed after switching from mouse to keyboard)

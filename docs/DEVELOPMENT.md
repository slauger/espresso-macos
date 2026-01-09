# Espresso Development State - 2026-01-08

## Current Status: Screen Monitoring Implementation

### What We're Working On

Implementing **screen monitoring** to detect Teams notifications visually, because:
- Audio monitoring works for calls (sustained audio)
- But Teams chat notifications don't trigger audio in Citrix (audio routing issue)
- Solution: Monitor Citrix Viewer window for visual changes (notification popups)

### Current Problem

Testing window screenshot capture with `test_window_capture.py`:
- ✅ Can find Citrix Viewer windows via Quartz API
- ✅ Can identify OnScreen windows (Window ID: 54611, 1920x1055)
- ❌ CGWindowListCreateImage returns NULL (fails to capture)
- **Hypothesis**: Screen Recording permissions issue or Citrix-specific limitation

### What's Been Implemented So Far

#### 1. Audio Monitoring (Working ✅)
- `espresso/audio_monitor.py`: Audio fingerprinting and detection
- Peak tracking for short sounds (< 100ms)
- Block size reduced from 2048 to 1024 samples (~23ms latency)
- Detects incoming calls via sustained audio (> 3 seconds)

#### 2. Audio Fingerprinting (Implemented ✅)
- `espresso/audio_fingerprint.py`: Learn and identify specific sounds
- `learn_sound.py`: Record and learn notification sounds
- `identify_sound.py`: Real-time sound identification
- Stores fingerprints in `~/.espresso/audio_fingerprints.json`
- Uses RMS profile, frequency analysis, energy distribution

#### 3. Smart Notifications (Working ✅)
- `espresso/gui.py`: Foreground detection added
- Only sends notifications when Citrix is NOT in foreground
- Prevents spam during active use

#### 4. Autostart Feature (Working ✅)
- Config option: `"autostart": true` (keepalive)
- Config option: `"autostart_audio": true` (audio monitoring)
- `setup-autostart.sh`: One-command setup script
- Config file: `~/.espresso/config.json`

#### 5. Screen Monitoring (In Progress 🚧)
- `test_window_capture.py`: Test script for window capture
- **Current issue**: CGWindowListCreateImage returns NULL
- **Next**: Try alternative capture methods or check permissions

### Files Created This Session

```
espresso/
  ├── audio_fingerprint.py     # Audio fingerprinting system
  ├── screen_monitor.py         # (TODO) Screen monitoring
  └── notification_detector.py  # (TODO) Visual notification detection

test_window_capture.py          # Window capture test (debugging)
learn_sound.py                  # Learn notification sounds
identify_sound.py               # Identify sounds in real-time
test_audio.py                   # Audio level monitoring (improved with peaks)
setup-autostart.sh              # Autostart configuration script
test_foreground.py              # Test foreground app detection

examples/
  └── config-autostart.json     # Example config with autostart

AUDIO_FINGERPRINTING.md         # Complete docs for audio fingerprinting
```

### Current Config Structure

```json
{
  "app_name": "Citrix Viewer",
  "interval_seconds": 60,
  "move_pixels": 1,
  "audio_device": "BlackHole",
  "notification_threshold": 0.05,
  "call_threshold": 0.02,
  "call_duration": 3.0,
  "autostart": true,
  "autostart_audio": true,

  "screen_monitoring": {
    "enabled": false,
    "scan_interval": 2,
    "detection_method": "color",
    "teams_notification_color": "#464775",
    "color_tolerance": 30,
    "min_pixels": 1000
  }
}
```

### Technical Issues Encountered

#### Issue 1: Audio Not Captured (SOLVED ✅)
- **Problem**: Multi-Output Device not routing audio to BlackHole
- **Solution**: Recreate Multi-Output with correct order (Speakers first, then BlackHole)
- **Command**: `sudo killall coreaudiod` to restart audio

#### Issue 2: Short Notifications Missed (SOLVED ✅)
- **Problem**: Teams notifications < 100ms missed between audio blocks
- **Solution**:
  - Reduced block size: 2048 → 1024 samples
  - Added peak tracking (holds max level for 0.5s)
  - Uses `max(rms, peak_level)` for detection

#### Issue 3: Notification Spam (SOLVED ✅)
- **Problem**: Getting notified during active Citrix use
- **Solution**: Added foreground detection via AppleScript
- **Code**: `is_app_in_foreground()` checks frontmost app

#### Issue 4: Window Capture Fails (CURRENT 🚧)
- **Problem**: CGWindowListCreateImage returns NULL for Citrix window
- **Status**:
  - Window ID found: 54611 (OnScreen: True)
  - Window bounds: 1920x1055 @ (1923, 25)
  - Capture returns NULL (permission issue?)
- **Next Steps**:
  1. Check Screen Recording permissions
  2. Try `screencapture -l<window_id>` command
  3. Try capturing entire screen and cropping
  4. If all fail: Fallback to audio-only + manual config

### Screenshot Example

See `Bildschirmfoto.png`:
- Teams notification popup in bottom-right
- Dark blue background (~#464775)
- Text: "(Gast) Simon Lauger" + "Hallo dies ist eine Test Nachricht"
- Button: "Schnelle Antwort senden"
- Appears for ~5 seconds

### Screen Monitoring Plan

**Detection Strategy: Color-Based**
1. Capture Citrix Viewer window screenshot
2. Crop to bottom-right region (where notifications appear)
3. Count pixels matching Teams blue color (#464775 ± tolerance)
4. If > 1000 pixels → Notification detected
5. Scan every 2 seconds (notification lasts 5s)

**Alternative if capture fails:**
- Option A: Capture entire screen, find Citrix region
- Option B: Use Accessibility API
- Option C: Fallback to audio-only (works for calls at least)

### Dependencies Installed

```bash
pip install espresso-app[full]
pip install pyobjc-framework-Quartz  # For window capture
pip install Pillow                   # For image processing
pip install sounddevice numpy        # For audio monitoring
pip install rumps                    # For GUI menu bar
```

### How to Test Current State

#### Test Audio Monitoring
```bash
python3 test_audio.py
# Play Teams notification in Citrix, watch for peaks
```

#### Test Audio Fingerprinting
```bash
# Learn a sound
python3 learn_sound.py teams_notification
# (Play notification immediately when recording starts)

# Identify sounds
python3 identify_sound.py
# (Play notification again, should identify it)
```

#### Test Window Capture
```bash
python3 test_window_capture.py
# Currently fails at capture step (returns NULL)
```

#### Test Foreground Detection
```bash
python3 test_foreground.py
# Shows which app is currently active
```

#### Run GUI with Autostart
```bash
# Setup config first
./setup-autostart.sh

# Launch (everything starts automatically)
espresso-gui
```

### Known Limitations

1. **Audio Routing**:
   - Requires BlackHole + Multi-Output Device setup
   - Only works if Citrix audio routed through BlackHole
   - Chat notifications may not produce audio at all

2. **Window Capture**:
   - CGWindowListCreateImage may not work for all window types
   - Citrix might use special rendering (remote desktop)
   - May require Screen Recording permissions in System Settings

3. **Notification Timing**:
   - Teams notifications only visible for 5 seconds
   - Need to poll < 5s to catch them
   - 2-second interval recommended

### Next Steps

1. **Debug Window Capture**
   - Check System Settings → Privacy & Security → Screen Recording
   - Try alternative capture method (screencapture command)
   - Test if Citrix uses special protected window mode

2. **If Capture Works**
   - Implement `espresso/screen_monitor.py`
   - Add color-based detection
   - Integrate with GUI (toggle on/off)
   - Add to autostart config

3. **If Capture Fails**
   - Document limitation in README
   - Focus on audio-only solution
   - Consider asking user to test on different machine
   - Or: Capture full screen instead of window

### Important Window IDs (Current Session)

```
Citrix Viewer Windows:
- ID: 54611 (OnScreen: True)  1920x1055 @ (1923, 25)  ← Main window
- ID: 54603 (OnScreen: True)  1200x982  @ (2261, 68)  ← Secondary?
- Many other windows (OnScreen: False) - menu bars, etc.
```

### Config File Location

```bash
~/.espresso/config.json          # Auto-loaded default config
~/.espresso/audio_fingerprints.json  # Learned sounds
```

### Commands to Remember

```bash
# List all windows
python3 -c "import Quartz; ..."

# List audio devices
python3 -c "import sounddevice as sd; print(sd.query_devices())"
# Or: espresso-list-audio

# List running apps
espresso-list

# Restart audio service
sudo killall coreaudiod

# Kill background processes
pkill -f test_audio.py
```

### Terminal Restart Required Because...

Need to test screencapture command with window ID, which may have different behavior/permissions than Python Quartz API.

## Summary

**What Works:**
- ✅ Keepalive (mouse/keyboard simulation)
- ✅ Audio monitoring for calls
- ✅ Audio fingerprinting for sound identification
- ✅ Smart notifications (foreground detection)
- ✅ Autostart configuration
- ✅ GUI with menu bar integration

**What's In Progress:**
- 🚧 Screen monitoring for visual notifications
- 🚧 Window screenshot capture (permission/capability issue)

**What's Blocked:**
- ❌ Window capture returns NULL (need to debug permissions or try alternative)

**Next Action After Terminal Restart:**
Test if `screencapture -l<window_id>` works better than CGWindowListCreateImage API.

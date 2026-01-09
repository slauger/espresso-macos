<div align="center">
  <img src="icons/icon-256.png" alt="Espresso Logo" width="128" height="128">

  # ☕ Espresso

  [![PyPI](https://img.shields.io/pypi/v/espresso-app)](https://pypi.org/project/espresso-app/)
  [![Python](https://img.shields.io/pypi/pyversions/espresso-app)](https://pypi.org/project/espresso-app/)
  [![License](https://img.shields.io/pypi/l/espresso-app)](LICENSE)

  **Keep your apps awake with a shot of activity** ☕
</div>

Prevent applications from timing out or locking by simulating periodic mouse/keyboard activity on macOS.

## Quick Start

### Manual Start

```bash
# Install
pip install espresso-app[full]

# Launch GUI
espresso-gui --audio-device "BlackHole"
```

Click the menu bar icon ☕ → Start → Enable Audio Monitor

### Autostart Everything

```bash
# 1. Install with full support
pip install espresso-app[full]

# 2. Create config
mkdir -p ~/.espresso
cat > ~/.espresso/config.json << 'EOF'
{
  "app_name": "Citrix Viewer",
  "interval_seconds": 60,
  "audio_device": "BlackHole",
  "autostart": true,
  "autostart_audio": true,
  "autostart_screen": true,
  "screen_monitoring": {
    "enabled": true,
    "scan_interval": 2,
    "teams_notification_color": "#464775"
  }
}
EOF

# 3. Launch (everything starts automatically!)
espresso-gui

# Optional: Enable debug logging
espresso-gui --debug
```

## Features

- ☕ **Universal**: Works with any macOS app (Citrix, Teams, Slack, etc.)
- 🎨 **GUI & CLI**: Menu bar app OR command-line tool
- ⚙️ **Configurable**: Custom intervals, target apps
- 🧠 **Smart**: Only active when target app is running
- 🪶 **Lightweight**: Minimal resource usage
- 🔒 **Safe**: Non-intrusive keyboard simulation
- 🔔 **Audio Monitoring**: Detect Teams calls and notifications via audio
- 📺 **Screen Monitoring**: Visual notification detection with OCR

## Audio Monitoring

**Never miss a call or notification again!** 📞

Espresso can monitor audio from your remote desktop session to detect:
- 🔔 **Notification sounds** (Teams messages, alerts)
- 📞 **Incoming calls** (sustained audio activity)
- macOS notifications delivered to your local machine
- 🧠 **Smart filtering**: Only notifies when you're NOT actively using the app (no spam during calls!)

### How It Works

1. Install BlackHole (virtual audio device)
2. Route Citrix/Teams audio through BlackHole
3. Espresso monitors BlackHole for audio spikes
4. Sends macOS notifications when detected

### Quick Setup

```bash
# 1. Install BlackHole
brew install blackhole-2ch

# 2. Install Espresso with audio support
pip install espresso-app[full]

# 3. Launch with audio monitoring
espresso-gui --audio-device "BlackHole"
```

Then click "Enable Audio Monitor" in the menu bar!

See [Audio Monitoring Setup](#audio-monitoring-setup) below for detailed instructions.

## Screen Monitoring

**Catch visual notifications even when audio isn't available!** 📺

Screen monitoring detects Teams notifications by:
- 📸 **Screenshot analysis**: Captures window screenshots every 2 seconds
- 🎨 **Color detection**: Identifies Teams notification blue color (#464775)
- 📝 **OCR extraction**: Reads notification text using macOS Vision Framework
- 🧠 **Smart filtering**: Only notifies when Citrix is NOT in foreground

### Quick Setup

```bash
# Enable in config
cat > ~/.espresso/config.json << 'EOF'
{
  "app_name": "Citrix Viewer",
  "autostart_screen": true,
  "screen_monitoring": {
    "enabled": true,
    "scan_interval": 2,
    "teams_notification_color": "#464775"
  }
}
EOF

# Launch (screen monitoring starts automatically!)
espresso-gui
```

Or enable manually via menu bar: "Enable Screen Monitor"

**Requirements:**
- macOS Screen Recording permission
- Citrix Viewer window visible (doesn't need to be focused)

## Why "Espresso"?

Just like a shot of espresso keeps _you_ awake, this app keeps your _sessions_ awake! ☕

## Installation

### From PyPI

```bash
# CLI only
pip install espresso-app

# With GUI (recommended)
pip install espresso-app[gui]

# With audio monitoring
pip install espresso-app[audio]

# Full installation (GUI + Audio)
pip install espresso-app[full]
```

### From Source

```bash
git clone https://github.com/yourusername/espresso-app.git
cd espresso-app
pip install -e ".[gui]"
```

## Setup

### 1. Grant Accessibility Permissions

macOS requires permission to simulate keyboard/mouse activity:

1. **System Settings** → **Privacy & Security** → **Accessibility**
2. Add **Python** or **Terminal**
3. Enable the checkbox

### 2. (Optional) Install cliclick

For precise mouse movement (otherwise uses keyboard activity):

```bash
brew install cliclick
```

## Usage

### GUI Version (Recommended)

```bash
espresso-gui
```

A ☕ icon appears in your menu bar. Click it and select "Start".

**Icons:**
- 🟢 **Green**: Target app running, actively keeping alive
- 🟡 **Yellow**: Monitoring, but app not running
- ⏸ **Paused**: Monitoring stopped
- ⚠️ **Warning**: Errors occurred

**Custom Configuration:**

```bash
# Monitor Microsoft Teams with 2-minute interval
espresso-gui --app "Microsoft Teams" --interval 120

# Autostart keepalive on launch
espresso-gui --autostart

# Autostart keepalive AND audio monitoring
espresso-gui --autostart --autostart-audio --audio-device "BlackHole"

# Use config file (recommended for autostart)
espresso-gui --config config.json
```

### CLI Version

```bash
# Default: Monitors Citrix Viewer, 60s interval
espresso

# Custom app and interval
espresso --app "Microsoft Teams" --interval 120

# More pixels, less frequent
espresso --app "Slack" --interval 300 --pixels 2

# Use config file
espresso --config config.json
```

**Options:**

```
--app APP           Name of application to monitor (default: "Citrix Viewer")
--interval SECONDS  Interval between actions (default: 60)
--pixels PIXELS     Pixels to move mouse (default: 1)
--config FILE       Path to JSON config file
```

**Run in Background:**

```bash
# Start in background
nohup espresso --app "Citrix Viewer" > ~/espresso.log 2>&1 &

# View logs
tail -f ~/espresso.log

# Stop
pkill -f espresso
```

### Find Your App Name

```bash
espresso-list
```

Shows all running apps. Look for your target app's exact name (e.g., "Citrix Viewer", "Microsoft Teams").

## Configuration File

**Default location:** `~/.espresso/config.json` (automatically loaded if exists)

Create default config with autostart:

```bash
mkdir -p ~/.espresso
cat > ~/.espresso/config.json << 'EOF'
{
  "app_name": "Citrix Viewer",
  "interval_seconds": 60,
  "move_pixels": 1,
  "audio_device": "BlackHole",
  "notification_threshold": 0.05,
  "call_threshold": 0.02,
  "call_duration": 3.0,
  "autostart": true,
  "autostart_audio": true
}
EOF
```

**Config Options:**
- `app_name`: Application to monitor
- `interval_seconds`: Interval between keepalive actions
- `move_pixels`: Pixels to move mouse
- `audio_device`: Audio device name for monitoring (e.g., "BlackHole")
- `notification_threshold`: Sensitivity for notification sounds (0-1, default: 0.05)
- `call_threshold`: Sensitivity for call detection (0-1, default: 0.02)
- `call_duration`: Seconds of sustained audio to detect as call (default: 3.0)
- `autostart`: Start keepalive monitoring automatically (default: false)
- `autostart_audio`: Start audio monitoring automatically (default: false)

Or use custom config location:

```bash
espresso --config my-config.json
espresso-gui --config my-config.json
```

**Config Priority:** CLI arguments > Custom config file > `~/.espresso/config.json` > Defaults

Example configs in `examples/`.

## Examples

### Citrix Remote Desktop

```bash
espresso-gui --autostart
```

### Microsoft Teams

```bash
espresso-gui --app "Microsoft Teams" --interval 120 --autostart
```

### Multiple Apps

Monitor different apps simultaneously:

```bash
# Terminal 1: Citrix
espresso --app "Citrix Viewer" &

# Terminal 2: Teams
espresso --app "Microsoft Teams" --interval 300 &
```

## How It Works

1. **Detection**: Uses AppleScript to check if target app is running
2. **Activity Simulation**:
   - **With cliclick**: Precise mouse movement (preferred)
   - **Without cliclick**: Keyboard activity via Shift key press
3. **Smart Activation**: Only acts when target app has windows open
4. **Minimal Impact**:
   - Mouse mode: Moves cursor by specified pixels, then back (imperceptible)
   - Keyboard mode: Single Shift key press (no visible effect)

## Audio Monitoring Setup

Get notifications for Teams calls and messages on your local Mac!

### Prerequisites

1. **Install BlackHole** (virtual audio device):
   ```bash
   brew install blackhole-2ch
   ```

2. **Install Espresso with audio support**:
   ```bash
   pip install espresso-app[full]
   ```

### macOS Audio Configuration

#### Option 1: Multi-Output Device (Recommended)

This lets you hear audio AND monitor it:

1. Open **Audio MIDI Setup** (Applications → Utilities)
2. Click **+** (bottom left) → **Create Multi-Output Device**
3. Name it "BlackHole + Output"
4. Check both:
   - ✅ **BlackHole 2ch**
   - ✅ **Your speakers/headphones**
5. In Citrix Viewer → Preferences → Audio, select "BlackHole + Output"

#### Option 2: Monitor Only

If you don't need to hear the audio:

1. In Citrix Viewer → Preferences → Audio
2. Select **BlackHole 2ch** as output device

### Configure Espresso

```bash
# List available audio devices
espresso-list-audio

# Launch with audio monitoring
espresso-gui --audio-device "BlackHole"
```

### Enable in GUI

1. Launch `espresso-gui`
2. Click menu bar icon
3. Click **"Enable Audio Monitor"**
4. Test with a Teams notification sound

### What You'll See

- 🔔 **Notification detected**: Short audio spike (< 1 second)
  - macOS notification: "Teams Notification"
  - **Smart filtering**: Only notifies when Citrix is NOT in foreground

- 📞 **Incoming call**: Sustained audio (> 3 seconds)
  - macOS notification: "Incoming Call" with sound alert
  - **Smart filtering**: Only notifies when Citrix is NOT in foreground

- 📞 **Call ended**: Audio activity stopped
  - Always notified (even if Citrix is active)

### Customizing Thresholds

Edit config file:

```json
{
  "app_name": "Citrix Viewer",
  "interval_seconds": 60,
  "move_pixels": 1,
  "audio_device": "BlackHole",
  "notification_threshold": 0.05,
  "call_threshold": 0.02,
  "call_duration": 3.0
}
```

- `notification_threshold`: Sensitivity for short sounds (0-1)
- `call_threshold`: Sensitivity for calls (0-1)
- `call_duration`: Seconds of audio to detect as call

## Troubleshooting

### Actions not working

1. **Grant Accessibility Permissions** (see Setup above)
2. **Verify app is running**: `espresso-list`
3. **Install cliclick**: `brew install cliclick`

### GUI not starting

Ensure rumps is installed:

```bash
pip install rumps
```

### Can't find app name

Run `espresso-list` to see exact names of running apps.

### Audio monitoring not working

1. **Check BlackHole is installed**:
   ```bash
   brew list blackhole-2ch
   ```

2. **List audio devices**:
   ```bash
   espresso-list-audio
   ```
   Verify BlackHole appears in the list

3. **Check Citrix audio output**:
   - Citrix Viewer → Preferences → Audio
   - Should be set to "BlackHole" or "BlackHole + Output"

4. **Check permissions**:
   - System Settings → Privacy & Security → Microphone
   - Add Python/Terminal if needed

5. **Test audio levels**:
   - Play a Teams notification in Citrix
   - Check `espresso-gui` logs for audio levels

### No notifications appearing

1. **Check macOS notification settings**:
   - System Settings → Notifications
   - Find "Python" or "Terminal"
   - Enable "Allow Notifications"

2. **Test notifications**:
   ```bash
   osascript -e 'display notification "Test" with title "Test"'
   ```

## Development

### Project Structure

```
espresso-app/
├── espresso/
│   ├── __init__.py      # Package metadata
│   ├── core.py          # Core keepalive logic
│   ├── cli.py           # CLI entry point
│   ├── gui.py           # GUI entry point
│   ├── audio_monitor.py # Audio monitoring (NEW!)
│   ├── list_apps.py     # App listing utility
│   ├── list_audio.py    # Audio device listing
│   └── utils.py         # Helper functions
├── examples/
│   └── config.example.json
├── pyproject.toml       # Package configuration
├── README.md
└── LICENSE
```

### Building

```bash
pip install build
python -m build
```

### Testing Locally

```bash
pip install -e ".[gui]"
espresso --help
espresso-gui
espresso-list
```

## Publishing to PyPI

```bash
# Build
python -m build

# Upload to TestPyPI (optional)
python -m twine upload --repository testpypi dist/*

# Upload to PyPI
python -m twine upload dist/*
```

## Requirements

- **macOS** (Monterey or later recommended)
- **Python 3.8+**
- **Optional**:
  - `rumps>=0.4.0` (for GUI)
  - `sounddevice>=0.4.6` + `numpy>=1.20.0` (for audio monitoring)
  - `cliclick` (for precise mouse movement)
  - BlackHole 2ch (for audio capture)

## License

MIT License - see [LICENSE](LICENSE)

## Contributing

Contributions welcome! Please open an issue or submit a pull request.

## Changelog

### 0.1.0 (2026-01-08)

- Initial release
- CLI and GUI versions
- Configurable app monitoring
- Mouse and keyboard fallback modes
- Menu bar integration with visual status
- **Audio monitoring** for Teams calls and notifications
- BlackHole integration for audio capture
- macOS notifications for remote desktop events

---

Made with ☕ and Python

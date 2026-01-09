<div align="center">
  <img src="icons/icon-256.png" alt="Espresso Logo" width="128" height="128">

  # ☕ Espresso

  **Keep your macOS apps awake and never miss a notification**

  [![License](https://img.shields.io/github/license/simonlauger/espresso)](LICENSE)
  [![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

</div>

---

## What is Espresso?

Espresso prevents session timeouts and monitors for notifications in remote desktop applications (like Citrix Viewer) on macOS.

**Three monitoring modes:**
- 🎹 **Keepalive** - Simulates keyboard activity to prevent timeouts
- 🔔 **Audio Monitoring** - Detects Teams calls/notifications via audio
- 📺 **Screen Monitoring** - Visual notification detection with OCR

## Quick Start

### Option 1: Download Binary (Recommended)

1. Download the latest release from [GitHub Releases](https://github.com/slauger/espresso-macos/releases)
2. Open the DMG and drag **Espresso.app** to Applications
3. **First launch**: Right-click Espresso.app → "Open" → Click "Open" again
   - macOS will show a Gatekeeper warning (app is not signed)
   - Alternative: `xattr -cr /Applications/Espresso.app` in Terminal

The ☕ icon appears in your menu bar. Click it to enable features.

> **Note**: The app is not code-signed (requires Apple Developer Account $99/year). It's safe to run, source code is public.

### Option 2: Install from Source

```bash
# Clone and install
git clone https://github.com/slauger/espresso-macos.git
cd espresso-macos
pip install -e .[full]

# Launch GUI (works without config!)
espresso-gui

# Optional: Setup autostart with config
mkdir -p ~/.espresso
cp examples/config-autostart.json ~/.espresso/config.json
```

## Features

- ☕ **Universal** - Works with any macOS app (Citrix, Teams, Slack)
- 🎨 **Menu Bar GUI** - Simple click-to-enable interface
- ⚙️ **Configurable** - JSON config or command-line options
- 🧠 **Smart** - Only monitors when app is running
- 🔒 **Non-intrusive** - Keyboard simulation (no mouse movement)
- 📦 **Lightweight** - Minimal resource usage

## Configuration

**Configuration is optional!** Espresso works out of the box with sensible defaults.

### Optional: Create `~/.espresso/config.json`

```json
{
  "app_name": "Citrix Viewer",
  "interval_seconds": 60,
  "autostart": true,
  "autostart_audio": true,
  "audio_device": "BlackHole 2ch"
}
```

**Default values** (when no config exists):
- `app_name`: "Citrix Viewer"
- `interval_seconds`: 60
- `autostart`: false (manual start)
- `audio_device`: null (configure for audio monitoring)

See [`examples/`](examples/) for complete configuration examples.

## Advanced Features

### Audio Monitoring
Monitor audio from remote desktop to catch Teams calls and notifications.

📖 **[Audio Monitoring Setup Guide](docs/AUDIO_SETUP.md)**

### Screen Monitoring
Detect notifications visually via screenshot analysis and OCR.

📖 **[Screen Monitoring Setup Guide](docs/SCREEN_MONITORING.md)**

## Documentation

- 📖 [Audio Monitoring Setup](docs/AUDIO_SETUP.md)
- 📖 [Audio Fingerprinting](docs/AUDIO_FINGERPRINTING.md)
- 📖 [Screen Monitoring Setup](docs/SCREEN_MONITORING.md)
- 📖 [Development Guide](docs/DEVELOPMENT.md)
- 📋 [Config Examples](examples/)

## Installation

### Binary Release (Recommended)

Download from [GitHub Releases](https://github.com/slauger/espresso-macos/releases):
- **Espresso-macOS.dmg** - Drag & drop installer
- **Espresso-macOS.zip** - Portable .app bundle

### From Source

```bash
git clone https://github.com/slauger/espresso-macos.git
cd espresso-macos
pip install -e .[full]
```

**Build your own binary:**
```bash
pip install pyinstaller
pyinstaller espresso-gui.spec
# → dist/Espresso.app
```

## Usage

### Launch the App

- **Binary**: Open Espresso.app from Applications
- **From source**: Run `espresso-gui` in terminal

Click the ☕ menu bar icon to:
- Enable/disable keepalive
- Enable/disable audio monitoring
- Enable/disable screen monitoring
- View status and logs

### CLI (Optional)

For automation or headless usage:
```bash
espresso --app "Citrix Viewer" --interval 60 --config ~/.espresso/config.json
```

## Command-Line Options

```
espresso-gui [OPTIONS]

Options:
  --app TEXT              Target application name (default: Citrix Viewer)
  --interval INT          Seconds between keepalive actions (default: 60)
  --audio-device TEXT     Audio device for monitoring (e.g., BlackHole)
  --autostart            Start keepalive automatically
  --autostart-audio      Start audio monitoring automatically
  --autostart-screen     Start screen monitoring automatically
  --debug                Enable verbose logging
  --config PATH          Path to JSON config file
```

## Requirements

- macOS 10.15+
- Python 3.9+

**Optional:**
- [BlackHole](https://github.com/ExistentialAudio/BlackHole) for audio monitoring
- Screen Recording permission for screen monitoring

## Why "Espresso"?

Just like a shot of espresso keeps *you* awake, this app keeps your *sessions* awake! ☕

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

Issues and pull requests welcome!

For major changes, please open an issue first to discuss what you'd like to change.

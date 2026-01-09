# Audio Monitoring Setup Guide

Complete guide to set up audio monitoring for Teams calls and notifications in Citrix Viewer.

## Overview

Audio monitoring detects:
- 📞 **Incoming calls** - Sustained audio activity (>3 seconds)
- 🔔 **Notifications** - Short sound bursts (<100ms)
- Only notifies when Citrix is NOT in foreground (no spam!)

## Prerequisites

- macOS 10.15+
- [BlackHole](https://github.com/ExistentialAudio/BlackHole) virtual audio device
- Citrix Viewer with audio enabled

## Step 1: Install BlackHole

BlackHole creates a virtual audio device that captures audio from Citrix:

```bash
# Via Homebrew (recommended)
brew install blackhole-2ch

# Or download from: https://github.com/ExistentialAudio/BlackHole
```

After installation, restart your Mac.

## Step 2: Create Multi-Output Device

This routes audio to BOTH your speakers AND BlackHole for monitoring:

1. Open **Audio MIDI Setup** (`/Applications/Utilities/Audio MIDI Setup.app`)
2. Click the **+** button (bottom left) → **Create Multi-Output Device**
3. Name it: `Multi-Output Device`
4. **Check BOTH:**
   - ✅ **Your Speakers** (e.g., "MacBook Pro Speakers" or "External Headphones")
   - ✅ **BlackHole 2ch**
5. **Important:** Speakers must be FIRST in the list!
6. Set **Master Device** to your speakers (right-click → "Use This Device For Sound Output")

### Correct Order:
```
Multi-Output Device
  ✓ MacBook Pro Speakers (Master)
  ✓ BlackHole 2ch
```

### Why This Order Matters:
- Speakers first = You hear audio
- BlackHole second = Espresso monitors audio
- Wrong order = No audio to speakers!

## Step 3: Route Citrix Audio

Configure Citrix to send audio through Multi-Output Device:

### Option A: System-Wide (Easiest)

1. Open **System Settings** → **Sound** → **Output**
2. Select **Multi-Output Device**
3. All system audio (including Citrix) now routes through it

### Option B: Per-App (macOS Ventura+)

1. Open Citrix Viewer
2. **Control-click** the Volume icon in menu bar
3. Under "Output Device", select **Multi-Output Device**
4. Only Citrix audio routes through it

### Verify Audio Routing

Test in Citrix:
1. Play a Teams notification or video
2. You should **hear audio** through your speakers
3. Espresso will monitor via BlackHole

## Step 4: Configure Espresso

Create `~/.espresso/config.json`:

```json
{
  "app_name": "Citrix Viewer",
  "interval_seconds": 60,
  "audio_device": "BlackHole 2ch",
  "notification_threshold": 0.05,
  "call_threshold": 0.02,
  "call_duration": 3.0,
  "autostart_audio": true
}
```

### Configuration Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `audio_device` | `null` | Audio input device name (must be "BlackHole 2ch") |
| `notification_threshold` | `0.05` | RMS level for notification detection (0.0-1.0) |
| `call_threshold` | `0.02` | RMS level for call detection (0.0-1.0) |
| `call_duration` | `3.0` | Seconds of sustained audio to trigger call (float) |
| `autostart_audio` | `false` | Start audio monitoring automatically on launch |

### Tuning Detection Sensitivity

**If missing notifications:**
- Lower `notification_threshold` (try 0.03 or 0.02)
- Lower `call_threshold` (try 0.015)

**If getting false positives:**
- Raise `notification_threshold` (try 0.07 or 0.10)
- Raise `call_threshold` (try 0.03)

**For longer call rings:**
- Increase `call_duration` (try 4.0 or 5.0)

## Step 5: Launch Espresso

```bash
espresso-gui
```

The ☕ icon appears in menu bar. Click **"Enable Audio Monitor"**.

You should see:
```
Audio Monitor Enabled
Monitoring for audio activity
Device: BlackHole 2ch
```

## Testing

### Test Notification Detection

1. Ensure Citrix is NOT in foreground (click another app)
2. Play a Teams notification in Citrix
3. You should get a macOS notification from Espresso

### Test Call Detection

1. Ensure Citrix is NOT in foreground
2. Start a Teams call (or play sustained audio for >3 seconds)
3. You should get "Call activity detected" notification

## Troubleshooting

### "No audio device found"

**Check device name:**
```bash
espresso-list-audio
```

Look for `BlackHole 2ch` in the list. Copy the **exact name** to your config.

### "No audio detected"

1. **Verify BlackHole is receiving audio:**
   ```bash
   # Terminal 1: Monitor audio levels
   python3 tests/test_audio.py

   # Terminal 2: Play audio in Citrix
   ```

   You should see RMS levels > 0.0 when audio plays.

2. **Check Multi-Output Device:**
   - Open Audio MIDI Setup
   - Verify BOTH speakers and BlackHole are checked
   - Speakers must be FIRST in list

3. **Restart audio service:**
   ```bash
   sudo killall coreaudiod
   ```

   Then reopen Audio MIDI Setup and recreate Multi-Output Device.

### "Audio detected but no notification"

- Citrix might be in foreground (smart filtering prevents spam)
- Check notification threshold in config (try lowering it)
- Enable debug logging: `espresso-gui --debug`

### "I hear no audio"

- Multi-Output Device order is wrong (speakers must be first)
- Master Device not set (right-click speakers → "Use This Device For Sound Output")
- Speakers not checked in Multi-Output Device

## Advanced: Audio Fingerprinting

Learn specific notification sounds for accurate identification:

📖 **See [Audio Fingerprinting Guide](AUDIO_FINGERPRINTING.md)**

This allows Espresso to:
- Identify specific notification types
- Ignore background noise
- Reduce false positives

## Removing Audio Monitoring

To remove BlackHole and Multi-Output Device:

1. **System Settings** → **Sound** → **Output** → Select your speakers
2. **Audio MIDI Setup** → Delete Multi-Output Device
3. Uninstall BlackHole:
   ```bash
   brew uninstall blackhole-2ch
   ```

Your system audio returns to normal.

## Tips

- Use `notification_threshold` > `call_threshold` (calls are usually quieter)
- Test with debug logging first: `espresso-gui --debug`
- Keep Citrix window visible but unfocused for best results
- BlackHole uses minimal CPU (~0.1%)

## See Also

- [Audio Fingerprinting Guide](AUDIO_FINGERPRINTING.md) - Learn specific sounds
- [Screen Monitoring Guide](SCREEN_MONITORING.md) - Visual detection alternative
- [Config Examples](../examples/) - Sample configurations

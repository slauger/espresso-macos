# Audio Fingerprinting & Sound Identification

Espresso can learn specific notification sounds and identify them automatically!

## How It Works

The audio fingerprinting system analyzes sounds based on:

1. **Duration**: How long the sound lasts
2. **RMS Profile**: The "shape" of the sound over time
3. **Frequency Analysis**: Which frequencies are dominant
4. **Energy Distribution**: Balance between low, mid, and high frequencies
5. **Peak Characteristics**: Peak level and timing

These characteristics create a unique "fingerprint" for each sound.

## Quick Start

### Step 1: Learn a Sound

Play a Teams notification in Citrix and record it:

```bash
python3 learn_sound.py teams_notification
```

When prompted:
1. The script starts recording
2. **Immediately** play the Teams notification in Citrix
3. Recording stops after 2 seconds
4. The fingerprint is saved to `~/.espresso/audio_fingerprints.json`

### Step 2: Test Identification

```bash
python3 identify_sound.py
```

Now play the same notification again and watch it get identified! 🎉

## Learning Multiple Sounds

You can learn different sounds:

```bash
# Learn notification sound
python3 learn_sound.py teams_notification

# Learn incoming call sound
python3 learn_sound.py teams_call_incoming

# Learn call end sound
python3 learn_sound.py teams_call_end

# Learn message sound
python3 learn_sound.py teams_message
```

## Integration with Espresso GUI

The audio fingerprinting is automatically integrated:

1. When audio monitoring detects a sound, it tries to identify it
2. If confidence is > 60%, it shows the specific sound name
3. If confidence is < 60%, it shows "Unknown notification"

Example notification:
```
🔔 Teams Notification (teams_message)
Detected with 87% confidence
```

## Viewing Learned Sounds

```bash
cat ~/.espresso/audio_fingerprints.json
```

Shows all learned sounds with their characteristics.

## Troubleshooting

### "Very low audio level detected"

- Check that Citrix audio is routed through BlackHole
- Check Multi-Output Device configuration
- Play the sound louder

### "No learned sounds found"

- Run `learn_sound.py` first to learn at least one sound
- Check that `~/.espresso/audio_fingerprints.json` exists

### Sound not identified correctly

- Learn the sound again with `learn_sound.py`
- Make sure to play the sound immediately when recording starts
- Try increasing the recording by playing the sound right at the start

### Always shows "Unknown sound"

- The confidence threshold is 60%
- Try learning the sound again in a quieter environment
- Make sure the sound is consistent (same volume, same device)

## How Accurate Is It?

The system compares multiple characteristics:

- **Duration**: Must be within ±50% to match
- **Shape**: Correlation coefficient > 0.6
- **Frequency**: Energy distribution within ±30%
- **Overall**: Average confidence > 60% to identify

Typical results:
- Same sound, same device: 85-95% confidence ✅
- Same sound, different volume: 70-85% confidence ✅
- Similar sounds: 40-60% confidence ❌
- Different sounds: 0-30% confidence ❌

## Advanced Usage

### Adjust Confidence Threshold

Edit `espresso/audio_monitor.py` and change:

```python
sound_name, confidence = fp.identify_sound(
    audio_data,
    sample_rate,
    min_confidence=0.6  # Lower = more matches, higher = more strict
)
```

### View Fingerprint Details

```python
from espresso.audio_fingerprint import AudioFingerprint

fp = AudioFingerprint()
for name, fingerprint in fp.fingerprints.items():
    print(f"{name}:")
    print(f"  Duration: {fingerprint['active_duration']:.3f}s")
    print(f"  Peak: {fingerprint['peak_level']:.3f}")
    print(f"  Energy: Low={fingerprint['energy_distribution']['low']:.2f}")
```

### Delete a Learned Sound

```bash
# Edit the JSON file and remove the entry
nano ~/.espresso/audio_fingerprints.json
```

Or delete all:

```bash
rm ~/.espresso/audio_fingerprints.json
```

## Technical Details

### Fingerprint Structure

```json
{
  "teams_notification": {
    "duration": 0.523,
    "active_duration": 0.423,
    "peak_level": 0.234,
    "mean_level": 0.067,
    "rms_profile": [0.01, 0.05, 0.23, 0.15, 0.08, ...],
    "top_frequencies": [1200.5, 2400.3, 800.1, 3200.7, 1600.2],
    "energy_distribution": {
      "low": 0.25,
      "mid": 0.60,
      "high": 0.15
    },
    "learned_at": "2026-01-08T12:00:00",
    "sample_rate": 44100
  }
}
```

### Comparison Algorithm

1. **Duration matching**: `score = 1 - (|dur1 - dur2| / max(dur1, dur2)) * 2`
2. **Peak matching**: `score = 1 - |peak1 - peak2| / max(peak1, peak2)`
3. **Shape matching**: Pearson correlation of normalized RMS profiles
4. **Energy matching**: `score = 1 - avg_diff_across_bands`
5. **Final score**: Average of all component scores

### Performance

- Learning: ~0.1s per sound
- Identification: ~0.05s per comparison
- Memory: ~1KB per learned sound

## Examples

### Example 1: Learn Teams Notification

```bash
$ python3 learn_sound.py teams_notification
=== Available Audio Devices ===
2: Elgato Wave:3
10: BlackHole 2ch
11: MacBook Pro-Mikrofon

✅ Using: BlackHole 2ch

🎤 Recording sound 'teams_notification'...
   Play the notification sound NOW!
   Recording for 2 seconds...

✅ Recording complete! RMS level: 0.0823
🔍 Trimmed to active audio: 0.412s
✅ Learned sound: teams_notification
   Duration: 0.412s
   Peak level: 0.234

🎉 Sound 'teams_notification' learned successfully!
   Stored in: /Users/simon/.espresso/audio_fingerprints.json
```

### Example 2: Identify Sound

```bash
$ python3 identify_sound.py
=== Available Audio Devices ===
10: BlackHole 2ch

✅ Using: BlackHole 2ch

📚 Loaded 1 learned sounds:
   - teams_notification

🎧 Listening for sounds... (Ctrl+C to stop)

Level: 0.0234 ███                   Peak: 0.0823 ████████
🔔 IDENTIFIED: teams_notification (confidence: 87%)
```

## Next Steps

1. **Learn your sounds**: Record Teams notification, call, etc.
2. **Test identification**: Use `identify_sound.py` to verify
3. **Use in GUI**: Espresso will automatically identify sounds
4. **Customize notifications**: Different alerts for different sounds

## See Also

- [AUDIO_SETUP.md](AUDIO_SETUP.md) - Basic audio monitoring setup
- [SCREEN_MONITORING.md](SCREEN_MONITORING.md) - Visual notification detection
- [README.md](../README.md) - Main project documentation

---

Made with ☕ and Python

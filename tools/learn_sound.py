#!/usr/bin/env python3
"""
Learn a notification sound for later identification
"""
import sounddevice as sd
import numpy as np
import sys
import time
from pathlib import Path

# Add espresso to path
sys.path.insert(0, str(Path(__file__).parent))

from espresso.audio_fingerprint import AudioFingerprint


def main():
    """Learn a sound"""
    if len(sys.argv) < 2:
        print("Usage: python3 learn_sound.py <sound_name>")
        print("")
        print("Example: python3 learn_sound.py teams_notification")
        print("")
        print("This will record audio for 2 seconds and learn the sound pattern.")
        sys.exit(1)

    sound_name = sys.argv[1]

    # Find BlackHole device
    devices = sd.query_devices()
    device_id = None

    print("=== Available Audio Devices ===")
    for i, device in enumerate(devices):
        if device['max_input_channels'] > 0:
            print(f"{i}: {device['name']}")
            if 'blackhole' in device['name'].lower():
                device_id = i

    if device_id is None:
        print("\n⚠️  BlackHole not found, using default input device")
    else:
        print(f"\n✅ Using: {devices[device_id]['name']}")

    print(f"\n🎤 Recording sound '{sound_name}'...")
    print("   Play the notification sound NOW!")
    print("   Recording for 2 seconds...")
    print("")

    # Record
    sample_rate = 44100
    duration = 2.0
    audio_buffer = []

    def callback(indata, frames, time_info, status):
        audio_buffer.append(indata.copy())

    stream = sd.InputStream(
        device=device_id,
        channels=1,
        samplerate=sample_rate,
        blocksize=1024,
        callback=callback
    )

    with stream:
        time.sleep(duration)

    # Concatenate buffer
    audio_data = np.concatenate(audio_buffer, axis=0)

    # Check if we got audio
    rms = np.sqrt(np.mean(audio_data**2))
    print(f"✅ Recording complete! RMS level: {rms:.4f}")

    if rms < 0.001:
        print("⚠️  Warning: Very low audio level detected!")
        print("   Make sure audio is routed through the correct device.")
        response = input("   Continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)

    # Find the actual sound in the buffer (trim silence)
    threshold = rms * 2
    above_threshold = np.abs(audio_data.flatten()) > threshold

    if np.any(above_threshold):
        start_idx = np.argmax(above_threshold)
        end_idx = len(audio_data) - np.argmax(above_threshold[::-1])

        # Add some padding
        padding = int(0.1 * sample_rate)  # 100ms padding
        start_idx = max(0, start_idx - padding)
        end_idx = min(len(audio_data), end_idx + padding)

        audio_data = audio_data[start_idx:end_idx]

        actual_duration = len(audio_data) / sample_rate
        print(f"🔍 Trimmed to active audio: {actual_duration:.3f}s")

    # Learn the sound
    fp = AudioFingerprint()
    fp.learn_sound(sound_name, audio_data.flatten(), sample_rate)

    print("")
    print(f"🎉 Sound '{sound_name}' learned successfully!")
    print(f"   Stored in: {fp.fingerprint_file}")
    print("")
    print("Now audio monitoring will identify this sound automatically!")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Identify notification sounds in real-time
"""
import sounddevice as sd
import numpy as np
import sys
import time
from pathlib import Path
from collections import deque

# Add espresso to path
sys.path.insert(0, str(Path(__file__).parent))

from espresso.audio_fingerprint import AudioFingerprint


def main():
    """Identify sounds in real-time"""
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

    # Load fingerprints
    fp = AudioFingerprint()

    if not fp.fingerprints:
        print("\n⚠️  No learned sounds found!")
        print("   Learn a sound first with: python3 learn_sound.py <name>")
        sys.exit(1)

    print(f"\n📚 Loaded {len(fp.fingerprints)} learned sounds:")
    for name in fp.fingerprints.keys():
        print(f"   - {name}")

    print("\n🎧 Listening for sounds... (Ctrl+C to stop)")
    print("   Play a Teams notification to test identification")
    print("")

    # Audio parameters
    sample_rate = 44100
    block_size = 1024
    buffer_duration = 2.0  # Keep 2 seconds of audio
    buffer_size = int(sample_rate * buffer_duration)

    # Ring buffer for audio
    audio_buffer = deque(maxlen=buffer_size)

    # Detection state
    last_detection_time = 0
    detection_cooldown = 2.0  # Don't re-identify for 2 seconds
    threshold = 0.02

    # Peak tracking
    peak_level = 0.0
    last_peak_time = time.time()

    def audio_callback(indata, frames, time_info, status):
        nonlocal peak_level, last_peak_time, last_detection_time

        if status:
            print(f"Status: {status}")

        # Add to buffer
        for sample in indata:
            audio_buffer.append(sample[0])

        # Calculate RMS
        rms = np.sqrt(np.mean(indata**2))

        # Track peak
        now = time.time()
        if rms > peak_level:
            peak_level = rms
            last_peak_time = now

        # Reset peak after 0.5 seconds
        if now - last_peak_time > 0.5:
            peak_level = 0.0

        # Visual feedback
        detection_level = max(rms, peak_level)
        bar_length = int(detection_level * 100)
        bar = "█" * min(bar_length, 50)

        peak_bar_length = int(peak_level * 100)
        peak_bar = "▓" * min(peak_bar_length, 50)

        print(f"\rLevel: {rms:.4f} {bar:<50} Peak: {peak_level:.4f} {peak_bar:<50}", end='', flush=True)

        # Check for sound above threshold
        if detection_level > threshold and (now - last_detection_time) > detection_cooldown:
            # Wait a bit to capture the full sound
            time.sleep(0.3)

            # Get audio from buffer
            audio_data = np.array(list(audio_buffer))

            if len(audio_data) > sample_rate * 0.1:  # At least 100ms
                # Try to identify
                sound_name, confidence = fp.identify_sound(audio_data, sample_rate, min_confidence=0.6)

                if sound_name:
                    print(f"\n🔔 IDENTIFIED: {sound_name} (confidence: {confidence:.2%})")
                else:
                    print(f"\n❓ Unknown sound (best match confidence: {confidence:.2%})")

                last_detection_time = now

    # Start listening
    try:
        with sd.InputStream(
            device=device_id,
            channels=1,
            samplerate=sample_rate,
            blocksize=block_size,
            callback=audio_callback
        ):
            while True:
                time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n\n✋ Stopped")


if __name__ == "__main__":
    main()

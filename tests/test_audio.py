#!/usr/bin/env python3
"""
Test audio monitoring to see if audio is being captured
"""
import sounddevice as sd
import numpy as np
import time

# Track peak level for detecting short sounds
peak_level = 0.0
last_peak_time = time.time()

def audio_callback(indata, frames, time_info, status):
    """Print audio levels"""
    global peak_level, last_peak_time

    if status:
        print(f"Status: {status}")

    # Calculate RMS level
    rms = np.sqrt(np.mean(indata**2))

    # Track peak
    if rms > peak_level:
        peak_level = rms
        last_peak_time = time.time()

    # Reset peak after 0.5 seconds
    if time.time() - last_peak_time > 0.5:
        peak_level = 0.0

    # Print bar graph (current RMS)
    bar_length = int(rms * 100)
    bar = "█" * min(bar_length, 50)

    # Print peak bar
    peak_bar_length = int(peak_level * 100)
    peak_bar = "▓" * min(peak_bar_length, 50)

    # Detection indicator
    notification_detected = rms > 0.05 or peak_level > 0.05
    indicator = " 🔔 NOTIFICATION!" if notification_detected else ""

    print(f"\rLevel: {rms:.4f} {bar:<50} Peak: {peak_level:.4f} {peak_bar:<50}{indicator}", end='', flush=True)

# List devices
print("=== Available Audio Devices ===")
devices = sd.query_devices()
for i, device in enumerate(devices):
    if device['max_input_channels'] > 0:
        print(f"{i}: {device['name']}")

print("\n")

# Find BlackHole
device_id = None
for i, device in enumerate(devices):
    if 'blackhole' in device['name'].lower():
        device_id = i
        print(f"Using device: {device['name']}")
        break

if device_id is None:
    print("BlackHole not found! Using default input.")

print("\nListening for audio... (Ctrl+C to stop)")
print("Play a Teams notification in Citrix to test")
print()

try:
    with sd.InputStream(
        device=device_id,
        channels=1,
        samplerate=44100,
        blocksize=2048,
        callback=audio_callback
    ):
        while True:
            time.sleep(0.1)
except KeyboardInterrupt:
    print("\n\nStopped")

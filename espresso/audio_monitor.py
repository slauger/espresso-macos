"""
Audio monitoring for detecting notifications and calls
"""
import threading
import time
import numpy as np
from datetime import datetime, timedelta
from typing import Callable, Optional

try:
    import sounddevice as sd
except ImportError:
    sd = None


class AudioMonitor:
    """Monitor system audio for notification sounds and calls"""

    def __init__(
        self,
        device_name: Optional[str] = None,
        sample_rate: int = 44100,
        block_size: int = 1024,  # Reduced from 2048 for better short sound detection
        notification_threshold: float = 0.05,
        call_threshold: float = 0.02,
        call_duration: float = 3.0,
    ):
        """
        Initialize audio monitor

        Args:
            device_name: Name of audio input device (None = default)
            sample_rate: Audio sample rate
            block_size: Size of audio blocks to process (smaller = better short sound detection)
            notification_threshold: RMS threshold for notification detection (0-1)
            call_threshold: RMS threshold for call detection (0-1)
            call_duration: Seconds of sustained audio to detect as call
        """
        if sd is None:
            raise ImportError(
                "sounddevice is not installed. Install with: pip install sounddevice numpy"
            )

        self.device_name = device_name
        self.sample_rate = sample_rate
        self.block_size = block_size
        self.notification_threshold = notification_threshold
        self.call_threshold = call_threshold
        self.call_duration = call_duration

        # State
        self.running = False
        self.monitor_thread = None
        self.stream = None

        # Detection state
        self.last_notification_time = None
        self.call_start_time = None
        self.in_call = False
        self.notification_cooldown = 2.0  # seconds

        # Peak tracking for short sounds
        self.peak_level = 0.0
        self.last_peak_time = None

        # Callbacks
        self.on_notification = None
        self.on_call_start = None
        self.on_call_end = None

    def get_available_devices(self):
        """Get list of available audio input devices"""
        devices = sd.query_devices()
        input_devices = []

        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                input_devices.append({
                    'id': i,
                    'name': device['name'],
                    'channels': device['max_input_channels'],
                    'sample_rate': device['default_samplerate']
                })

        return input_devices

    def find_device_by_name(self, name: str) -> Optional[int]:
        """Find device ID by name (partial match)"""
        devices = self.get_available_devices()
        for device in devices:
            if name.lower() in device['name'].lower():
                return device['id']
        return None

    def calculate_rms(self, audio_data):
        """Calculate RMS (Root Mean Square) of audio data"""
        return np.sqrt(np.mean(audio_data**2))

    def audio_callback(self, indata, frames, time_info, status):
        """Callback for audio stream"""
        if status:
            print(f"Audio status: {status}")

        # Calculate RMS level
        rms = self.calculate_rms(indata)

        # Track peak level for short sound detection
        now = datetime.now()
        if rms > self.peak_level:
            self.peak_level = rms
            self.last_peak_time = now

        # Reset peak after 0.5 seconds
        if self.last_peak_time and (now - self.last_peak_time).total_seconds() > 0.5:
            self.peak_level = 0.0
            self.last_peak_time = None

        # Check for notification (short spike) - use peak level for better detection
        detection_level = max(rms, self.peak_level)
        if detection_level > self.notification_threshold:
            # Check cooldown to avoid duplicate notifications
            if (self.last_notification_time is None or
                (now - self.last_notification_time).total_seconds() > self.notification_cooldown):

                self.last_notification_time = now

                # Trigger notification callback
                if self.on_notification and not self.in_call:
                    threading.Thread(
                        target=self.on_notification,
                        args=(detection_level,),
                        daemon=True
                    ).start()

        # Check for call (sustained audio)
        if rms > self.call_threshold:
            now = datetime.now()

            if self.call_start_time is None:
                self.call_start_time = now
            else:
                # Check if audio has been sustained long enough
                duration = (now - self.call_start_time).total_seconds()

                if duration >= self.call_duration and not self.in_call:
                    self.in_call = True
                    if self.on_call_start:
                        threading.Thread(
                            target=self.on_call_start,
                            daemon=True
                        ).start()
        else:
            # Audio level dropped
            if self.in_call:
                self.in_call = False
                if self.on_call_end:
                    threading.Thread(
                        target=self.on_call_end,
                        daemon=True
                    ).start()

            self.call_start_time = None

    def start(self):
        """Start audio monitoring"""
        if self.running:
            return

        self.running = True

        # Find device
        device_id = None
        if self.device_name:
            device_id = self.find_device_by_name(self.device_name)
            if device_id is None:
                raise ValueError(f"Audio device not found: {self.device_name}")

        # Start audio stream
        try:
            self.stream = sd.InputStream(
                device=device_id,
                channels=1,
                samplerate=self.sample_rate,
                blocksize=self.block_size,
                callback=self.audio_callback
            )
            self.stream.start()
        except Exception as e:
            self.running = False
            raise RuntimeError(f"Failed to start audio monitoring: {e}")

    def stop(self):
        """Stop audio monitoring"""
        if not self.running:
            return

        self.running = False

        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

    def set_notification_callback(self, callback: Callable[[float], None]):
        """Set callback for notification detection"""
        self.on_notification = callback

    def set_call_callbacks(
        self,
        on_start: Callable[[], None],
        on_end: Callable[[], None]
    ):
        """Set callbacks for call detection"""
        self.on_call_start = on_start
        self.on_call_end = on_end


def list_audio_devices():
    """Print all available audio input devices"""
    if sd is None:
        print("sounddevice is not installed")
        print("Install with: pip install sounddevice numpy")
        return

    print("=== Available Audio Input Devices ===\n")

    devices = sd.query_devices()
    input_devices = []

    for i, device in enumerate(devices):
        if device['max_input_channels'] > 0:
            print(f"{i}. {device['name']}")
            print(f"   Channels: {device['max_input_channels']}")
            print(f"   Sample Rate: {device['default_samplerate']}")
            print()

    print("\nTip: Use 'BlackHole' or similar virtual audio device")
    print("     to capture system audio on macOS")
    print("\nInstall BlackHole: brew install blackhole-2ch")

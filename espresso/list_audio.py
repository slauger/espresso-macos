"""
Utility CLI to list audio devices
"""
from .audio_monitor import list_audio_devices


def main():
    """Main entry point for list-audio command"""
    list_audio_devices()


if __name__ == "__main__":
    main()

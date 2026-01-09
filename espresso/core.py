"""
Core functionality for espresso operations
"""
import subprocess
from datetime import datetime
from typing import Optional, Callable


class EspressoCore:
    """Core espresso functionality shared between CLI and GUI"""

    def __init__(self, app_name: str, interval: int):
        """
        Initialize keepalive core

        Args:
            app_name: Name of application to monitor
            interval: Seconds between keepalive actions
        """
        self.app_name = app_name
        self.interval = interval
        self.consecutive_errors = 0
        self.max_errors = 5

    def is_app_running(self) -> bool:
        """Check if target app is running and has windows"""
        script = f'''
        tell application "System Events"
            set appRunning to exists (process "{self.app_name}")
            if appRunning then
                try
                    set winCount to count of windows of process "{self.app_name}"
                    return winCount > 0
                on error
                    return false
                end try
            else
                return false
            end if
        end tell
        '''

        try:
            result = subprocess.run(['osascript', '-e', script],
                                  capture_output=True, text=True, timeout=5)
            return result.stdout.strip() == "true"
        except Exception:
            return False

    def perform_keepalive_action(self) -> bool:
        """
        Perform keepalive action (focus window, send key, restore focus)

        Returns:
            True if action successful, False otherwise
        """
        # Focus Citrix, send key, return to previous app
        return self._send_key_with_focus()

    def _send_key_with_focus(self) -> bool:
        """Focus Citrix window, send key, return to previous app"""
        try:
            script = f'''
            tell application "System Events"
                -- Remember current frontmost app
                set currentApp to name of first application process whose frontmost is true

                -- Focus Citrix Viewer
                tell process "{self.app_name}"
                    set frontmost to true
                end tell

                -- Wait briefly for focus
                delay 0.2

                -- Send Control key (key code 59)
                key code 59

                -- Wait briefly
                delay 0.1

                -- Return to previous app
                tell process currentApp
                    set frontmost to true
                end tell
            end tell
            '''

            result = subprocess.run(['osascript', '-e', script],
                                   capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except Exception:
            return False

    @staticmethod
    def log(message: str, callback: Optional[Callable[[str], None]] = None):
        """
        Log a message with timestamp

        Args:
            message: Message to log
            callback: Optional callback function for custom logging
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] {message}"

        if callback:
            callback(log_line)
        else:
            print(log_line)

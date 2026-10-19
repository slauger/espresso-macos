"""
Core functionality for espresso operations
"""
import subprocess
from datetime import datetime
from typing import Callable, List, Optional


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

    def _get_window_pids(self) -> List[int]:
        """Return PIDs of all target app processes that have at least one window"""
        script = f'''
        tell application "System Events"
            set pids to {{}}
            repeat with p in (every process whose name is "{self.app_name}")
                try
                    if (count of windows of p) > 0 then set end of pids to unix id of p
                end try
            end repeat
            set AppleScript's text item delimiters to ","
            return pids as text
        end tell
        '''

        try:
            result = subprocess.run(['osascript', '-e', script],
                                  capture_output=True, text=True, timeout=5)
            return [int(pid) for pid in result.stdout.strip().split(',') if pid.strip()]
        except Exception:
            return []

    def is_app_running(self) -> bool:
        """Check if target app is running and has windows"""
        return len(self._get_window_pids()) > 0

    def perform_keepalive_action(self) -> bool:
        """
        Perform keepalive action (focus window, send key, restore focus)

        Returns:
            True if action successful, False otherwise
        """
        # Multiple sessions run as separate processes with the same name,
        # so every one of them needs its own keepalive
        pids = self._get_window_pids()
        if not pids:
            return False
        return all([self._send_key_with_focus(pid) for pid in pids])

    def _send_key_with_focus(self, pid: int) -> bool:
        """Focus Citrix window of the given process, send key, return to previous app"""
        try:
            script = f'''
            tell application "System Events"
                -- Remember current frontmost app
                set currentApp to first application process whose frontmost is true

                -- Focus Citrix Viewer session
                tell (first process whose unix id is {pid})
                    set frontmost to true
                end tell

                -- Wait briefly for focus
                delay 0.2

                -- Send Control key (key code 59)
                key code 59

                -- Wait briefly
                delay 0.1

                -- Return to previous app
                set frontmost of currentApp to true
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

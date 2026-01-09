"""
GUI version of espresso with menu bar icon
"""
import argparse
import json
import subprocess
import sys
import threading
import time
import os
import logging
from datetime import datetime
from pathlib import Path

# Setup logging (level will be configured in main())
logging.basicConfig(
    level=logging.INFO,  # Default level
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.expanduser('~/.espresso/gui.log')),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

try:
    import rumps
except ImportError:
    print("Error: rumps is not installed")
    print("Install it with: pip3 install rumps")
    sys.exit(1)

from .core import EspressoCore

# Optional audio monitoring
try:
    from .audio_monitor import AudioMonitor
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False

# Optional screen monitoring
try:
    from .screen_monitor import ScreenMonitor
    SCREEN_AVAILABLE = True
except ImportError:
    SCREEN_AVAILABLE = False


def get_icon_path():
    """Get path to icon file"""
    # Try different locations
    possible_paths = [
        # Installed package
        Path(__file__).parent.parent / "icons" / "icon-22.png",
        # Development
        Path.cwd() / "icons" / "icon-22.png",
        # Fallback
        Path.home() / "git" / "citrix-keepalive" / "icons" / "icon-22.png",
    ]

    for path in possible_paths:
        if path.exists():
            return str(path)

    return None


class EspressoApp(rumps.App):
    """Menu bar app for espresso functionality"""

    def __init__(
        self,
        app_name="Citrix Viewer",
        interval=60,
        audio_device=None,
        notification_threshold=0.05,
        call_threshold=0.02,
        call_duration=3.0,
        screen_config=None
    ):
        # Get icon path
        icon_path = get_icon_path()

        super(EspressoApp, self).__init__(
            "Espresso",
            icon=icon_path,
            quit_button=None,
            template=True  # Use template mode for proper macOS dark mode support
        )

        # Create core
        self.core = EspressoCore(app_name=app_name, interval=interval)

        # State
        self.running = False
        self.keepalive_thread = None
        self.last_action_time = None
        self.last_status = "Idle"

        # Audio monitoring
        self.audio_monitor = None
        self.audio_enabled = False
        self.audio_device = audio_device

        if AUDIO_AVAILABLE:
            try:
                self.audio_monitor = AudioMonitor(
                    device_name=audio_device,
                    notification_threshold=notification_threshold,
                    call_threshold=call_threshold,
                    call_duration=call_duration
                )
                self.audio_monitor.set_notification_callback(self.on_audio_notification)
                self.audio_monitor.set_call_callbacks(
                    on_start=self.on_call_start,
                    on_end=self.on_call_end
                )
            except Exception as e:
                print(f"Audio monitoring not available: {e}")
                self.audio_monitor = None

        # Screen monitoring
        self.screen_monitor = None
        self.screen_enabled = False
        self.screen_config = screen_config or {}

        # Create screen monitor if available (independent of enabled flag)
        # The 'enabled' flag is only used for autostart
        if SCREEN_AVAILABLE and self.screen_config:
            try:
                self.screen_monitor = ScreenMonitor(
                    window_name=app_name,
                    scan_interval=self.screen_config.get('scan_interval', 2.0),
                    detection_method=self.screen_config.get('detection_method', 'color'),
                    notification_color=self.screen_config.get('teams_notification_color', '#464775'),
                    color_tolerance=self.screen_config.get('color_tolerance', 30),
                    min_pixels=self.screen_config.get('min_pixels', 1000),
                    debug_screenshots=self.screen_config.get('debug_screenshots', False)
                )
            except Exception as e:
                print(f"Screen monitoring not available: {e}")
                self.screen_monitor = None

        # Create menu items (keep references for updates)
        self.status_item = rumps.MenuItem("Status: Stopped", callback=None)
        self.last_action_item = rumps.MenuItem("Last action: Never", callback=None)
        self.keepalive_item = rumps.MenuItem("▶ Start Keepalive", callback=self.toggle_keepalive)
        self.audio_item = None
        self.screen_item = None

        # Build menu
        menu_items = [
            rumps.MenuItem(f"Target: {self.core.app_name}", callback=None),
            rumps.MenuItem(f"Interval: {self.core.interval}s", callback=None),
            rumps.separator,
            self.keepalive_item,
            rumps.separator,
            self.status_item,
            self.last_action_item,
        ]

        # Add audio monitoring menu items if available
        if self.audio_monitor:
            self.audio_item = rumps.MenuItem("▶ Enable Audio Monitor", callback=self.toggle_audio_monitoring)
            menu_items.extend([
                rumps.separator,
                self.audio_item,
            ])

        # Add screen monitoring menu items if available
        if self.screen_monitor:
            self.screen_item = rumps.MenuItem("▶ Enable Screen Monitor", callback=self.toggle_screen_monitoring)
            menu_items.extend([
                rumps.separator,
                self.screen_item,
            ])

        menu_items.extend([
            rumps.separator,
            rumps.MenuItem("Quit", callback=rumps.quit_application)
        ])

        self.menu = menu_items

        # Store original icon
        self.icon_path = icon_path

    def update_icon(self, status):
        """Update menu bar icon - for now just keep the espresso icon"""
        # With a real icon, we keep it consistent
        # Could add colored overlays or badges in the future
        pass

    def update_status(self, status):
        """Update status menu item"""
        self.last_status = status
        self.status_item.title = f"Status: {status}"

    def update_last_action(self):
        """Update last action time"""
        self.last_action_time = datetime.now()
        time_str = self.last_action_time.strftime("%H:%M:%S")
        self.last_action_item.title = f"Last action: {time_str}"

    def keepalive_loop(self):
        """Main keepalive loop running in background thread"""
        while self.running:
            try:
                if self.core.is_app_running():
                    self.update_icon("🟢")
                    self.update_status(f"{self.core.app_name} active")

                    if self.core.perform_keepalive_action():
                        self.core.consecutive_errors = 0
                        self.update_last_action()
                    else:
                        self.core.consecutive_errors += 1
                        self.update_status(
                            f"Error ({self.core.consecutive_errors}/{self.core.max_errors})"
                        )

                    if self.core.consecutive_errors >= self.core.max_errors:
                        self.update_status("Too many errors - stopped")
                        self.update_icon("⚠️")
                        self.running = False
                        break
                else:
                    self.update_icon("🟡")
                    self.update_status(f"{self.core.app_name} not running")
                    self.core.consecutive_errors = 0

                # Wait for next interval
                time.sleep(self.core.interval)

            except Exception as e:
                self.core.consecutive_errors += 1
                self.update_status(f"Error: {str(e)[:30]}")
                if self.core.consecutive_errors >= self.core.max_errors:
                    self.running = False
                    break
                time.sleep(self.core.interval)

        # Stopped
        if not self.running:
            self.update_icon("⏸")
            if self.core.consecutive_errors < self.core.max_errors:
                self.update_status("Stopped")

    def toggle_keepalive(self, _):
        """Toggle keepalive monitoring on/off"""
        if self.running:
            self.stop_keepalive()
        else:
            self.start_keepalive()

    def start_keepalive(self):
        """Start keepalive monitoring"""
        if not self.running:
            self.running = True
            self.core.consecutive_errors = 0
            self.update_status("Starting...")
            self.update_icon("🟢")

            # Start background thread
            self.keepalive_thread = threading.Thread(target=self.keepalive_loop, daemon=True)
            self.keepalive_thread.start()

            # Update menu item
            self.keepalive_item.title = "⏸ Stop Keepalive"

            rumps.notification(
                "Espresso Started",
                f"Monitoring {self.core.app_name}",
                f"Interval: {self.core.interval}s"
            )

    def stop_keepalive(self):
        """Stop keepalive monitoring"""
        if self.running:
            self.running = False
            self.update_status("Stopped")
            self.update_icon("⏸")

            # Update menu item
            self.keepalive_item.title = "▶ Start Keepalive"

            rumps.notification(
                "Espresso Stopped",
                "Monitoring paused",
                ""
            )

    def toggle_audio_monitoring(self, sender):
        """Toggle audio monitoring on/off"""
        if not self.audio_monitor:
            return

        if self.audio_enabled:
            # Disable audio monitoring
            self.audio_monitor.stop()
            self.audio_enabled = False
            if self.audio_item:
                self.audio_item.title = "▶ Enable Audio Monitor"

            rumps.notification(
                "Audio Monitor Disabled",
                "No longer monitoring for calls/notifications",
                ""
            )
        else:
            # Enable audio monitoring
            try:
                self.audio_monitor.start()
                self.audio_enabled = True
                if self.audio_item:
                    self.audio_item.title = "⏸ Disable Audio Monitor"

                rumps.notification(
                    "Audio Monitor Enabled",
                    "Monitoring for Teams calls and notifications",
                    ""
                )
            except Exception as e:
                rumps.notification(
                    "Audio Monitor Error",
                    f"Failed to start: {str(e)[:50]}",
                    ""
                )

    def is_app_in_foreground(self) -> bool:
        """Check if target app is in foreground (frontmost)"""
        script = f'''
        tell application "System Events"
            set frontApp to name of first application process whose frontmost is true
        end tell
        return frontApp
        '''

        try:
            result = subprocess.run(['osascript', '-e', script],
                                  capture_output=True, text=True, timeout=2)
            frontmost_app = result.stdout.strip()
            return frontmost_app == self.core.app_name
        except Exception:
            return False

    def on_audio_notification(self, level):
        """Callback for audio notification detection"""
        # Only notify if app is NOT in foreground
        if self.is_app_in_foreground():
            return  # User is already looking at the app, no need to notify

        rumps.notification(
            "🔔 Teams Notification",
            f"Notification detected in {self.core.app_name}",
            f"Audio level: {level:.3f}",
            sound=True
        )

    def on_call_start(self):
        """Callback for call start detection"""
        # Only notify if app is NOT in foreground
        if self.is_app_in_foreground():
            return  # User is already in the app, can see the call

        rumps.notification(
            "📞 Incoming Call",
            f"Call detected in {self.core.app_name}",
            "Audio activity detected - possible incoming call",
            sound=True
        )

    def on_call_end(self):
        """Callback for call end detection"""
        # Always notify call end (even if in foreground)
        # This is useful info even when actively using the app
        rumps.notification(
            "📞 Call Ended",
            f"Call ended in {self.core.app_name}",
            "Audio activity stopped",
            sound=False
        )

    def toggle_screen_monitoring(self, sender):
        """Toggle screen monitoring on/off"""
        logger.debug(f"toggle_screen_monitoring called (current state: enabled={self.screen_enabled})")

        if not self.screen_monitor:
            logger.error("No screen monitor available!")
            return

        if self.screen_enabled:
            # Disable screen monitoring
            logger.info("Disabling screen monitor...")
            self.screen_monitor.stop()
            self.screen_enabled = False
            if self.screen_item:
                try:
                    self.screen_item.set_title("▶ Enable Screen Monitor")
                except:
                    self.screen_item.title = "▶ Enable Screen Monitor"

            rumps.notification(
                "Screen Monitor Disabled",
                "No longer monitoring for visual notifications",
                ""
            )
        else:
            # Enable screen monitoring
            logger.info("Enabling screen monitor...")
            logger.debug(f"screen_monitor object: {self.screen_monitor}")
            logger.debug(f"screen_item object: {self.screen_item}")
            try:
                # Start in background thread
                logger.debug(f"Creating thread with callback: {self.on_screen_notification}")
                screen_thread = threading.Thread(
                    target=self.screen_monitor.start,
                    args=(self.on_screen_notification,),
                    daemon=True
                )
                screen_thread.start()
                logger.debug(f"Thread started: {screen_thread}")

                self.screen_enabled = True

                if self.screen_item:
                    try:
                        self.screen_item.set_title("⏸ Disable Screen Monitor")
                    except:
                        self.screen_item.title = "⏸ Disable Screen Monitor"

                rumps.notification(
                    "Screen Monitor Enabled",
                    "Monitoring for Teams visual notifications",
                    f"Scanning every {self.screen_monitor.scan_interval}s"
                )
            except Exception as e:
                logger.error(f"Error starting screen monitor: {e}", exc_info=True)
                rumps.notification(
                    "Screen Monitor Error",
                    f"Failed to start: {str(e)[:50]}",
                    ""
                )

    def on_screen_notification(self, source: str, details: dict):
        """Callback for screen notification detection"""
        logger.info(f"on_screen_notification called: source={source}, details={details}")

        # Only notify if app is NOT in foreground
        in_foreground = self.is_app_in_foreground()
        logger.info(f"is_app_in_foreground: {in_foreground}")

        if in_foreground:
            logger.info(f"Skipping notification - {self.core.app_name} is in foreground")
            return  # User is already looking at the app, no need to notify

        logger.info("Sending macOS notification...")

        # Use longer notification text to keep it visible longer
        timestamp = datetime.now().strftime('%H:%M:%S')

        # Get notification text from OCR if available
        notification_text = details.get('notification_text', '')

        if notification_text:
            # Show OCR text in notification
            message = f"💬 {notification_text}\n\n⏰ Detected at {timestamp}"
            logger.info(f"Notification with OCR text: {notification_text}")
        else:
            # Fallback message without OCR
            message = f"A Teams chat notification appeared at {timestamp}. Click to switch to Citrix Viewer."

        rumps.notification(
            title="🔔 Teams Notification!",
            subtitle=f"New message in {self.core.app_name}",
            message=message,
            sound=True
        )
        logger.info(f"Notification sent at {timestamp}")


def load_config(config_file: str = None) -> dict:
    """Load configuration from JSON file"""
    # Try user-specified config first
    if config_file:
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Warning: Could not load config from {config_file}: {e}")
            return {}

    # Try default config location
    default_config = Path.home() / ".espresso" / "config.json"
    if default_config.exists():
        try:
            with open(default_config, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            print(f"Warning: Could not parse {default_config}: {e}")

    return {}


def main():
    """Main entry point for GUI"""
    parser = argparse.ArgumentParser(
        description='Espresso GUI - Keep your apps awake',
    )

    parser.add_argument(
        '--app',
        type=str,
        default='Citrix Viewer',
        help='Name of the application to monitor (default: Citrix Viewer)'
    )

    parser.add_argument(
        '--interval',
        type=int,
        default=60,
        help='Interval in seconds between actions (default: 60)'
    )

    parser.add_argument(
        '--config',
        type=str,
        help='Path to JSON config file'
    )

    parser.add_argument(
        '--autostart',
        action='store_true',
        help='Start monitoring automatically on launch'
    )

    parser.add_argument(
        '--autostart-audio',
        action='store_true',
        help='Start audio monitoring automatically on launch'
    )

    parser.add_argument(
        '--autostart-screen',
        action='store_true',
        help='Start screen monitoring automatically on launch'
    )

    parser.add_argument(
        '--audio-device',
        type=str,
        help='Audio input device name for monitoring (e.g., "BlackHole")'
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )

    args = parser.parse_args()

    # Configure logging level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.info("Debug logging enabled")

    # Load config (from --config arg or default ~/.espresso/config.json)
    config = load_config(args.config)

    # Merge config with CLI args (CLI args have priority)
    app_name = args.app if args.app != 'Citrix Viewer' else config.get('app_name', args.app)
    interval = config.get('interval_seconds', args.interval)
    audio_device = args.audio_device if args.audio_device else config.get('audio_device')
    notification_threshold = config.get('notification_threshold', 0.05)
    call_threshold = config.get('call_threshold', 0.02)
    call_duration = config.get('call_duration', 3.0)
    screen_config = config.get('screen_monitoring', {})
    autostart = args.autostart or config.get('autostart', False)
    autostart_audio = args.autostart_audio or config.get('autostart_audio', False)
    # Check for autostart_screen in both root level and inside screen_monitoring config
    autostart_screen = (args.autostart_screen or
                       config.get('autostart_screen', False) or
                       screen_config.get('enabled', False))

    # Create and run app
    app = EspressoApp(
        app_name=app_name,
        interval=interval,
        audio_device=audio_device,
        notification_threshold=notification_threshold,
        call_threshold=call_threshold,
        call_duration=call_duration,
        screen_config=screen_config
    )

    # Autostart keepalive if requested
    if autostart:
        logger.info("Autostarting keepalive...")
        app.start_keepalive()

    # Autostart audio monitoring if requested
    if autostart_audio:
        logger.info(f"Autostart audio requested, audio_monitor available: {app.audio_monitor is not None}")
        if app.audio_monitor is not None and app.audio_item is not None:
            logger.info("Starting audio monitor via autostart...")
            app.toggle_audio_monitoring(app.audio_item)
        elif app.audio_monitor is None:
            logger.warning("Audio monitor not available")
        else:
            logger.warning("Audio menu item not created")

    # Autostart screen monitoring if requested
    if autostart_screen:
        logger.debug(f"Autostart screen requested, screen_monitor available: {app.screen_monitor is not None}")
        if app.screen_monitor is not None and app.screen_item is not None:
            logger.info("Autostarting screen monitor...")
            app.toggle_screen_monitoring(app.screen_item)
        elif app.screen_monitor is None:
            logger.warning("Screen monitor not available for autostart")
        else:
            logger.warning("Screen menu item not created")

    # Update menu items after a short delay to ensure rumps is ready
    def update_menu_titles():
        """Update menu item titles to reflect autostart state"""
        logger.debug("Updating menu item titles after autostart...")

        if app.screen_enabled and app.screen_item is not None:
            app.screen_item.title = "⏸ Disable Screen Monitor"
            logger.debug("Set screen monitor item to active state")

        if app.audio_enabled and app.audio_item is not None:
            app.audio_item.title = "⏸ Disable Audio Monitor"
            logger.debug("Set audio monitor item to active state")

        if app.running and app.keepalive_item is not None:
            app.keepalive_item.title = "⏸ Stop Keepalive"
            logger.debug("Set keepalive item to active state")

    # Schedule menu update using threading.Timer (to sync menu state with autostart)
    import threading
    timer = threading.Timer(0.5, update_menu_titles)
    timer.daemon = True
    timer.start()

    app.run()


if __name__ == "__main__":
    main()

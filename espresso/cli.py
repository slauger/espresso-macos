"""
CLI version of espresso
"""
import argparse
import json
import sys
import time
from pathlib import Path

from .core import EspressoCore


def load_config(config_file: str = None) -> dict:
    """Load configuration from JSON file"""
    # Try user-specified config first
    if config_file:
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Config file not found: {config_file}")
            return {}
        except json.JSONDecodeError as e:
            print(f"Error parsing config file: {e}")
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


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Espresso - Keep your apps awake',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Use with Citrix Viewer (default)
  %(prog)s

  # Custom app with 2 minute interval
  %(prog)s --app "Microsoft Teams" --interval 120

  # Use config file
  %(prog)s --config config.json

  # Custom settings
  %(prog)s --app "Slack" --interval 300
        '''
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
        help='Interval in seconds between keepalive actions (default: 60)'
    )

    parser.add_argument(
        '--config',
        type=str,
        help='Path to JSON config file (overrides other arguments)'
    )

    return parser.parse_args()


def run_keepalive(core: EspressoCore):
    """Main keepalive loop"""
    EspressoCore.log(f"Espresso started")
    EspressoCore.log(f"  Target app: {core.app_name}")
    EspressoCore.log(f"  Interval: {core.interval} seconds")
    EspressoCore.log(f"Press Ctrl+C to stop")

    try:
        while True:
            try:
                if core.is_app_running():
                    EspressoCore.log(f"{core.app_name} is running - performing keepalive action")

                    if core.perform_keepalive_action():
                        EspressoCore.log("Action performed successfully")
                        core.consecutive_errors = 0
                    else:
                        core.consecutive_errors += 1
                        EspressoCore.log(
                            f"Action failed (error {core.consecutive_errors}/{core.max_errors})"
                        )
                else:
                    EspressoCore.log(f"{core.app_name} is not running - skipping")
                    core.consecutive_errors = 0

                # Stop if too many consecutive errors
                if core.consecutive_errors >= core.max_errors:
                    EspressoCore.log(f"Too many consecutive errors ({core.max_errors}). Stopping.")
                    EspressoCore.log("You may need to grant Accessibility permissions:")
                    EspressoCore.log("System Settings > Privacy & Security > Accessibility")
                    break

                # Wait for next interval
                time.sleep(core.interval)

            except KeyboardInterrupt:
                raise
            except Exception as e:
                core.consecutive_errors += 1
                EspressoCore.log(f"Error in main loop: {e}")
                if core.consecutive_errors >= core.max_errors:
                    raise
                time.sleep(core.interval)

    except KeyboardInterrupt:
        EspressoCore.log(f"\nStopping Espresso (Ctrl+C pressed)")
        sys.exit(0)


def main():
    """Main entry point for CLI"""
    args = parse_args()

    # Load config (from --config arg or default ~/.espresso/config.json)
    config = load_config(args.config)

    # Merge config with CLI args (CLI args have priority)
    app_name = args.app if args.app != 'Citrix Viewer' else config.get('app_name', args.app)
    interval = config.get('interval_seconds', args.interval)

    # Validate parameters
    if interval < 1:
        print("Error: Interval must be at least 1 second")
        sys.exit(1)

    # Create core and run
    core = EspressoCore(app_name=app_name, interval=interval)
    run_keepalive(core)


if __name__ == "__main__":
    main()

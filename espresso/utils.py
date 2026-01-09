"""
Utility functions for app discovery and window management
"""
import subprocess
from typing import List, Tuple


def get_running_apps() -> List[str]:
    """Get list of running applications"""
    script = '''
    tell application "System Events"
        set appList to name of every process whose background only is false
    end tell
    return appList
    '''

    result = subprocess.run(['osascript', '-e', script],
                          capture_output=True, text=True)
    apps = result.stdout.strip().split(', ')
    return apps


def get_active_app() -> str:
    """Get currently active application"""
    script = '''
    tell application "System Events"
        set frontApp to name of first application process whose frontmost is true
    end tell
    return frontApp
    '''

    result = subprocess.run(['osascript', '-e', script],
                          capture_output=True, text=True)
    return result.stdout.strip()


def get_window_info(app_name: str) -> str:
    """Get window information for a specific app"""
    script = f'''
    tell application "System Events"
        tell process "{app_name}"
            try
                set winCount to count of windows
                set winInfo to {{}}
                repeat with i from 1 to winCount
                    set winName to name of window i
                    set winPos to position of window i
                    set winSize to size of window i
                    set end of winInfo to {{winName, winPos, winSize}}
                end repeat
                return winInfo
            on error
                return {{}}
            end try
        end tell
    end tell
    '''

    result = subprocess.run(['osascript', '-e', script],
                          capture_output=True, text=True)
    return result.stdout.strip()


def find_citrix_apps() -> List[Tuple[str, str]]:
    """
    Find Citrix-related applications

    Returns:
        List of (app_name, window_info) tuples
    """
    apps = get_running_apps()
    citrix_apps = []

    for app in apps:
        if any(keyword in app.lower() for keyword in ['citrix', 'receiver', 'workspace']):
            windows = get_window_info(app)
            citrix_apps.append((app, windows))

    return citrix_apps


def list_all_apps():
    """Print all running apps (useful for finding app names)"""
    print("=== Currently Active App ===")
    active = get_active_app()
    print(f"Active: {active}\n")

    print("=== All Running Apps ===")
    apps = get_running_apps()
    for i, app in enumerate(apps, 1):
        print(f"{i}. {app}")

    print("\n=== Citrix Related Apps ===")
    citrix_apps = find_citrix_apps()

    if citrix_apps:
        for app, windows in citrix_apps:
            print(f"\nFound: {app}")
            print(f"Windows: {windows}")
    else:
        print("No Citrix apps currently running")
        print("\nTip: Start Citrix Viewer/Receiver and run this command again")

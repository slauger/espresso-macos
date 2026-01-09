#!/usr/bin/env python3
"""
Wrapper script for PyInstaller to launch espresso-gui
This avoids relative import issues when running as a frozen app
"""
from espresso.gui import main

if __name__ == '__main__':
    main()

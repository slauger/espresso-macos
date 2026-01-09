"""
Utility CLI to list running applications
"""
from .utils import list_all_apps


def main():
    """Main entry point for list-apps command"""
    list_all_apps()


if __name__ == "__main__":
    main()

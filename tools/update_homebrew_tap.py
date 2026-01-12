#!/usr/bin/env python3
"""
Update Homebrew tap with latest release information.

This script:
1. Fetches the latest release from espresso-macos
2. Downloads the ZIP file
3. Calculates SHA256 checksum
4. Updates the Cask file in homebrew-tap repository
5. Optionally commits and pushes the changes
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.request import urlretrieve


def run_command(cmd, capture=True, check=True):
    """Run a shell command and optionally capture output."""
    if capture:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            check=check
        )
        return result.stdout.strip()
    else:
        subprocess.run(cmd, shell=True, check=check)
        return None


def get_latest_release():
    """Get latest release info from GitHub."""
    print("📡 Fetching latest release info...")

    try:
        # Try gh CLI first
        output = run_command(
            'gh release view --repo slauger/espresso-macos --json tagName,url',
            check=False
        )

        if output:
            data = json.loads(output)
            tag = data['tagName']
            version = tag.lstrip('v')
            url = data['url']
            print(f"✅ Found release: {tag} ({url})")
            return version, tag

    except Exception as e:
        print(f"⚠️  gh CLI failed: {e}")

    # Fallback: try to parse from git tags
    print("🔍 Trying to get version from git tags...")
    try:
        tags = run_command('git tag --list "v*" --sort=-version:refname')
        if tags:
            latest_tag = tags.split('\n')[0]
            version = latest_tag.lstrip('v')
            print(f"✅ Found tag: {latest_tag}")
            return version, latest_tag
    except Exception as e:
        print(f"❌ Failed to get version: {e}")
        sys.exit(1)

    print("❌ Could not determine latest version")
    sys.exit(1)


def download_zip(version):
    """Download the ZIP file for the given version."""
    url = f"https://github.com/slauger/espresso-macos/releases/download/v{version}/Espresso-{version}-macOS.zip"

    print(f"⬇️  Downloading {url}...")

    # Create temp file
    temp_dir = tempfile.gettempdir()
    zip_path = os.path.join(temp_dir, f"espresso-{version}.zip")

    try:
        urlretrieve(url, zip_path)
        print(f"✅ Downloaded to {zip_path}")
        return zip_path
    except Exception as e:
        print(f"❌ Download failed: {e}")
        print(f"   Make sure the release exists: {url}")
        sys.exit(1)


def calculate_sha256(file_path):
    """Calculate SHA256 checksum of a file."""
    print(f"🔐 Calculating SHA256...")

    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)

    checksum = sha256_hash.hexdigest()
    print(f"✅ SHA256: {checksum}")
    return checksum


def update_cask_file(tap_path, version, sha256):
    """Update the Cask file with new version and SHA256."""
    cask_file = tap_path / "Casks" / "espresso.rb"

    if not cask_file.exists():
        print(f"❌ Cask file not found: {cask_file}")
        sys.exit(1)

    print(f"📝 Updating {cask_file}...")

    # Read current content
    content = cask_file.read_text()

    # Update version
    content = re.sub(
        r'version\s+"[^"]+"',
        f'version "{version}"',
        content
    )

    # Update SHA256
    content = re.sub(
        r'sha256\s+"[^"]+"',
        f'sha256 "{sha256}"',
        content
    )

    # Write back
    cask_file.write_text(content)

    print("✅ Cask file updated")

    # Show diff
    print("\n📋 Changes:")
    try:
        diff = run_command(f'cd {tap_path} && git diff Casks/espresso.rb', check=False)
        if diff:
            print(diff)
        else:
            print("  No changes (version/SHA256 already up to date)")
    except:
        pass


def commit_and_push(tap_path, version, dry_run=False):
    """Commit and push changes to the tap repository."""
    os.chdir(tap_path)

    # Check if there are changes
    status = run_command('git status --porcelain', check=False)
    if not status:
        print("✅ No changes to commit")
        return

    commit_message = f"chore: update espresso to {version}"

    if dry_run:
        print(f"\n🔍 DRY RUN - Would commit: '{commit_message}'")
        print("   Run without --dry-run to actually commit and push")
        return

    print(f"\n💾 Committing changes...")
    run_command('git add Casks/espresso.rb', capture=False)
    run_command(f'git commit -m "{commit_message}"', capture=False)

    print(f"🚀 Pushing to remote...")
    run_command('git push', capture=False)

    print("✅ Changes committed and pushed")


def main():
    parser = argparse.ArgumentParser(
        description='Update Homebrew tap with latest espresso release'
    )
    parser.add_argument(
        '--tap-path',
        type=Path,
        help='Path to homebrew-tap repository (default: ../homebrew-tap)',
        default=None
    )
    parser.add_argument(
        '--version',
        help='Specific version to use (default: auto-detect latest)',
        default=None
    )
    parser.add_argument(
        '--commit',
        action='store_true',
        help='Commit and push changes (default: just update locally)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )

    args = parser.parse_args()

    print("☕ Homebrew Tap Updater\n")

    # Determine tap path
    if args.tap_path:
        tap_path = args.tap_path.resolve()
    else:
        # Try to find it relative to this script
        script_dir = Path(__file__).parent.parent
        tap_path = script_dir.parent / "homebrew-tap"

    if not tap_path.exists():
        print(f"❌ Tap repository not found: {tap_path}")
        print(f"\n💡 Clone it first:")
        print(f"   cd {tap_path.parent}")
        print(f"   gh repo clone slauger/homebrew-tap")
        sys.exit(1)

    print(f"📂 Tap path: {tap_path}\n")

    # Get version
    if args.version:
        version = args.version.lstrip('v')
        tag = f"v{version}"
        print(f"📌 Using specified version: {version}")
    else:
        version, tag = get_latest_release()

    print()

    # Download ZIP
    zip_path = download_zip(version)

    # Calculate SHA256
    sha256 = calculate_sha256(zip_path)

    print()

    # Update Cask file
    if not args.dry_run:
        update_cask_file(tap_path, version, sha256)
    else:
        print(f"🔍 DRY RUN - Would update Cask file with:")
        print(f"   version: {version}")
        print(f"   sha256:  {sha256}")

    # Commit and push if requested
    if args.commit:
        print()
        commit_and_push(tap_path, version, dry_run=args.dry_run)
    else:
        print(f"\n💡 To commit and push, run with --commit flag")

    # Cleanup
    try:
        os.remove(zip_path)
    except:
        pass

    print("\n✅ Done!")


if __name__ == '__main__':
    main()

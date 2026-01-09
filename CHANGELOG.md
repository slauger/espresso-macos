# CHANGELOG

## v0.0.1 (2026-01-09)

### Fix

* fix: change build_command to avoid shell escaping issues

- Changed from &#39;pip install -e .[full]&#39; to &#39;pip install build &amp;&amp; python -m build&#39;
- Square brackets in .[full] were causing shell parsing errors
- Matches check_netscaler working configuration
- Builds standard Python package (not uploaded, just for semantic release) ([`2c693fe`](https://github.com/slauger/espresso-macos/commit/2c693fe9a5c164dceaf910f5db2b3a5a01960d9f))

* fix: add build dependencies and verbose logging to semantic release

- Install build package before running semantic release
- Add root_options: -vv for verbose logging
- Add condition to only run on push to main (not PRs)
- Matches working check_netscaler workflow structure ([`3fb495d`](https://github.com/slauger/espresso-macos/commit/3fb495d26f7ade3dc8108dd694bcafd8d41b9939))

* fix: complete semantic release configuration

- Added upload_to_pypi = false (no PyPI publishing)
- Added upload_to_release = true (GitHub releases only)
- Added commit_parser = angular for conventional commits
- Added commit_parser_options with allowed tags
- Matches check_netscaler semantic release config ([`18f8f36`](https://github.com/slauger/espresso-macos/commit/18f8f36f886edd13385ad752b11a41128cd27153))

### Unknown

* Clarify that config.json is optional

- Updated README to show config is completely optional
- App works out of the box with sensible defaults
- Added default values list in Configuration section
- Made it clear in Quick Start that config is not required
- Config only needed for autostart or custom settings ([`b1f612b`](https://github.com/slauger/espresso-macos/commit/b1f612bf3c0ab426b2fb302158c879597ee9edae))

* Remove remaining cliclick/mouse movement references

- Removed core.pixels reference from cli.py logging
- Removed move_pixels from setup-autostart.sh config
- Removed move_pixels from DEVELOPMENT.md example config
- All mouse movement code fully replaced by keyboard simulation ([`319186f`](https://github.com/slauger/espresso-macos/commit/319186f3563a0b8698ecbfb4eae61b4bc9d033b3))

* Switch to Python Semantic Release and simplify installation

- Replaced build-macos.yml with release.yml workflow
  - Uses python-semantic-release for version management
  - No custom templates (simple config)
  - Builds macOS binary only on new release
  - Attaches DMG and ZIP to GitHub release
- Added semantic release config to pyproject.toml
  - Simple configuration without custom templates
  - Automatic versioning based on conventional commits
- Updated copyright: Simon → Simon Lauger
  - LICENSE file
  - pyproject.toml author field
  - Updated email to simon@lauger.name
- Removed PyPI installation instructions from README
  - Focus on binary releases (DMG/ZIP)
  - Alternative: Install from source with pip -e
  - Added instructions for building your own binary
- Simplified usage section in README ([`b023468`](https://github.com/slauger/espresso-macos/commit/b0234680edd8634728ad631fcad4fb05d0f84c46))

* Add PyInstaller build configuration for macOS binaries

- Created espresso-gui.spec for PyInstaller configuration
- Added espresso_gui_wrapper.py to avoid relative import issues
- Created GitHub Actions workflow for building macOS binaries
  - Builds .app bundle and DMG on tag push
  - Creates GitHub releases automatically
  - Generates ZIP archives for distribution
- Updated pyproject.toml:
  - Added all full dependencies (Pillow, pyobjc frameworks)
  - Added dev dependencies (pyinstaller, build, twine)
  - Corrected repository URLs to slauger/espresso-macos
- Tested locally: 25MB app bundle, all features working
- LSUIElement=True for menu bar-only app (no dock icon) ([`70047a5`](https://github.com/slauger/espresso-macos/commit/70047a56a0d02a922393f19f1eb610f8ff798791))

* Add See Also section to AUDIO_FINGERPRINTING.md

- Cross-reference to AUDIO_SETUP.md for basic setup
- Cross-reference to SCREEN_MONITORING.md as alternative
- Improved documentation navigation ([`9c15498`](https://github.com/slauger/espresso-macos/commit/9c15498dc4435d3a15908534527084415ebcec59))

* Update documentation cross-references

- Updated CLAUDE.md to reference AUDIO_SETUP.md as main guide
- Updated SCREEN_MONITORING.md See Also section
- Fixed path to README.md (relative from docs/)
- Improved documentation structure clarity ([`7023de1`](https://github.com/slauger/espresso-macos/commit/7023de1c189f17ecd73c837077266c05831d8c56))

* Add comprehensive audio setup guide

- Created docs/AUDIO_SETUP.md with complete BlackHole setup instructions
- Covers Multi-Output Device creation, Citrix audio routing
- Includes troubleshooting and configuration tuning guidance
- Updated README.md to reference AUDIO_SETUP.md as main guide
- Audio Fingerprinting remains as advanced feature guide ([`72fabcf`](https://github.com/slauger/espresso-macos/commit/72fabcfb3fb71f2fe5c9cc49b2fc1e8dfe3dd6bc))

* Initial commit: Espresso - macOS session keepalive and notification monitoring

Features:
- Session keepalive via keyboard simulation
- Audio monitoring for Teams calls/notifications (BlackHole integration)
- Screen monitoring with visual notification detection and OCR
- macOS menu bar GUI with autostart support
- Configurable via JSON config files

Components:
- espresso/core.py - Keepalive logic
- espresso/audio_monitor.py - Audio detection and fingerprinting
- espresso/screen_monitor.py - Screen capture, color detection, OCR
- espresso/gui.py - Menu bar app

Installation:
  pip install espresso-app[full]
  espresso-gui

See README.md for detailed setup instructions. ([`d7ca3e0`](https://github.com/slauger/espresso-macos/commit/d7ca3e0f0ac492173eb16ecd0e259f927ac22776))

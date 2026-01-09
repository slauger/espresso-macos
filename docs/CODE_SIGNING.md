# Code Signing Guide (Optional)

This app is currently **unsigned**. Users will see a Gatekeeper warning on first launch.

## User Workaround (No Developer Account Required)

**Method 1: Right-click Open**
1. Right-click Espresso.app
2. Click "Open"
3. Click "Open" again in the dialog

**Method 2: Remove Quarantine Flag**
```bash
xattr -cr /Applications/Espresso.app
```

This is safe - the source code is public and auditable.

## Developer: Code Signing (Requires Apple Developer Account)

If you want to distribute a signed app (costs $99/year):

### Prerequisites

1. Apple Developer Account: https://developer.apple.com/programs/
2. Developer ID Application Certificate installed in Keychain

### Add to PyInstaller Spec

```python
exe = EXE(
    # ...
    codesign_identity='Developer ID Application: Your Name (TEAM_ID)',
)

app = BUNDLE(
    # ...
    codesign_identity='Developer ID Application: Your Name (TEAM_ID)',
)
```

### Sign Manually After Build

```bash
# Build
pyinstaller espresso-gui.spec

# Sign
codesign --deep --force --sign "Developer ID Application: Your Name" \
  dist/Espresso.app

# Verify
codesign --verify --verbose dist/Espresso.app
spctl --assess --verbose dist/Espresso.app
```

### Notarization (Optional but Recommended)

```bash
# Create ZIP for notarization
cd dist
zip -r Espresso.zip Espresso.app

# Submit for notarization
xcrun notarytool submit Espresso.zip \
  --apple-id "your@email.com" \
  --team-id "TEAM_ID" \
  --wait

# Staple notarization ticket
xcrun stapler staple Espresso.app
```

### GitHub Actions (Automated Signing)

Add to `.github/workflows/release.yml`:

```yaml
- name: Import signing certificate
  env:
    CERTIFICATE_P12: ${{ secrets.CERTIFICATE_P12 }}
    CERTIFICATE_PASSWORD: ${{ secrets.CERTIFICATE_PASSWORD }}
  run: |
    echo "$CERTIFICATE_P12" | base64 --decode > certificate.p12
    security create-keychain -p actions build.keychain
    security default-keychain -s build.keychain
    security unlock-keychain -p actions build.keychain
    security import certificate.p12 -k build.keychain -P "$CERTIFICATE_PASSWORD" -T /usr/bin/codesign
    security set-key-partition-list -S apple-tool:,apple: -s -k actions build.keychain

- name: Sign app
  run: |
    codesign --deep --force --sign "Developer ID Application: Your Name" dist/Espresso.app
```

### Secrets Required

Add to GitHub repository secrets:
- `CERTIFICATE_P12`: Base64-encoded .p12 certificate
- `CERTIFICATE_PASSWORD`: Certificate password
- `APPLE_ID`: Apple ID email
- `APPLE_TEAM_ID`: Team ID from developer account

## Is Code Signing Necessary?

**No** - for open source projects:
- Users can build from source
- Users can bypass Gatekeeper (documented above)
- Source code is auditable

**Yes** - for commercial/professional use:
- Better user experience (no warning)
- Required for Mac App Store
- Builds trust with non-technical users

## Current Status

This project is **unsigned** by default. Users need to right-click → Open on first launch.

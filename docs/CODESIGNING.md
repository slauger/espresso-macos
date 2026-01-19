# Code Signing Setup for Espresso

This guide explains how to set up code signing for Espresso, both locally and in GitHub Actions.

## Prerequisites

- Apple Developer Account
- Xcode installed (for local development)
- macOS machine with Keychain Access

## Local Code Signing

### 1. Install Developer Certificate

1. Log in to [Apple Developer Portal](https://developer.apple.com)
2. Go to **Certificates, Identifiers & Profiles**
3. Create or download your **Developer ID Application** certificate
4. Double-click the downloaded certificate to install it in Keychain

### 2. Verify Certificate Installation

```bash
security find-identity -v -p codesigning
```

You should see something like:
```
1) B37C7C99B021EDBD4E8F2D356FEF1369261D5984 "Apple Development: Simon Lauger (SCUHYFZ5Q3)"
```

### 3. Build with Code Signing

The project is already configured to sign automatically with PyInstaller:

```bash
# Install dependencies
pip install pyinstaller
pip install -e .[full]

# Build (automatically signs with your certificate)
pyinstaller espresso-gui.spec
```

### 4. Verify Signature

```bash
# Verify app signature
codesign -vvv --deep --strict dist/Espresso.app

# View entitlements
codesign -d --entitlements - dist/Espresso.app

# Check if app will run without Gatekeeper warnings
spctl -a -vv dist/Espresso.app
```

## GitHub Actions Setup

To enable code signing in GitHub Actions, you need to add your certificate as secrets.

### 1. Export Certificate from Keychain

1. Open **Keychain Access**
2. Find your certificate: `Apple Development: Simon Lauger (SCUHYFZ5Q3)`
3. Right-click → **Export "Apple Development: Simon Lauger..."**
4. Save as `.p12` format
5. Set a strong password when prompted

### 2. Convert to Base64

```bash
base64 -i /path/to/certificate.p12 | pbcopy
```

This copies the base64-encoded certificate to your clipboard.

### 3. Add GitHub Secrets

Go to your repository settings → **Secrets and variables** → **Actions** → **New repository secret**

Add these secrets:

- **APPLE_CERTIFICATE**: Paste the base64 string from step 2
- **APPLE_CERTIFICATE_PASSWORD**: The password you set when exporting the .p12

### 4. How It Works

The GitHub Actions workflow (`.github/workflows/release.yml`) will:

1. Create a temporary keychain on the runner
2. Import your certificate into the keychain
3. Run PyInstaller (which automatically signs the app)
4. Sign the DMG file
5. Verify signatures
6. Clean up the keychain

If the secrets are not configured, the build will still succeed but without code signing (warnings will be shown in logs).

## Entitlements

The project uses the following entitlements (defined in `entitlements.plist`):

- **com.apple.security.automation.apple-events**: Required for controlling other apps (keepalive feature)
- **com.apple.security.device.audio-input**: Required for audio monitoring (Teams notifications)
- **com.apple.security.screen-recording**: Required for screen monitoring (visual notifications)

Additional entitlements for Python/PyInstaller compatibility:
- **com.apple.security.cs.allow-jit**
- **com.apple.security.cs.allow-unsigned-executable-memory**
- **com.apple.security.cs.allow-dyld-environment-variables**
- **com.apple.security.cs.disable-library-validation**

## Notarization (Optional)

For distribution outside of the App Store, you should notarize your app:

### 1. Add App-Specific Password

1. Go to [appleid.apple.com](https://appleid.apple.com)
2. Sign in → **App-Specific Passwords** → Generate new password
3. Save the password

### 2. Add GitHub Secrets

- **APPLE_ID**: Your Apple ID email
- **APPLE_APP_PASSWORD**: The app-specific password from step 1
- **APPLE_TEAM_ID**: Your Team ID from Apple Developer Portal

### 3. Update Workflow

Add notarization step after signing (currently not implemented):

```yaml
- name: Notarize App
  run: |
    xcrun notarytool submit "dist/Espresso.app" \
      --apple-id "${{ secrets.APPLE_ID }}" \
      --password "${{ secrets.APPLE_APP_PASSWORD }}" \
      --team-id "${{ secrets.APPLE_TEAM_ID }}" \
      --wait

    # Staple the notarization ticket
    xcrun stapler staple "dist/Espresso.app"
```

## Troubleshooting

### "Developer cannot be verified" error

If users see this error when opening the app:
1. They need to right-click → **Open** (instead of double-clicking)
2. Click **Open** in the dialog
3. This only needs to be done once

Alternatively, notarize the app (see above).

### Certificate not found in GitHub Actions

Make sure:
- The base64 encoding is correct (no line breaks)
- The password is correct
- The secrets are named exactly as expected: `APPLE_CERTIFICATE` and `APPLE_CERTIFICATE_PASSWORD`

### "No identity found" locally

Run:
```bash
security find-identity -v -p codesigning
```

If no certificate is shown, you need to install it from Apple Developer Portal.

## References

- [Apple Code Signing Guide](https://developer.apple.com/documentation/security/code_signing_services)
- [PyInstaller macOS Code Signing](https://pyinstaller.org/en/stable/feature-notes.html#macos-code-signing)
- [Apple Notarization](https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution)

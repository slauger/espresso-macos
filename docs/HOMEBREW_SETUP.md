# Homebrew Tap Setup

This document describes how to set up the automated Homebrew tap updates for espresso.

## Overview

When a new version of espresso is released via semantic-release, the GitHub Actions workflow automatically:
1. Builds the macOS app bundle
2. Creates a GitHub Release with ZIP archive
3. Updates the Homebrew cask file in the `slauger/homebrew-tap` repository

## Prerequisites

### 1. Create the homebrew-tap Repository

Create a new repository on GitHub: **`slauger/homebrew-tap`**

Initialize with the following structure:

```
homebrew-tap/
  ├── Casks/
  │   └── espresso.rb
  └── README.md
```

**Copy the cask template** from `homebrew/espresso.rb` in this repository to `Casks/espresso.rb` in the tap repository.

### 2. Create GitHub Personal Access Token (PAT)

The workflow needs a PAT to push updates to the homebrew-tap repository.

#### Option A: Fine-Grained Token (Recommended)

1. Go to **Settings** → **Developer settings** → **Personal access tokens** → **Fine-grained tokens**
2. Click **Generate new token**
3. Configure:
   - **Token name:** `Homebrew Tap Updater`
   - **Expiration:** 90 days or custom (you'll need to renew)
   - **Repository access:** Only select repositories → `slauger/homebrew-tap`
   - **Permissions:**
     - Repository permissions:
       - Contents: **Read and write**
       - Metadata: **Read-only** (automatic)
4. Click **Generate token**
5. **Copy the token** (you won't see it again!)

#### Option B: Classic Token

1. Go to **Settings** → **Developer settings** → **Personal access tokens** → **Tokens (classic)**
2. Click **Generate new token**
3. Configure:
   - **Note:** `Homebrew Tap Updater`
   - **Expiration:** 90 days or custom
   - **Scopes:**
     - ✅ `repo` (Full control of private repositories)
4. Click **Generate token**
5. **Copy the token**

### 3. Add Token as Repository Secret

1. Go to the **espresso-macos** repository
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Configure:
   - **Name:** `HOMEBREW_TAP_TOKEN`
   - **Secret:** Paste your PAT from step 2
5. Click **Add secret**

## How It Works

### Workflow Trigger

When code is pushed to `main`, the workflow:
1. Runs semantic-release to determine if a new version should be created
2. If yes, creates a git tag and GitHub Release
3. Builds the macOS app bundle with PyInstaller
4. Creates DMG and ZIP archives
5. Uploads archives to the GitHub Release
6. **Updates the Homebrew cask** (new job: `update-homebrew-tap`)

### Update Process

The `update-homebrew-tap` job:
1. Checks out the `slauger/homebrew-tap` repository using the PAT
2. Downloads the ZIP file from the new GitHub Release
3. Calculates the SHA256 checksum
4. Updates `Casks/espresso.rb`:
   - Sets `version` to the new version
   - Sets `sha256` to the calculated checksum
5. Commits and pushes the changes back to homebrew-tap

### Cask File Format

```ruby
cask "espresso" do
  version "0.1.0"                    # ← Updated automatically
  sha256 "abc123..."                 # ← Updated automatically

  url "https://github.com/slauger/espresso-macos/releases/download/v#{version}/Espresso-#{version}-macOS.zip"
  name "Espresso"
  desc "Keep Citrix Viewer sessions alive and monitor Teams notifications"
  homepage "https://github.com/slauger/espresso-macos"

  livecheck do
    url :url
    strategy :github_latest
  end

  app "Espresso.app"

  zap trash: "~/.espresso"
end
```

## Installation for End Users

Once the tap is set up, users can install espresso via Homebrew:

```bash
# Add the tap (only needed once)
brew tap slauger/tap

# Install espresso
brew install espresso

# Update espresso when new versions are available
brew upgrade espresso
```

## Troubleshooting

### Workflow fails: "Resource not accessible by integration"

- The `HOMEBREW_TAP_TOKEN` secret is missing or has expired
- Solution: Create a new PAT and update the secret

### Workflow fails: "repository not found"

- The homebrew-tap repository doesn't exist yet
- Solution: Create `slauger/homebrew-tap` on GitHub first

### Cask file not updating

- Check the workflow logs for the `update-homebrew-tap` job
- Verify the PAT has write permissions to the homebrew-tap repository
- Check if the `Casks/espresso.rb` file exists in the tap repository

### sed command fails on macOS locally

The workflow uses Linux (`ubuntu-latest`), so it uses GNU sed. If testing locally on macOS:
```bash
# macOS requires -i '' instead of -i
sed -i '' "s/version \".*\"/version \"${VERSION}\"/" Casks/espresso.rb
```

## Maintenance

### Token Expiration

When the PAT expires:
1. Create a new token (same steps as above)
2. Update the `HOMEBREW_TAP_TOKEN` secret in repository settings
3. The next release will use the new token

### Testing the Workflow

To test without a real release:
1. Use `workflow_dispatch` trigger (already enabled)
2. Go to **Actions** tab → **Release and Build** → **Run workflow**
3. Note: This will only test if `semantic-release` determines a new version is needed

## References

- [Homebrew: How to Create and Maintain a Tap](https://docs.brew.sh/How-to-Create-and-Maintain-a-Tap)
- [GitHub: Automatic token authentication](https://docs.github.com/en/actions/security-guides/automatic-token-authentication)
- [Homebrew Cask Cookbook](https://docs.brew.sh/Cask-Cookbook)

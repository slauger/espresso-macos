# Quick Homebrew Tap Setup (CLI)

Fast track setup using CLI commands where possible.

## 1. Create homebrew-tap Repository

```bash
# Create new repo on GitHub
gh repo create slauger/homebrew-tap --public --description "Homebrew tap for slauger's tools"

# Clone it locally
git clone git@github.com:slauger/homebrew-tap.git
cd homebrew-tap

# Create Cask structure
mkdir Casks
cp ../espresso-macos/homebrew/espresso.rb Casks/espresso.rb

# Initial commit
git add Casks/
git commit -m "Initial espresso cask"
git push origin main

cd ../espresso-macos
```

## 2. Create GitHub Personal Access Token

**This step MUST be done via web UI** (GitHub CLI can't create tokens):

```bash
# Open the token creation page
open "https://github.com/settings/tokens?type=beta"
```

**Manual steps:**
1. Click **"Generate new token"**
2. Configure:
   - **Token name:** `Homebrew Tap Updater`
   - **Expiration:** 90 days (or custom)
   - **Repository access:** Only select repositories → `slauger/homebrew-tap`
   - **Permissions:**
     - Repository permissions → Contents: **Read and write**
3. Click **"Generate token"**
4. **Copy the token** (starts with `github_pat_...`)

## 3. Store Token as Repository Secret

Now back to CLI! Store the token you just copied:

```bash
# Interactive mode (paste token when prompted)
gh secret set HOMEBREW_TAP_TOKEN

# Or from clipboard (macOS)
pbpaste | gh secret set HOMEBREW_TAP_TOKEN --body -

# Verify it was set
gh secret list
```

## 4. Test the Workflow

Uncomment the `update-homebrew-tap` job in `.github/workflows/release.yml` and push a test commit:

```bash
# Make a small change (e.g., update README)
git add .
git commit -m "feat: enable homebrew tap auto-update"
git push origin main

# Watch the workflow run
gh run watch
```

If semantic-release creates a new version, the workflow will automatically update the homebrew-tap!

## 5. Verify Installation Works

After the first release completes:

```bash
# Test installation (full tap name required due to name conflict)
brew install slauger/tap/espresso

# Check it installed correctly
open /Applications/Espresso.app
```

## Troubleshooting

**Check if secret exists:**
```bash
gh secret list
```

**View workflow logs:**
```bash
gh run list --limit 5
gh run view <run-id>  # Get ID from above
```

**Re-run failed workflow:**
```bash
gh run rerun <run-id>
```

**Update expired token:**
```bash
# Create new token via web UI, then:
gh secret set HOMEBREW_TAP_TOKEN  # Enter new token
```

## One-Time Manual Sync (Optional)

If you want to manually sync the cask before the next release:

```bash
# Get latest release info
VERSION=$(gh release view --json tagName -q .tagName | sed 's/^v//')
ZIP_URL="https://github.com/slauger/espresso-macos/releases/download/v${VERSION}/Espresso-${VERSION}-macOS.zip"

# Download and calculate SHA256
wget "$ZIP_URL" -O espresso.zip
SHA256=$(shasum -a 256 espresso.zip | awk '{print $1}')

# Clone homebrew-tap
cd /tmp
gh repo clone slauger/homebrew-tap
cd homebrew-tap

# Update cask
sed -i '' "s/version \".*\"/version \"${VERSION}\"/" Casks/espresso.rb
sed -i '' "s/sha256 \".*\"/sha256 \"${SHA256}\"/" Casks/espresso.rb

# Commit and push
git add Casks/espresso.rb
git commit -m "chore: update espresso to ${VERSION}"
git push
```

## Summary

**What needs Web UI:**
- Creating the PAT (step 2)

**Everything else via CLI:**
- ✅ Create repo (`gh repo create`)
- ✅ Store secret (`gh secret set`)
- ✅ Monitor workflows (`gh run watch`)
- ✅ Manual sync (`gh release view`, `wget`, etc.)

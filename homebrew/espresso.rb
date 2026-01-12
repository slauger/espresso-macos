cask "espresso" do
  version "0.1.0"
  sha256 "PLACEHOLDER_SHA256"

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

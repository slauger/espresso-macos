#!/bin/bash
# Setup script for Espresso with autostart

set -e

echo "🚀 Setting up Espresso with autostart..."
echo ""

# Create config directory
echo "📁 Creating config directory..."
mkdir -p ~/.espresso

# Create config file
echo "⚙️  Creating config file at ~/.espresso/config.json..."
cat > ~/.espresso/config.json << 'EOF'
{
  "app_name": "Citrix Viewer",
  "interval_seconds": 60,
  "move_pixels": 1,
  "audio_device": "BlackHole",
  "notification_threshold": 0.05,
  "call_threshold": 0.02,
  "call_duration": 3.0,
  "autostart": true,
  "autostart_audio": true
}
EOF

echo "✅ Config file created!"
echo ""
echo "📝 Config contents:"
cat ~/.espresso/config.json
echo ""
echo ""

echo "✅ Setup complete!"
echo ""
echo "Now you can start espresso-gui and it will:"
echo "  ✓ Automatically start keepalive monitoring"
echo "  ✓ Automatically start audio monitoring"
echo "  ✓ Detect Teams calls and notifications"
echo "  ✓ Only notify when Citrix is NOT in foreground"
echo ""
echo "To launch:"
echo "  espresso-gui"
echo ""
echo "To edit config:"
echo "  nano ~/.espresso/config.json"
echo ""

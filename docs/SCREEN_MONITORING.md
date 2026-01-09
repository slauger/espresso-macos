# Screen Monitoring for Visual Notification Detection

## Overview

Screen monitoring captures screenshots of a target window (e.g., Citrix Viewer) and analyzes them for visual indicators of notifications, such as Teams notification popups.

This is useful when:
- Audio monitoring can't detect chat notifications (no sound produced)
- Notifications appear visually but don't trigger audio
- You need a backup detection method to complement audio monitoring

## How It Works

1. **Window Capture**: Uses macOS Quartz API to capture screenshots of specific windows
2. **Region Extraction**: Focuses on notification areas (e.g., bottom-right corner)
3. **Color Detection**: Counts pixels matching the notification background color
4. **Notification Trigger**: Sends notification when enough matching pixels are detected

## Detection Method: Color-Based

The color detection method works by:

1. Capturing the target window (even when in background)
2. Extracting the monitoring region (default: bottom-right 1000x750px)
3. Counting pixels that match the Teams notification blue color (`#464775`)
4. Triggering when `min_pixels` threshold is exceeded (default: 1000 pixels)

### Why Color Detection?

Teams notifications have a distinctive dark blue background color (~#464775). When a notification popup appears:
- The popup covers ~1500-2000 pixels in the bottom-right corner
- The color is consistent across notification types
- Detection is fast and reliable (< 100ms per scan)

## Configuration

Add to `~/.espresso/config.json`:

```json
{
  "screen_monitoring": {
    "enabled": true,
    "scan_interval": 2,
    "detection_method": "color",
    "teams_notification_color": "#464775",
    "color_tolerance": 30,
    "min_pixels": 1000
  }
}
```

### Configuration Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `enabled` | `false` | Enable screen monitoring feature |
| `scan_interval` | `2` | Seconds between scans (notification lasts ~5s) |
| `detection_method` | `"color"` | Detection algorithm (currently only "color") |
| `teams_notification_color` | `"#464775"` | Hex color to detect (Teams blue) |
| `color_tolerance` | `30` | RGB tolerance for color matching (0-255) |
| `min_pixels` | `1000` | Minimum matching pixels to trigger detection |

### Tuning the Detection

**If getting false positives** (detecting when no notification):
- Increase `min_pixels` (try 1500 or 2000)
- Decrease `color_tolerance` (try 20 or 15)

**If missing notifications**:
- Decrease `min_pixels` (try 800 or 500)
- Increase `color_tolerance` (try 40 or 50)
- Decrease `scan_interval` (try 1.5 or 1.0)

**Finding the right color**:
1. Take a screenshot of a Teams notification
2. Use a color picker to get the hex color
3. Update `teams_notification_color` in config

## Usage

### Test Screen Monitoring (Standalone)

```bash
# Uses config from ~/.espresso/config.json
python3 -m espresso.screen_monitor
```

This will:
- Load configuration
- Start monitoring the configured window
- Print debug info for each scan
- Trigger callback when notification detected

### Using with GUI

Screen monitoring integrates with the GUI menu bar app:

```bash
espresso-gui
```

Then:
1. Click the Espresso menu bar icon
2. Click "Enable Screen Monitor"
3. Notifications will appear when Teams popups are detected

### Autostart Screen Monitoring

Enable automatic startup in config:

```json
{
  "autostart_screen": true,
  "screen_monitoring": {
    "enabled": true,
    ...
  }
}
```

Or use CLI flag:

```bash
espresso-gui --autostart-screen
```

## Testing

### 1. Test Window Capture

```bash
python3 test_window_capture.py "Citrix Viewer"
```

This verifies:
- Window can be found
- Screenshot capture works
- Background capture works (switch away from Citrix)

Check the generated screenshots:
- `window_capture_TIMESTAMP.png` - Full window
- `window_capture_region_TIMESTAMP.png` - Bottom-right region

### 2. Test Color Detection

1. Start screen monitoring:
   ```bash
   python3 -m espresso.screen_monitor
   ```

2. In Citrix, trigger a Teams notification:
   - Have someone send you a Teams chat message
   - Or use Teams "Test notification" feature

3. Check the terminal output:
   - Should see: "🔔 Notification detected via screen monitoring!"
   - Debug info shows pixel count and percentage

### 3. Test with GUI

1. Start GUI with screen monitoring:
   ```bash
   espresso-gui --autostart-screen
   ```

2. Click menu bar icon → verify "Disable Screen Monitor" is shown (means it's running)

3. Trigger a Teams notification in Citrix

4. You should receive a macOS notification:
   - Title: "🔔 Teams Notification (Visual)"
   - Subtitle: "Notification detected in Citrix Viewer"

## Troubleshooting

### Screen Recording Permissions

If capture fails, check:
1. System Settings → Privacy & Security → Screen Recording
2. Ensure Terminal.app (or your IDE) is allowed
3. Restart Terminal after granting permissions

### Window Not Found

If "Window 'Citrix Viewer' not found":
- Check the exact window name: `espresso-list`
- Update `app_name` in config to match exactly
- Ensure Citrix is running and has visible windows

### No Detection

If monitoring runs but doesn't detect notifications:
1. Verify the notification color:
   - Take a screenshot during a notification
   - Use color picker to check the blue color
   - Update `teams_notification_color` if different

2. Check the region:
   - Open `window_capture_region_TIMESTAMP.png`
   - Verify notification popup is within this region
   - Adjust region settings if needed (see Advanced Config below)

3. Enable debug logging:
   - Set `LOG_LEVEL=DEBUG` environment variable
   - Re-run screen monitor
   - Check pixel count in output

### Performance Issues

If CPU usage is too high:
- Increase `scan_interval` (try 3 or 5 seconds)
- Reduce monitoring region size (see Advanced Config)

## Advanced Configuration

### Custom Region Position

By default, monitors bottom-right corner. To change:

```python
# In code (not yet exposed to config)
monitor = ScreenMonitor(
    window_name="Citrix Viewer",
    region_position="top-right",  # or "bottom-left", "top-left"
    region_size=(400, 200)  # width, height in pixels
)
```

### Multiple Detection Areas

Not yet supported, but planned for future:
- Monitor multiple regions simultaneously
- Different thresholds per region
- Support for different notification types

## Architecture

### Files

- `espresso/screen_monitor.py` - Main screen monitoring module
- `test_window_capture.py` - Test script for window capture
- `examples/config-with-screen-monitoring.json` - Example config

### Key Classes

**ScreenMonitor**:
- `__init__()` - Initialize with config
- `start(callback)` - Start monitoring loop
- `stop()` - Stop monitoring
- `_scan_once()` - Perform one detection cycle
- `_capture_window()` - Capture window screenshot
- `_detect_color()` - Count matching pixels

### Callback Interface

```python
def on_notification(source: str, details: dict):
    """
    Args:
        source: "screen" (detection source)
        details: {
            'window': 'Desktop Remote',
            'detection_method': 'color',
            'timestamp': '2026-01-08T13:30:00'
        }
    """
    print(f"Notification from {source}: {details}")
```

## Integration with Audio Monitoring

Screen monitoring complements audio monitoring:

| Feature | Audio Monitoring | Screen Monitoring |
|---------|-----------------|-------------------|
| Detects calls | ✅ Yes | ❌ No |
| Detects chat notifications | ⚠️ Sometimes | ✅ Yes |
| CPU usage | Low | Medium |
| Latency | < 100ms | ~2 seconds |
| Requires setup | Yes (BlackHole) | No |

**Best Practice**: Enable both for complete coverage:
- Audio monitoring catches calls (sustained audio)
- Screen monitoring catches chat notifications (visual only)

## Limitations

1. **macOS only**: Uses Quartz API (macOS-specific)
2. **Notification timing**: 2-second scan interval means 0-2s delay
3. **Color-dependent**: Requires consistent notification colors
4. **CPU overhead**: Screenshot capture + pixel analysis every 2 seconds
5. **Citrix-specific**: May need tuning for other apps

## Future Enhancements

- [ ] Support for multiple notification colors
- [ ] Motion detection (change between frames)
- [ ] OCR-based detection (read notification text)
- [ ] Machine learning classifier
- [ ] Linux/Windows support (alternative APIs)
- [ ] Configurable region positions via config file

## See Also

- [AUDIO_FINGERPRINTING.md](AUDIO_FINGERPRINTING.md) - Audio-based detection
- [CLAUDE.md](CLAUDE.md) - Development state and history
- [README.md](README.md) - Main project documentation

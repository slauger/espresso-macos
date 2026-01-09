#!/usr/bin/env python3
"""
Debug script for screen monitoring - shows detailed detection info
"""
import sys
import time
from datetime import datetime

try:
    import Quartz
    from Quartz import CGWindowListCopyWindowInfo, CGWindowListCreateImage
    from Quartz import kCGWindowListOptionAll, kCGNullWindowID
    from Quartz import kCGWindowListOptionIncludingWindow
    from Quartz import kCGWindowImageBoundsIgnoreFraming, CGRectNull
except ImportError:
    print("❌ Error: pyobjc-framework-Quartz not installed")
    sys.exit(1)

try:
    from PIL import Image
except ImportError:
    print("❌ Error: Pillow not installed")
    sys.exit(1)


def hex_to_rgb(hex_color: str) -> tuple:
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def color_distance(color1: tuple, color2: tuple) -> float:
    """Calculate Euclidean distance between two RGB colors."""
    r1, g1, b1 = color1
    r2, g2, b2 = color2
    return ((r2 - r1) ** 2 + (g2 - g1) ** 2 + (b2 - b1) ** 2) ** 0.5


def find_window(target_name: str):
    """Find window by name."""
    window_list = CGWindowListCopyWindowInfo(
        kCGWindowListOptionAll,
        kCGNullWindowID
    )

    matching_windows = []

    for window in window_list:
        window_name = window.get('kCGWindowName', '')
        owner_name = window.get('kCGWindowOwnerName', '')

        if target_name.lower() in window_name.lower() or target_name.lower() in owner_name.lower():
            bounds = window.get('kCGWindowBounds', {})
            width = bounds.get('Width', 0)
            height = bounds.get('Height', 0)

            matching_windows.append({
                'id': window.get('kCGWindowNumber'),
                'name': window_name,
                'owner': owner_name,
                'bounds': bounds,
                'is_onscreen': window.get('kCGWindowIsOnscreen', False),
                'size': width * height
            })

    if not matching_windows:
        return None

    onscreen_windows = [w for w in matching_windows if w['is_onscreen']]

    if onscreen_windows:
        return max(onscreen_windows, key=lambda w: w['size'])
    else:
        return max(matching_windows, key=lambda w: w['size'])


def capture_window(window_id: int):
    """Capture screenshot of window."""
    image_ref = CGWindowListCreateImage(
        CGRectNull,
        kCGWindowListOptionIncludingWindow,
        window_id,
        kCGWindowImageBoundsIgnoreFraming
    )

    if not image_ref:
        return None

    width = Quartz.CGImageGetWidth(image_ref)
    height = Quartz.CGImageGetHeight(image_ref)
    bytes_per_row = Quartz.CGImageGetBytesPerRow(image_ref)

    data_provider = Quartz.CGImageGetDataProvider(image_ref)
    pixel_data = Quartz.CGDataProviderCopyData(data_provider)

    image = Image.frombytes(
        'RGBA',
        (width, height),
        pixel_data,
        'raw',
        'BGRA',
        bytes_per_row
    )

    return image


def analyze_region(region: Image.Image, target_color: tuple, tolerance: int):
    """Analyze region and show detailed color statistics."""
    # Convert to RGB
    if region.mode != 'RGB':
        region = region.convert('RGB')

    pixels = region.load()
    matching_pixels = 0
    total_pixels = region.width * region.height

    # Color histogram
    color_counts = {}

    for x in range(region.width):
        for y in range(region.height):
            pixel_color = pixels[x, y][:3]
            distance = color_distance(pixel_color, target_color)

            if distance <= tolerance:
                matching_pixels += 1

            # Count top colors (sample every 10th pixel)
            if x % 10 == 0 and y % 10 == 0:
                color_key = f"#{pixel_color[0]:02x}{pixel_color[1]:02x}{pixel_color[2]:02x}"
                color_counts[color_key] = color_counts.get(color_key, 0) + 1

    percentage = (matching_pixels / total_pixels) * 100

    # Top 5 colors
    top_colors = sorted(color_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    return {
        'matching_pixels': matching_pixels,
        'total_pixels': total_pixels,
        'percentage': percentage,
        'top_colors': top_colors
    }


def main():
    """Main debug function."""
    target_name = "Citrix Viewer"
    target_color_hex = "#464775"
    tolerance = 30
    min_pixels = 1000

    if len(sys.argv) > 1:
        target_name = sys.argv[1]

    target_color = hex_to_rgb(target_color_hex)

    # BIGGER REGION - 3x taller AND 2x wider!
    region_width, region_height = 1000, 750

    print(f"🔍 Screen Monitor Debug")
    print(f"{'=' * 80}")
    print(f"Target window:  {target_name}")
    print(f"Target color:   {target_color_hex} = RGB{target_color}")
    print(f"Tolerance:      {tolerance}")
    print(f"Min pixels:     {min_pixels}")
    print(f"Region:         bottom-right {region_width}x{region_height}")
    print()
    print(f"Scanning every 2 seconds... Press Ctrl+C to stop")
    print(f"{'=' * 80}")
    print()

    scan_count = 0

    try:
        while True:
            scan_count += 1
            timestamp = datetime.now().strftime("%H:%M:%S")

            # Find window
            window_info = find_window(target_name)
            if not window_info:
                print(f"[{timestamp}] ❌ Window not found")
                time.sleep(2)
                continue

            # Capture
            image = capture_window(window_info['id'])
            if not image:
                print(f"[{timestamp}] ❌ Capture failed")
                time.sleep(2)
                continue

            # Extract region
            if image.width < region_width or image.height < region_height:
                print(f"[{timestamp}] ❌ Image too small: {image.width}x{image.height}")
                time.sleep(2)
                continue

            x = image.width - region_width
            y = image.height - region_height
            region = image.crop((x, y, image.width, image.height))

            # Analyze
            stats = analyze_region(region, target_color, tolerance)

            # Print results
            detected = stats['matching_pixels'] >= min_pixels
            icon = "🔔" if detected else "⚪"

            print(f"[{timestamp}] Scan #{scan_count} {icon}")
            print(f"  Matching pixels: {stats['matching_pixels']:,} / {stats['total_pixels']:,} ({stats['percentage']:.2f}%)")
            print(f"  Detection: {'✅ YES' if detected else '❌ NO'} (threshold: {min_pixels})")
            print(f"  Top colors in region:")
            for color, count in stats['top_colors']:
                print(f"    {color}: {count} samples")
            print()

            # Save every scan to check later
            filename = f"debug_region_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            region.save(filename)
            print(f"  💾 Saved: {filename}")
            print()

            time.sleep(2)

    except KeyboardInterrupt:
        print()
        print(f"{'=' * 80}")
        print(f"Stopped after {scan_count} scans")


if __name__ == "__main__":
    main()

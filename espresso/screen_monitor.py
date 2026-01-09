#!/usr/bin/env python3
"""
Screen monitoring for visual notification detection.

Monitors a specific window (e.g., Citrix Viewer) for visual changes
that indicate notifications, such as Teams notification popups.
"""
import sys
import time
import logging
from datetime import datetime
from typing import Optional, Callable, Dict, Any

try:
    import Quartz
    from Quartz import CGWindowListCopyWindowInfo, CGWindowListCreateImage
    from Quartz import kCGWindowListOptionAll, kCGNullWindowID
    from Quartz import kCGWindowListOptionIncludingWindow
    from Quartz import kCGWindowImageBoundsIgnoreFraming, CGRectNull
except ImportError:
    print("❌ Error: pyobjc-framework-Quartz not installed")
    print("Install with: pip install pyobjc-framework-Quartz")
    sys.exit(1)

try:
    from PIL import Image
except ImportError:
    print("❌ Error: Pillow not installed")
    print("Install with: pip install Pillow")
    sys.exit(1)

try:
    import Vision
    from Foundation import NSURL
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    logger.warning("Vision framework not available - OCR disabled")


logger = logging.getLogger(__name__)


class ScreenMonitor:
    """
    Monitor a window for visual notifications using color detection.

    This class captures screenshots of a specific window and analyzes
    regions for notification indicators (e.g., Teams blue notification popup).
    """

    def __init__(
        self,
        window_name: str,
        scan_interval: float = 2.0,
        detection_method: str = "color",
        notification_color: str = "#464775",
        color_tolerance: int = 30,
        min_pixels: int = 1000,
        region_size: tuple = (1000, 750),
        region_position: str = "bottom-right",
        debug_screenshots: bool = False
    ):
        """
        Initialize screen monitor.

        Args:
            window_name: Name of the window to monitor (e.g., "Citrix Viewer")
            scan_interval: Seconds between scans (default: 2.0)
            detection_method: Detection method ("color" or "diff")
            notification_color: Hex color of notification background (e.g., "#464775")
            color_tolerance: RGB tolerance for color matching (0-255)
            min_pixels: Minimum pixels required to trigger detection
            region_size: (width, height) of region to monitor (default: 1000x750)
            region_position: Where to monitor ("bottom-right", "top-right", etc.)
        """
        self.window_name = window_name
        self.scan_interval = scan_interval
        self.detection_method = detection_method
        self.notification_color = self._hex_to_rgb(notification_color)
        self.color_tolerance = color_tolerance
        self.min_pixels = min_pixels
        self.region_size = region_size
        self.region_position = region_position

        self.running = False
        self.callback = None
        self.last_detection_time = None
        self.detection_cooldown = 10.0  # Don't re-trigger within 10 seconds
        self.debug_screenshots = debug_screenshots
        self.scan_count = 0

        logger.info(f"ScreenMonitor initialized: window='{window_name}', "
                   f"scan_interval={scan_interval}s, color={notification_color}, "
                   f"debug_screenshots={debug_screenshots}")

    def _hex_to_rgb(self, hex_color: str) -> tuple:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def _find_window(self) -> Optional[Dict[str, Any]]:
        """
        Find window by name.

        Returns:
            Dict with window info (id, name, owner, bounds) or None if not found
        """
        window_list = CGWindowListCopyWindowInfo(
            kCGWindowListOptionAll,
            kCGNullWindowID
        )

        matching_windows = []

        for window in window_list:
            window_name = window.get('kCGWindowName', '')
            owner_name = window.get('kCGWindowOwnerName', '')

            # Check both window name and owner name
            if (self.window_name.lower() in window_name.lower() or
                self.window_name.lower() in owner_name.lower()):
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

        # Prioritize OnScreen windows, then by size
        onscreen_windows = [w for w in matching_windows if w['is_onscreen']]

        if onscreen_windows:
            return max(onscreen_windows, key=lambda w: w['size'])
        else:
            return max(matching_windows, key=lambda w: w['size'])

    def _capture_window(self, window_id: int) -> Optional[Image.Image]:
        """
        Capture screenshot of window.

        Args:
            window_id: Window ID to capture

        Returns:
            PIL Image or None if capture failed
        """
        image_ref = CGWindowListCreateImage(
            CGRectNull,
            kCGWindowListOptionIncludingWindow,
            window_id,
            kCGWindowImageBoundsIgnoreFraming
        )

        if not image_ref:
            return None

        # Convert CGImage to PIL Image
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

    def _extract_region(self, image: Image.Image) -> Optional[Image.Image]:
        """
        Extract monitoring region from image.

        Args:
            image: Full window screenshot

        Returns:
            Cropped region or None if image too small
        """
        region_width, region_height = self.region_size

        if image.width < region_width or image.height < region_height:
            logger.warning(f"Image too small for region: {image.width}x{image.height}")
            return None

        # Calculate region coordinates based on position
        if self.region_position == "bottom-right":
            x = image.width - region_width
            y = image.height - region_height
        elif self.region_position == "top-right":
            x = image.width - region_width
            y = 0
        elif self.region_position == "bottom-left":
            x = 0
            y = image.height - region_height
        elif self.region_position == "top-left":
            x = 0
            y = 0
        else:
            logger.error(f"Unknown region position: {self.region_position}")
            return None

        return image.crop((x, y, x + region_width, y + region_height))

    def _color_distance(self, color1: tuple, color2: tuple) -> float:
        """
        Calculate Euclidean distance between two RGB colors.

        Args:
            color1: RGB tuple (r, g, b)
            color2: RGB tuple (r, g, b)

        Returns:
            Distance value (0 = identical)
        """
        r1, g1, b1 = color1
        r2, g2, b2 = color2
        return ((r2 - r1) ** 2 + (g2 - g1) ** 2 + (b2 - b1) ** 2) ** 0.5

    def _detect_color(self, region: Image.Image) -> tuple:
        """
        Detect notification color in region.

        Args:
            region: Image region to analyze

        Returns:
            Tuple of (detected: bool, matching_pixels: int)
        """
        # Convert to RGB if needed
        if region.mode != 'RGB':
            region = region.convert('RGB')

        # Count pixels matching notification color
        pixels = region.load()
        matching_pixels = 0
        total_pixels = region.width * region.height

        for x in range(region.width):
            for y in range(region.height):
                pixel_color = pixels[x, y][:3]  # RGB only (ignore alpha)
                distance = self._color_distance(pixel_color, self.notification_color)

                if distance <= self.color_tolerance:
                    matching_pixels += 1

        percentage = (matching_pixels / total_pixels) * 100
        detected = matching_pixels >= self.min_pixels

        logger.debug(f"Color detection: {matching_pixels}/{total_pixels} pixels "
                    f"({percentage:.1f}%) match {self.notification_color}, "
                    f"detected={detected}")

        return (detected, matching_pixels)

    def _extract_text_from_region(self, region: Image.Image) -> str:
        """
        Extract text from region using OCR.

        Args:
            region: Image region to analyze

        Returns:
            Extracted text (empty string if OCR not available or no text found)
        """
        if not OCR_AVAILABLE:
            return ""

        try:
            # Save region to temp file
            temp_path = "/tmp/espresso_ocr.png"
            region.save(temp_path)

            # Create OCR request
            request = Vision.VNRecognizeTextRequest.alloc().init()
            request.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate)
            request.setUsesLanguageCorrection_(True)

            # Load image
            url = NSURL.fileURLWithPath_(temp_path)
            handler = Vision.VNImageRequestHandler.alloc().initWithURL_options_(url, None)

            # Perform OCR
            success = handler.performRequests_error_([request], None)

            if not success[0]:
                logger.debug("OCR request failed")
                return ""

            # Extract text from results
            results = request.results()
            if not results:
                return ""

            # Get all text lines
            lines = []
            for observation in results:
                text = observation.text()
                confidence = observation.confidence()
                if confidence > 0.5:  # Only include confident results
                    lines.append(text)

            # Filter relevant lines (sender + message)
            return self._filter_notification_text(lines)

        except Exception as e:
            logger.debug(f"OCR extraction failed: {e}")
            return ""

    def _filter_notification_text(self, lines: list) -> str:
        """
        Filter OCR text to extract only sender and message.

        Args:
            lines: List of text lines from OCR

        Returns:
            Filtered text with sender and message
        """
        if not lines:
            return ""

        # Filter out common UI elements
        ignore_keywords = [
            'Microsoft Teams',
            'Schnelle Antwort senden',
            'Online mit Microsoft Exchange',
            'len',
            'SL',
            '100 %',
            '+',
        ]

        filtered_lines = []
        found_sender = False

        for line in lines:
            # Skip lines with ignore keywords
            if any(keyword in line for keyword in ignore_keywords):
                continue

            # Skip time patterns (HH:MM or DD.MM.YYYY)
            if ':' in line and len(line) < 10:  # Like "15:16"
                continue
            if '.' in line and line.replace('.', '').replace(' ', '').isdigit():  # Like "08.01.2026"
                continue

            # Look for sender pattern: (Gast) Name or just Name
            if '(' in line and ')' in line:
                found_sender = True
                filtered_lines.append(line)
            elif found_sender:
                # This is likely the message after the sender
                filtered_lines.append(line)
                break  # Only take sender + first message line

        # Return sender and message
        return " | ".join(filtered_lines) if filtered_lines else " | ".join(lines[:2])


    def _should_trigger(self) -> bool:
        """
        Check if enough time has passed since last detection (cooldown).

        Returns:
            True if detection should trigger callback
        """
        if self.last_detection_time is None:
            return True

        elapsed = time.time() - self.last_detection_time
        return elapsed >= self.detection_cooldown

    def _scan_once(self) -> bool:
        """
        Perform one scan cycle.

        Returns:
            True if notification detected
        """
        self.scan_count += 1

        # Find window
        window_info = self._find_window()
        if not window_info:
            logger.warning(f"Window '{self.window_name}' not found")
            return False

        # Capture screenshot
        image = self._capture_window(window_info['id'])
        if not image:
            # Only log every 10th failure to avoid spam
            if self.scan_count % 10 == 0:
                logger.warning(f"Failed to capture window {window_info['id']} (scan #{self.scan_count})")
            return False

        # Extract monitoring region
        region = self._extract_region(image)
        if not region:
            return False

        # Save debug screenshot if enabled
        if self.debug_screenshots:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screen_monitor_debug_{timestamp}.png"
            try:
                region.save(filename)
                logger.debug(f"Saved debug screenshot: {filename}")
            except Exception as e:
                logger.error(f"Failed to save debug screenshot: {e}")

        # Detect notification
        detected = False
        matching_pixels = 0
        notification_text = ""

        if self.detection_method == "color":
            detected, matching_pixels = self._detect_color(region)
            logger.debug(f"Scan #{self.scan_count}: {matching_pixels:,} matching pixels, "
                        f"detected={detected}")

            # If detected, extract text via OCR
            if detected and OCR_AVAILABLE:
                notification_text = self._extract_text_from_region(region)
                if notification_text:
                    logger.info(f"OCR extracted: {notification_text[:100]}")
        else:
            logger.error(f"Unknown detection method: {self.detection_method}")
            return False

        if detected:
            logger.info(f"🔔 Notification detected via screen monitoring! "
                       f"({matching_pixels} pixels)")

            print(f"[SCREEN_MONITOR] Detection! pixels={matching_pixels}")
            print(f"[SCREEN_MONITOR] callback={self.callback}")
            print(f"[SCREEN_MONITOR] _should_trigger={self._should_trigger()}")

            # Call callback if registered and cooldown passed
            if self.callback:
                if self._should_trigger():
                    print(f"[SCREEN_MONITOR] Calling callback...")
                    try:
                        self.callback("screen", {
                            'window': window_info['name'],
                            'detection_method': self.detection_method,
                            'timestamp': datetime.now().isoformat(),
                            'matching_pixels': matching_pixels,
                            'notification_text': notification_text
                        })
                        print(f"[SCREEN_MONITOR] Callback called successfully")
                        # Update last detection time AFTER successful callback
                        self.last_detection_time = time.time()
                    except Exception as e:
                        logger.error(f"Callback error: {e}", exc_info=True)
                        print(f"[SCREEN_MONITOR] Callback error: {e}")
                        import traceback
                        traceback.print_exc()
                else:
                    print(f"[SCREEN_MONITOR] Cooldown active, not triggering")
            else:
                print(f"[SCREEN_MONITOR] No callback registered!")

        return detected

    def start(self, callback: Optional[Callable] = None):
        """
        Start monitoring loop.

        Args:
            callback: Function to call when notification detected
                     Signature: callback(source: str, details: dict)
        """
        if self.running:
            logger.warning("Screen monitor already running")
            return

        self.callback = callback
        self.running = True
        self.last_detection_time = None

        logger.info(f"Screen monitor started: scanning every {self.scan_interval}s")

        try:
            while self.running:
                self._scan_once()
                time.sleep(self.scan_interval)
        except KeyboardInterrupt:
            logger.info("Screen monitor interrupted")
        finally:
            self.running = False
            logger.info("Screen monitor stopped")

    def stop(self):
        """Stop monitoring loop."""
        logger.info("Stopping screen monitor...")
        self.running = False


def load_config(config_path: str = None) -> dict:
    """Load screen monitoring config from JSON file."""
    import json
    import os

    if config_path is None:
        config_path = os.path.expanduser("~/.espresso/config.json")

    if not os.path.exists(config_path):
        logger.warning(f"Config not found: {config_path}")
        return {}

    with open(config_path) as f:
        config = json.load(f)

    return config.get("screen_monitoring", {})


def main():
    """Test screen monitor."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Load config
    config = load_config()
    window_name = config.get("window_name", "Citrix Viewer")

    # Create monitor
    monitor = ScreenMonitor(
        window_name=window_name,
        scan_interval=config.get("scan_interval", 2.0),
        detection_method=config.get("detection_method", "color"),
        notification_color=config.get("teams_notification_color", "#464775"),
        color_tolerance=config.get("color_tolerance", 30),
        min_pixels=config.get("min_pixels", 1000)
    )

    # Test callback
    def on_notification(source: str, details: dict):
        print(f"\n🔔 NOTIFICATION DETECTED!")
        print(f"   Source: {source}")
        print(f"   Details: {details}")
        print()

    # Start monitoring
    print(f"🔍 Monitoring window: {window_name}")
    print(f"📍 Region: {monitor.region_position} ({monitor.region_size[0]}x{monitor.region_size[1]})")
    print(f"🎨 Color: {config.get('teams_notification_color', '#464775')} (tolerance: {monitor.color_tolerance})")
    print(f"⏱️  Scan interval: {monitor.scan_interval}s")
    print()
    print("Press Ctrl+C to stop...")
    print()

    monitor.start(callback=on_notification)


if __name__ == "__main__":
    main()

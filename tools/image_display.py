
#!/usr/bin/env python3
"""
Display images on CRT TV
"""

import serial
import time
import sys
from PIL import Image
import os
from concurrent.futures import ThreadPoolExecutor
from queue import Queue

# Try to import matplotlib for preview
try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

class ImageDisplay:
    def __init__(self, port='/dev/cu.usbserial-120'):
        self.ser = serial.Serial(port, 115200, timeout=0.1)
        time.sleep(2)
        print("Connected to ESP32")

        # Per-color brightness multipliers (adjust these to change color intensity)
        self.color_brightness = {
            0: 1.1,       # Medium Gray (brighter for dark tones)
            1: 1.3,      # Green (dark)
            2: 0.65,      # Yellow (fallback)
            5: 0.60,       # Dark Red
            9: 0.85,       # Dark Blue (fallback)
            10: 0.50,      # Cyan
            12: 0.30,      # Light Green
            15: 0.35,      # Brown/Tan
            16: 0.85,      # Light Gray
            20: 0.75,     # Red
            30: 0.75,      # Yellow (brighter)
            32: 1.2,      # Dark Gray
            34: 0.03,      # Tan (extremely dark yellow)
            35: 0.60,      # Orange
            64: 1.0,      # White
            90: 0.50,      # Cyan (light blue)
            165: 0.65,     # Pink (brighter)
            200: 0.75,    # Blue (darker)
            230: 0.2,    # Purple
        }

    def send_command(self, cmd):
        self.ser.write((cmd + '\n').encode())
        try:
            response = self.ser.readline().decode().strip()
            return response
        except:
            return "OK"

    def apply_color_brightness(self, hue, brightness_val):
        """Apply per-color brightness multiplier"""
        if hue in self.color_brightness:
            brightness_val = int(brightness_val * self.color_brightness[hue])
        return (hue, brightness_val)

    def process_row(self, row_data):
        """Process a single image row (for parallel processing)"""
        y, pixels_row, offset_x, offset_y, pixel_size = row_data
        row_squares = []
        for x, (r, g, b) in enumerate(pixels_row):
            hue, brightness = self.rgb_to_hue(r, g, b)
            screen_x = offset_x + x * pixel_size
            screen_y = offset_y + y * pixel_size
            row_squares.append((screen_x, screen_y, pixel_size, hue, brightness))
        return row_squares

    def rgb_to_hue(self, r, g, b):
        """Convert RGB to closest hue in our color space"""
        brightness = (r + g + b) // 3

        # Map brightness to 0-255 scale (stepped for better color control)
        if brightness < 1:
            brightness_val = 2
        elif brightness < 3:
            brightness_val = 4
        elif brightness < 10:
            brightness_val = 10
        elif brightness < 15:
            brightness_val = 14
        elif brightness < 20:
            brightness_val = 18
        elif brightness < 25:
            brightness_val = 22
        elif brightness < 40:
            brightness_val = 20
        elif brightness < 50:
            brightness_val = 26
        elif brightness < 60:
            brightness_val = 30
        elif brightness < 75:
            brightness_val = 36
        elif brightness < 90:
            brightness_val = 42
        elif brightness < 100:
            brightness_val = 52
        elif brightness < 112:
            brightness_val = 60
        elif brightness < 125:
            brightness_val = 68
        elif brightness < 137:
            brightness_val = 76
        elif brightness < 150:
            brightness_val = 84
        elif brightness < 162:
            brightness_val = 78
        elif brightness < 175:
            brightness_val = 84
        elif brightness < 180:
            brightness_val = 90
        elif brightness < 185:
            brightness_val = 96
        elif brightness < 190:
            brightness_val = 104
        elif brightness < 195:
            brightness_val = 112
        else:
            brightness_val = 120

        # Check if grayscale (white/gray/black) - strict but allow light grays
        if abs(int(r) - int(g)) < 15 and abs(int(g) - int(b)) < 15 and abs(int(r) - int(b)) < 15:
            # Split into gray/white ranges for independent brightness control
            if brightness < 80:
                return self.apply_color_brightness(32, brightness_val)  # Dark gray (hue 32)
            elif brightness < 170:
                return self.apply_color_brightness(0, brightness_val)   # Medium gray (hue 0)
            elif brightness < 200:
                return self.apply_color_brightness(16, brightness_val)  # Light gray (hue 16)
            else:
                return self.apply_color_brightness(64, brightness_val)  # White (hue 64)

        # Pick color based on dominant channel
        max_val = max(r, g, b)

        # Check for green FIRST (split light and dark)
        if g > 30 and g > r and g > b and (g - r) > 3:
            # Light green if brightness is high, dark green if low
            if brightness > 120:
                return self.apply_color_brightness(12, brightness_val)  # Light green
            else:
                return self.apply_color_brightness(1, brightness_val)  # Dark green

        # Check for yellow (R and G very balanced, low B - exclude greens)
        if r > 100 and g > 100 and b < 110 and abs(int(r) - int(g)) < 15:
            return self.apply_color_brightness(30, brightness_val)

        # Check for orange (R much higher than G, warm tone, very low B)
        if r > 110 and g > 50 and g < 110 and b < 80 and (r - g) > 40:
            return self.apply_color_brightness(35, brightness_val)

        # Check for tan (moderate red, low green diff, low blue)
        if r > 90 and g > 50 and g < 100 and b < 80 and (r - g) > 5 and (r - g) < 50:
            return self.apply_color_brightness(34, brightness_val)

        # Check for magenta/pink (map pink tones to hue 165) - strict to avoid over-matching
        if r > 100 and b > 120 and g < 80 and abs(int(r) - int(b)) < 50:
            return self.apply_color_brightness(165, brightness_val)

        # Check for cyan (high G and B, low R)
        if g > 100 and b > 100 and r < 100 and abs(int(g) - int(b)) < 60:
            return self.apply_color_brightness(10, brightness_val)

        # Check for purple (B > R, high B, low G)
        if b > 100 and r > 60 and r < b and g < 80 and abs(int(b) - int(r)) < 60:
            return self.apply_color_brightness(230, brightness_val)

        # Check for red (R dominant, very low G to exclude browns)
        if r > 80 and g < 60 and b < 100 and r > g and r > b:
            return self.apply_color_brightness(20, brightness_val)

        if max_val == r and r > g and r > b:  # Red dominant (fallback)
            return self.apply_color_brightness(5, brightness_val)
        elif max_val == b and b > r and b > g:  # Blue dominant
            return self.apply_color_brightness(200, brightness_val)
        else:  # Default to grayscale (no green fallback - tan takes priority)
            return self.apply_color_brightness(0, brightness_val)

    def display_image(self, image_path, pixel_size=4):
        """Display image on TV (pixel_size = block size for performance)"""
        try:
            img = Image.open(image_path)
            print(f"Loaded: {image_path}")

            # Resize to fit screen (320x240)
            img.thumbnail((320 // pixel_size, 240 // pixel_size), Image.Resampling.LANCZOS)
            img = img.convert('RGB')

            width, height = img.size
            pixels = img.load()

            print(f"Displaying {width}x{height} image (may take a moment)...")

            # Clear screen first
            self.send_command("CLEAR")
            time.sleep(0.2)

            print("Collecting pixels...")

            # Calculate centering offset
            image_width = width * pixel_size
            image_height = height * pixel_size
            offset_x = (320 - image_width) // 2
            offset_y = (240 - image_height) // 2

            # Collect all squares using parallel row processing
            print("Processing image (parallel)...")
            squares = []
            row_data = []
            for y in range(height):
                pixels_row = [pixels[x, y] for x in range(width)]
                row_data.append((y, pixels_row, offset_x, offset_y, pixel_size))

            # Process rows in parallel (4 threads)
            with ThreadPoolExecutor(max_workers=4) as executor:
                for row_squares in executor.map(self.process_row, row_data):
                    squares.extend(row_squares)

            print(f"Sending {len(squares)} squares to ESP32...")
            print("(Rendering...)")

            # DON'T send COLOR - it clears squares!
            # Send squares using relative coordinates (batched for speed)
            last_x, last_y = 0, 0
            batch_size = 20
            batch = []

            for i, (sx, sy, sz, h, b) in enumerate(squares):
                dx = sx - last_x  # Delta X
                dy = sy - last_y  # Delta Y
                batch.append(f"RSQUARE:{dx}:{dy}:{sz}:{h}:{b}")
                last_x, last_y = sx, sy

                # Send batch when full or at end
                if len(batch) >= batch_size or i == len(squares) - 1:
                    batch_cmd = '\n'.join(batch) + '\n'
                    self.ser.write(batch_cmd.encode())
                    time.sleep(0.01)  # Small delay for ESP32 to process
                    # Read all responses
                    for _ in range(len(batch)):
                        try:
                            self.ser.readline()
                        except:
                            pass
                    batch = []

                    if (i + 1) % 500 == 0:
                        pct = 100 * (i + 1) // len(squares)
                        print(f"  {i+1}/{len(squares)} ({pct}%)")

            print("Done!")

        except FileNotFoundError:
            print(f"Image not found: {image_path}")
        except Exception as e:
            print(f"Error: {e}")

    def preview_image(self, image_path, pixel_size=4):
        """Show preview of how image will render on TV"""
        if not HAS_MATPLOTLIB:
            print("Error: matplotlib not installed. Install with: pip3 install matplotlib")
            return

        try:
            img = Image.open(image_path)
            print(f"Loading: {image_path}")

            # Debug: Check what hues are detected
            print("\nColor detection test:")
            test_colors = {
                "Pure Orange": (255, 165, 0),
                "Orange": (220, 140, 60),
                "Yellow": (255, 255, 0),
                "Red": (255, 0, 0),
                "Green": (0, 255, 0),
            }
            for name, (r, g, b) in test_colors.items():
                hue, brightness = self.rgb_to_hue(r, g, b)
                print(f"  {name} RGB({r},{g},{b}) → Hue {hue}")

            # Resize to fit screen
            img.thumbnail((320 // pixel_size, 240 // pixel_size), Image.Resampling.LANCZOS)
            img = img.convert('RGB')

            width, height = img.size
            pixels = img.load()

            # Create preview image showing mapped colors
            preview = Image.new('RGB', (width, height))
            preview_pixels = preview.load()

            # Map each pixel to TV color
            hue_to_rgb = {
                0: (128, 128, 128),  # Medium Gray
                1: (0, 200, 0),      # Green
                2: (255, 255, 0),    # Yellow (fallback)
                5: (150, 0, 0),      # Dark Red (fallback)
                9: (0, 50, 255),     # Dark Blue (fallback)
                15: (139, 69, 19),   # Brown
                16: (200, 200, 200), # Light Gray
                20: (200, 0, 0),     # Red
                30: (255, 255, 0),   # Yellow (vibrant)
                32: (64, 64, 64),    # Dark Gray
                35: (255, 140, 0),   # Orange
                64: (255, 255, 255), # White
                90: (0, 255, 255),   # Cyan
                165: (255, 0, 255),  # Magenta
                180: (255, 140, 0),  # Orange (fallback)
                200: (0, 100, 255),  # Blue
                230: (128, 0, 255),  # Purple
            }

            for y in range(height):
                for x in range(width):
                    r, g, b = pixels[x, y]
                    hue, brightness = self.rgb_to_hue(r, g, b)

                    # Get approximate RGB for this hue
                    base_rgb = hue_to_rgb.get(hue, (100, 100, 100))

                    # Scale by brightness
                    brightness_scale = brightness / 100.0
                    mapped_rgb = tuple(int(c * brightness_scale) for c in base_rgb)
                    preview_pixels[x, y] = mapped_rgb

            # Display both original and mapped
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

            ax1.imshow(img)
            ax1.set_title("Original Image")
            ax1.axis('off')

            ax2.imshow(preview)
            ax2.set_title("TV Color Map")
            ax2.axis('off')

            plt.tight_layout()
            plt.show()

        except FileNotFoundError:
            print(f"Image not found: {image_path}")
        except Exception as e:
            print(f"Error: {e}")

    def close(self):
        self.ser.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 image_display.py <image_file> [options]")
        print("Options:")
        print("  --preview [pixel_size]  - Show preview on computer (default pixel_size=4)")
        print("  [pixel_size]            - Send to TV (default pixel_size=4)")
        print("Examples:")
        print("  python3 image_display.py photo.jpg --preview")
        print("  python3 image_display.py photo.jpg --preview 8")
        print("  python3 image_display.py photo.jpg 4")
        sys.exit(1)

    image_file = sys.argv[1]
    pixel_size = 4
    show_preview = False

    # Check for preview option
    if len(sys.argv) > 2:
        if sys.argv[2] == "--preview":
            show_preview = True
            if len(sys.argv) > 3:
                try:
                    pixel_size = int(sys.argv[3])
                except ValueError:
                    pixel_size = 4
        else:
            try:
                pixel_size = int(sys.argv[2])
            except ValueError:
                pixel_size = 4

    if show_preview:
        display = ImageDisplay()
        display.preview_image(image_file, pixel_size=pixel_size)
        display.close()
        sys.exit(0)

    # Send to TV
    display = ImageDisplay()
    display.display_image(image_file, pixel_size=pixel_size)
    display.close()

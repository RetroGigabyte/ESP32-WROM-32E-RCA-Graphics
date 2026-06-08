#!/usr/bin/env python3
"""
Convert images to ESP32 raw RGB format (320x240, 3 bytes per pixel)
Usage: python3 image_converter.py input.jpg output.raw
"""

import sys
import os
from PIL import Image

def convert_image_to_raw_rgb(input_path, output_path):
    """Convert image to raw RGB format for ESP32"""

    try:
        # Open and convert image
        img = Image.open(input_path)
        print(f"✓ Opened: {input_path}")
        print(f"  Original size: {img.size}")

        # Convert to RGB if needed
        if img.mode != 'RGB':
            img = img.convert('RGB')
            print(f"✓ Converted to RGB")

        # Resize to 320x240
        img = img.resize((320, 240), Image.Resampling.LANCZOS)
        print(f"✓ Resized to 320x240")

        # Get raw pixel data
        pixels = img.tobytes()

        # Write raw RGB data
        with open(output_path, 'wb') as f:
            f.write(pixels)

        file_size = os.path.getsize(output_path)
        print(f"✓ Saved: {output_path}")
        print(f"  File size: {file_size} bytes (expected: 230,400)")

        if file_size == 230400:
            print("✓ Perfect size!")
        else:
            print(f"⚠ Warning: Expected 230,400 bytes, got {file_size}")

        return True

    except FileNotFoundError:
        print(f"❌ Error: Input file not found: {input_path}")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 image_converter.py input_image output.raw")
        print("\nExample:")
        print("  python3 image_converter.py photo.jpg image.raw")
        print("\nThen copy image.raw to your SD card root directory")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    print("=== ESP32 Image Converter ===")
    print(f"Input:  {input_file}")
    print(f"Output: {output_file}")
    print()

    if convert_image_to_raw_rgb(input_file, output_file):
        print("\n✓ Conversion successful!")
        print("Next steps:")
        print("1. Copy the .raw file to your SD card root directory")
        print("2. Insert SD card into your ESP32 kit")
        print("3. The image will display on your CRT!")
    else:
        print("\n❌ Conversion failed")
        sys.exit(1)

if __name__ == '__main__':
    main()

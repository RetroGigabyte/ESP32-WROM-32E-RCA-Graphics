# ESP32-WROM-32E RCA Graphics

> **AI Disclaimer:** This project was developed with the assistance of Claude AI. We believe AI-written code should be open source to benefit the community and maintain transparency.

A high-performance CRT TV display system using ESP32 and composite NTSC video output. Render images, gradients, and animations directly to vintage composite video displays.

## Features

- **320×240 composite NTSC video output** via RCA jack
- **True color rendering** with optimized hue palette for NTSC
- **Fast image rendering** with parallel processing and serial batching
- **Python control** over serial (115200 baud)
- **Up to 12,250 drawable squares** in memory
- **Configurable brightness levels** per color for accurate TV display

## Hardware Setup

See [SETUP.md](SETUP.md) for detailed hardware assembly and software installation.

### Quick Schematic

```
ESP32 Pin 25  ──────> RCA Video Out (yellow)
ESP32 GND     ──────> RCA Ground (black)
```

### Display Compatibility

**Best on CRT TVs** - This project is optimized for CRT displays with composite video inputs. CRTs naturally handle analog composite signals with excellent color accuracy and minimal artifacts.

**On LCD displays** - LCDs with composite inputs will work but may appear fuzzy due to analog-to-digital conversion and upscaling. This is a limitation of composite video on modern digital displays, not the project. For crisp results, use a CRT TV.

## Quick Start

### 1. Compile and Upload Firmware

```bash
# Build and upload to ESP32
platformio run -t upload -p /dev/cu.usbserial-120

# Monitor serial output
platformio device monitor -p /dev/cu.usbserial-120
```

### 2. Display an Image

```bash
# Send image to TV (4×4 pixel blocks for performance)
python3 tools/image_display.py samples/photo.jpg 4

# With preview of how it will look
python3 tools/image_display.py samples/photo.jpg --preview 4
```

### 3. Set Solid Color

```bash
# White screen
python3 tools/tv_control.py 64 200

# Dark screen
python3 tools/tv_control.py 0 50
```

## Color Palette

The system uses a specialized palette optimized for NTSC composite video:

| Hue | Color | Description | Best Brightness |
|-----|-------|-------------|-----------------|
| 0 | Medium Gray | Neutral gray | 50-150 |
| 1 | Dark Green | Forest green | 30-80 |
| 5 | Dark Red | Maroon | 10-50 |
| 10 | Cyan | Light blue | 50-120 |
| 12 | Light Green | Bright green | 80-150 |
| 15 | Brown/Tan | Warm brown | 30-90 |
| 16 | Light Gray | Off-white | 100-200 |
| 20 | Red | Bright red | 60-150 |
| 30 | Yellow | Golden yellow | 80-180 |
| 32 | Dark Gray | Charcoal | 20-80 |
| 34 | Tan | Light brown | 10-40 |
| 35 | Orange | Warm orange | 60-150 |
| 64 | White | Pure white | 150-255 |
| 90 | Cyan (light) | Sky blue | 100-200 |
| 165 | Pink | Magenta-pink | 80-150 |
| 200 | Blue (dark) | Deep blue | 60-150 |
| 230 | Purple | Magenta-purple | 40-120 |

See [COLOR_PALETTE.md](COLOR_PALETTE.md) for detailed color testing notes.

## Tools

### `image_display.py`

Display images on the TV with automatic color conversion.

```bash
# Basic usage
python3 tools/image_display.py <image_file> [pixel_size]

# With preview
python3 tools/image_display.py <image_file> --preview [pixel_size]

# Example: 4×4 pixel blocks
python3 tools/image_display.py samples/photo.jpg 4

# Example: 8×8 pixel blocks (fewer squares, faster)
python3 tools/image_display.py samples/photo.jpg 8
```

**Features:**
- Automatic RGB → Hue conversion
- Parallel row processing (4 threads)
- Batched serial commands for speed
- Preview mode to see how colors will map

### `tv_control.py`

Direct control of the TV display.

```bash
# Set background color (hue brightness)
python3 tools/tv_control.py 64 200    # White
python3 tools/tv_control.py 5 30      # Dark red
python3 tools/tv_control.py 1 80      # Dark green

# Color gradient animation
python3 tools/tv_control.py gradient 0.05

# Interactive mode
python3 tools/tv_control.py
```

### `image_converter.py`

Convert images to raw RGB format for SD card storage.

```bash
python3 tools/image_converter.py <input_image> <output_file.raw>
```

## Performance Notes

- **MAX_SQUARES = 12,250** objects maximum (memory limited by graphics framebuffer at 77KB)
- **Pixel batching** recommended for images (4×4 or 8×8 blocks reduce square count)
- **Serial speed** optimized at 115200 baud with command batching (20 per batch)
- **Rendering time** ~1-3 seconds for typical 320×240 images depending on pixel size

## Project Structure

```
esp32-master-system/
├── src/
│   ├── test_pattern.ino          # Main ESP32 firmware
│   ├── video_out.h               # Composite video driver
│   ├── ir_input.h                # IR receiver support
│   └── font6x8.h                 # Font data
├── lib_composite_color/          # Composite color library
├── lib_composite_color_rgb/      # Alternative RGB library
├── tools/
│   ├── image_display.py          # Image to TV tool
│   ├── tv_control.py             # Direct control tool
│   └── image_converter.py        # Raw image converter
├── samples/                      # Test/sample images
├── archive/
│   ├── img/                      # Reference images & diagrams
│   ├── esp32-nesemu/             # Old NES emulator project
│   └── *.bak, disabled_code/     # Backup files & old code
├── COLOR_PALETTE.md              # Color reference & testing
├── README.md                     # This file
├── SETUP.md                      # Hardware & software setup
└── platformio.ini                # Build configuration
```

## Troubleshooting

**No video output:**
- Verify RCA cable is connected to pin 25
- Check TV is on composite input (not HDMI)
- Try `python3 tools/tv_control.py 64 200` for a white test screen

**Colors look wrong:**
- Different TV models may display colors slightly differently
- Use `--preview` flag with image_display.py to test before sending
- Refer to COLOR_PALETTE.md for brightness recommendations
- Try adjusting brightness multipliers in image_display.py

**Image rendering too slow:**
- Increase pixel_size (e.g., `8` instead of `4`)
- This reduces the number of squares sent to the ESP32
- Trade-off: lower resolution but faster rendering

**Serial connection issues:**
- Update port in tools/*.py files (default: `/dev/cu.usbserial-120`)
- Check USB cable is a data cable, not charge-only
- Verify ESP32 drivers installed on your system

## Development

### Modifying Color Detection

Edit the `rgb_to_hue()` function in `tools/image_display.py` to adjust color mapping for your specific TV.

### Adjusting Brightness Multipliers

The `color_brightness` dictionary in `image_display.py` applies per-color brightness scaling:

```python
self.color_brightness = {
    0: 1.1,    # Medium Gray
    1: 1.3,    # Dark Green
    # ... etc
}
```

Higher values = brighter colors on your TV.

## Inspired By

Built with gratitude for:

- **[Bitluni](https://bitluni.net/)** - [ESP32CompositeVideo](https://github.com/bitluni/ESP32CompositeVideo) - pioneering ESP32 composite video output
- **[Peter Barrett (rossumur)](https://github.com/rossumur)** - [ESP_8_BIT](https://github.com/rossumur/esp_8_bit) - APLL-based stable NTSC video synchronization
- **[Marcio Teixeira (marciot)](https://github.com/marciot)** - [ESP32CompositeColorVideo](https://github.com/marciot/ESP32CompositeColorVideo) - library package and color support

Their open-source work made this project possible.

## References

- [CompositeGraphics Library](lib_composite_color/)
- [Technical Reference Images](archive/img/) - Oscilloscope captures and technical diagrams
- [ESP32 Datasheet](https://www.espressif.com/sites/default/files/documentation/esp32_datasheet_en.pdf)
- [NTSC Video Standard](https://en.wikipedia.org/wiki/NTSC)

## License

Open source - modify and use as needed.

---

**Status:** Stable and tested. MAX_SQUARES: 12,250 | Video: NTSC 320×240 | Baud: 115200

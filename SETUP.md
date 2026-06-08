# ESP32-WROM-32E RCA Graphics - Setup Guide

Complete guide for hardware assembly and software installation.

## Hardware Requirements

### Components

- **ESP32** (e.g., ESP32-DevKit-V1, DOIT-DevKit)
- **USB-A to USB-Micro cable** (data cable for programming)
- **RCA cable** (yellow connector for video)
- **CRT TV or composite monitor** with RCA video input
- **Breadboard** and jumper wires (for prototyping)

### Optional Components

- IR receiver (TSOP4838 or TSOP38238) for IR remote control
- Perfboard or PCB for permanent installation
- 3.3V power supply for standalone operation

## Circuit Assembly

### Video Connection

```
ESP32              RCA Cable
Pin 25 ──────────────> Video (yellow)
Pin GND ──────────────> Ground (black)
```

### With IR Receiver (Optional)

```
ESP32
Pin 0  ─────> IR Receiver Input (TSOP4838/38238)
3.3V   ─────> IR Receiver Power
GND    ─────> IR Receiver Ground
```

## Software Setup

### 1. Install PlatformIO

```bash
# Install VS Code extension
# Or via pip
pip3 install platformio

# Verify installation
platformio --version
```

### 2. Install ESP32 Board Drivers

```bash
# macOS (using Homebrew)
brew install ch340g-macos-driver

# Or download drivers
# - CH340G: https://github.com/macos-art/ch340g-driver
# - CP2102: https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers
```

### 3. Clone/Setup Project

```bash
# Navigate to project
cd /Users/Apple/Documents/dev/esp32-master-system

# Verify structure
ls -la
# Should see: src/, lib_composite_color/, platformio.ini, etc.
```

### 4. Identify USB Port

```bash
# List available serial ports
ls /dev/cu.* /dev/tty.*

# Common patterns:
# - /dev/cu.usbserial-120 (CH340G)
# - /dev/cu.SLAB_USBtoUART (CP2102)
```

### 5. Update Serial Port Configuration

Edit `platformio.ini`:

```ini
[env:esp32dev]
upload_port = /dev/cu.usbserial-120    # ← Update this to your port
monitor_port = /dev/cu.usbserial-120   # ← Update this too
```

Or in tools/*.py files:

```python
# Default in image_display.py and tv_control.py
self.ser = serial.Serial(port='/dev/cu.usbserial-120', ...)
```

### 6. Compile and Upload Firmware

```bash
# Option 1: PlatformIO CLI
platformio run -t upload -p /dev/cu.usbserial-120

# Option 2: VS Code
# 1. Open src/test_pattern.ino
# 2. Click "Upload" button (→ icon)

# Monitor serial output
platformio device monitor -p /dev/cu.usbserial-120
```

### 7. Install Python Dependencies

```bash
# Python 3.8+ required
python3 --version

# Install required packages
pip3 install pyserial pillow

# Optional: For image preview
pip3 install matplotlib
```

### 8. Verify Connection

```bash
# Test basic color control
python3 tools/tv_control.py 64 200

# Should display white screen on TV
# If nothing appears, check:
# 1. RCA cable connected correctly
# 2. TV on composite input
# 3. Serial port correct in tools/*.py
```

## Troubleshooting

### Upload Fails: "No module named 'serial'"

```bash
pip3 install pyserial
```

### USB Port Not Recognized

**macOS:**
```bash
# Check if driver installed
kextstat | grep -i ch340

# Restart system to load driver
```

**Common Ports:**
```bash
# List all serial devices
ls -la /dev/cu.*
ls -la /dev/tty.*

# If empty, drivers not installed
```

### Serial Connection Timeout

```bash
# Verify port is correct
# Test with screen
screen /dev/cu.usbserial-120 115200

# Exit with Ctrl+A then X
```

### Firmware Compiles but Won't Upload

```bash
# Try holding BOOT button while uploading
# Or use Manual Upload Mode:
platformio run -t upload --upload-port /dev/cu.usbserial-120

# Check ESP32 is powered
# Try different USB cable
```

### No Video Output

1. **Check connections:**
   ```bash
   # Verify pin 25 is connected to RCA yellow
   # Verify GND is connected to RCA black
   ```

2. **Test with white screen:**
   ```bash
   python3 tools/tv_control.py 64 200
   ```

3. **Monitor serial output:**
   ```bash
   platformio device monitor -p /dev/cu.usbserial-120
   # Should show "Ready!" after boot
   ```

4. **Check TV input:**
   - Ensure TV is on composite/video input (not HDMI)
   - Try different TV if possible
   - Verify RCA cable works with other devices

### Python Connection Fails

```bash
# Check port is accessible
ls -la /dev/cu.usbserial-120

# Give current user permission
sudo chown $(whoami):staff /dev/cu.usbserial-120

# Test connection
python3 -c "import serial; s = serial.Serial('/dev/cu.usbserial-120', 115200); print('OK')"
```

## First Run Checklist

- [ ] USB cable connected (data cable, not charge-only)
- [ ] ESP32 powered
- [ ] RCA video cable from pin 25 → TV yellow input
- [ ] GND connected from ESP32 → RCA black
- [ ] TV set to composite/video input
- [ ] Serial port identified and configured
- [ ] Firmware uploaded successfully
- [ ] Serial monitor shows "Ready!"
- [ ] Python can detect serial port
- [ ] `python3 tools/tv_control.py 64 200` displays white on TV

## Performance Tuning

### Serial Port Speed

The system is optimized for 115200 baud. Higher speeds may cause data loss on longer cables.

```python
# In tools/*.py
self.ser = serial.Serial(port, 115200, timeout=0.1)
```

### Parallel Processing

Image processing uses 4 worker threads. Adjust in `tools/image_display.py`:

```python
with ThreadPoolExecutor(max_workers=4) as executor:  # ← Change this
    for row_squares in executor.map(self.process_row, row_data):
        squares.extend(row_squares)
```

### Serial Command Batching

Commands are batched in groups of 20 for speed. Adjust in `tools/image_display.py`:

```python
batch_size = 20  # ← Increase for faster, but higher CPU load
                 # ← Decrease if serial errors occur
```

## Development Mode

For active development on the firmware:

```bash
# Watch for changes and auto-upload
platformio run -t upload --upload-port /dev/cu.usbserial-120 -w

# Continuous serial monitoring
platformio device monitor -p /dev/cu.usbserial-120 --baud 115200
```

## Next Steps

1. **Display test image:**
   ```bash
   python3 tools/image_display.py samples/photo.jpg 4
   ```

2. **Explore color palette:**
   ```bash
   cat COLOR_PALETTE.md
   ```

3. **Customize colors:**
   - Edit color_brightness in `tools/image_display.py`
   - Test with `--preview` flag
   - Adjust for your TV model

4. **Modify firmware:**
   - See comments in `src/test_pattern.ino`
   - Adjust MAX_SQUARES or color detection
   - Recompile and upload

## Support

- Check `README.md` for general troubleshooting
- Check serial monitor output: `platformio device monitor`
- Verify all connections match the circuit diagram
- Try test images in `samples/` folder

---

**Last Updated:** June 2026 | Status: Stable

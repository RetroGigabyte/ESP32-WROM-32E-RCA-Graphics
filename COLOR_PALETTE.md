# ESP32 CRT TV Color Palette Reference

**System:** NTSC Composite Video via CompositeGraphics library

## Grayscale Palette

| Hue | Brightness | Display |
|-----|-----------|---------|
| 0 | 30 | Medium Gray |
| 0 | 80 | Very Light Gray |
| 16 | 30 | Dark Gray (variant 2) |
| 16 | 80 | Light Gray (variant 2) |
| 32 | 30 | Dark Gray (variant 3) |
| 32 | 80 | Light Gray (variant 3) |
| 64 | 100 | White |

## Color Palette

| Hue | Brightness | Display | Notes |
|-----|-----------|---------|-------|
| 1 | 20 | Dark Green | Pure dark green |
| 1 | 25 | Dark Cactus Green | Medium-dark green |
| 1 | 50 | Light Lime Green | Bright green |
| 20 | 30 | Tan Red | Reddish-tan |
| 30 | 50 | Banana Yellow | Bright yellow |
| 35 | 30 | Dark Orange | Saturated orange |
| 90 | 30 | Light Blue | Cyan/light blue |
| 165 | 30 | Pink/Magenta | Magenta tones |
| 200 | 30 | Dark Blue | Deep blue |
| 230 | 30 | Purple | Purple tones |

## Current Color Detection & Brightness Multipliers

```python
color_brightness = {
    0: 1.0,       # Medium Gray
    1: 1.10,      # Green (darker)
    2: 0.85,      # Yellow (fallback)
    5: 0.90,      # Dark Red
    9: 0.80,      # Dark Blue (fallback)
    16: 1.0,      # Light Gray
    20: 0.75,     # Red (tan-red)
    30: 1.0,      # Yellow (vibrant)
    32: 1.0,      # Dark Gray
    35: 0.6,      # Orange (darker = more saturated)
    64: 1.0,      # White
    90: 0.9,      # Cyan (light blue)
    165: 0.8,     # Magenta (pink)
    200: 0.55,    # Blue (darker)
    230: 0.5,     # Purple
}
```

## Detection Thresholds

- **Yellow:** R>110, G>110, B<100, |R-G|<30
- **Orange:** R>120, G>60-100, B<70, (R-G)>50
- **Cyan:** G>100, B>100, R<100, |G-B|<60
- **Purple:** B>100, R>60, R<B, G<80, |B-R|<60
- **Magenta:** R>150, B>150, G<40, |R-B|<20
- **Red:** R>80, G<100, B<100, R>G, R>B
- **Green:** G dominant
- **Blue:** B dominant

## Testing Notes

- Hue 90 displays as light blue (not magenta)
- Hue 165 displays as pink/magenta (not cyan)
- Brightness values should be tuned per color for best saturation
- Lower brightness = more saturated colors
- Higher brightness = washed out but lighter colors

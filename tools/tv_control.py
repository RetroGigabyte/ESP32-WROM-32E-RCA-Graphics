#!/usr/bin/env python3
"""
Control ESP32 composite video display colors from Python
"""

import serial
import time
import sys

class TVController:
    def __init__(self, port='/dev/cu.usbserial-120', baud=115200):
        self.ser = serial.Serial(port, baud, timeout=1)
        time.sleep(2)
        print(f"Connected to {port}")

    def send_command(self, cmd):
        """Send command to ESP32"""
        self.ser.write((cmd + '\n').encode())
        response = self.ser.readline().decode().strip()
        return response

    def set_color(self, hue, brightness):
        """Set color (hue 0-360, brightness 0-255)"""
        cmd = f"COLOR:{hue}:{brightness}"
        return self.send_command(cmd)

    def draw_square(self, x, y, size, hue, brightness):
        """Draw a colored square"""
        cmd = f"SQUARE:{x}:{y}:{size}:{hue}:{brightness}"
        return self.send_command(cmd)

    def draw_squares(self, squares):
        """Draw multiple squares: [(x,y,size,hue,brightness), ...]"""
        for square in squares:
            x, y, size, hue, brightness = square
            self.draw_square(x, y, size, hue, brightness)

    def demo(self):
        """Color demo"""
        print("Running color demo...")
        for hue in range(0, 360, 30):
            print(f"Hue: {hue}")
            self.set_color(hue, 200)
            time.sleep(0.5)
        print("Done!")

    def gradient(self, speed=0.05):
        """Smooth color gradient with brightness 1-10"""
        print("Smooth gradient brightness 1-10 (press Ctrl+C to stop)...")
        try:
            while True:
                # Cycle through hue 1-10 with brightness 1-10
                for hue in range(1, 11):
                    for brightness in range(1, 11):
                        self.set_color(hue, brightness)
                        time.sleep(speed)
                    for brightness in range(10, 0, -1):
                        self.set_color(hue, brightness)
                        time.sleep(speed)
        except KeyboardInterrupt:
            print("\nStopped")

    def close(self):
        self.ser.close()

if __name__ == "__main__":
    try:
        tv = TVController()

        if len(sys.argv) > 1:
            cmd = sys.argv[1].lower()
            if cmd == "gradient":
                speed = float(sys.argv[2]) if len(sys.argv) > 2 else 0.05
                tv.gradient(speed=speed)
            elif cmd == "demo":
                tv.demo()
            elif cmd == "square":
                # Format: square x y size hue brightness [x y size hue brightness ...]
                if len(sys.argv) >= 7:
                    squares = []
                    i = 2
                    while i + 4 < len(sys.argv):
                        x = int(sys.argv[i])
                        y = int(sys.argv[i+1])
                        size = int(sys.argv[i+2])
                        hue = int(sys.argv[i+3])
                        brightness = int(sys.argv[i+4])
                        squares.append((x, y, size, hue, brightness))
                        i += 5
                    tv.draw_squares(squares)
                    print(f"Drew {len(squares)} square(s)")
                else:
                    print("Usage: python3 tv_control.py square <x> <y> <size> <hue> <brightness> [x y size hue brightness ...]")
            else:
                # Parse color from command line: hue brightness
                try:
                    hue = int(sys.argv[1])
                    brightness = int(sys.argv[2]) if len(sys.argv) > 2 else 200
                    tv.set_color(hue, brightness)
                    print(f"Color: hue {hue}, brightness {brightness}")
                except:
                    print("Usage: python3 tv_control.py [gradient|demo|square|<hue> [brightness]]")
        else:
            # Interactive mode
            print("\n=== ESP32 Color Control ===")
            print("Commands:")
            print("  'hue brightness' - set color (e.g., 120 200)")
            print("  'gradient' - smooth color animation")
            print("  'demo' - step through colors")
            print("  'quit' - exit\n")

            while True:
                cmd = input("> ").strip()

                if cmd.lower() in ["quit", "exit"]:
                    break
                elif cmd.lower() == "gradient":
                    tv.gradient(speed=0.05)
                elif cmd.lower() == "demo":
                    tv.demo()
                else:
                    parts = cmd.split()
                    if len(parts) >= 1:
                        try:
                            hue = int(parts[0])
                            brightness = int(parts[1]) if len(parts) > 1 else 200
                            tv.set_color(hue, brightness)
                            print(f"OK: hue {hue}, brightness {brightness}")
                        except:
                            print("Usage: <hue 0-360> [brightness 0-255]")

        tv.close()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

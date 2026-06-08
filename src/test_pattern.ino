// ESP32-WROM-32E RCA Graphics - CRT TV Display System
#include "esp_pm.h"
#include "CompositeGraphics.h"
#include "CompositeColorOutput.h"
#include "font6x8.h"
#include <math.h>
#include <SD_MMC.h>

CompositeGraphics graphics(CompositeColorOutput::XRES, CompositeColorOutput::YRES);
CompositeColorOutput composite(CompositeColorOutput::NTSC);
Font<CompositeGraphics> font(6, 8, font6x8::pixels);

// 3D cube vertices
struct Vec3 {
    float x, y, z;
};

struct Vec2 {
    float x, y;
};

// Cube corners in 3D space
Vec3 cube_verts[8] = {
    {-1, -1, -1}, {1, -1, -1}, {1, 1, -1}, {-1, 1, -1},
    {-1, -1, 1},  {1, -1, 1},  {1, 1, 1},  {-1, 1, 1}
};

// Cube edges (vertex pairs)
int edges[12][2] = {
    {0,1}, {1,2}, {2,3}, {3,0},  // front face
    {4,5}, {5,6}, {6,7}, {7,4},  // back face
    {0,4}, {1,5}, {2,6}, {3,7}   // connecting edges
};

float rotX = 0, rotY = 0, rotZ = 0;
int frameCount = 0;

// Control variables
int controlMode = 0;  // 0=demo, 1=color
uint16_t controlHue = 0;
uint8_t controlBrightness = 200;

// SD Card image buffer
uint8_t* imageBuffer = NULL;
bool imageLoaded = false;

// Image filenames
const char* imageFiles[] = {
    "/image1.raw",
    "/image2.raw",
    "/image3.raw",
    "/image4.raw",
    "/image5.raw"
};
const int maxImages = 5;

// Rotation matrix multiplication
Vec3 rotate(Vec3 v, float rx, float ry, float rz) {
    Vec3 p = v;

    // Rotate around X
    float y = p.y * cos(rx) - p.z * sin(rx);
    float z = p.y * sin(rx) + p.z * cos(rx);
    p.y = y;
    p.z = z;

    // Rotate around Y
    float x = p.x * cos(ry) + p.z * sin(ry);
    z = -p.x * sin(ry) + p.z * cos(ry);
    p.x = x;
    p.z = z;

    // Rotate around Z
    x = p.x * cos(rz) - p.y * sin(rz);
    y = p.x * sin(rz) + p.y * cos(rz);
    p.x = x;
    p.y = y;

    return p;
}

// Project 3D point to 2D screen
Vec2 project(Vec3 p) {
    float scale = 100 / (p.z + 5);  // perspective
    Vec2 screen;
    screen.x = CompositeColorOutput::XRES / 2 + p.x * scale;
    screen.y = CompositeColorOutput::YRES / 2 - p.y * scale;
    return screen;
}

// Load RGB image from SD card
bool loadColorImageFromSD(const char* filename) {
    File file = SD_MMC.open(filename, FILE_READ);
    if (!file) {
        return false;
    }

    size_t imageSize = 320 * 240 * 3;
    if (imageBuffer == NULL) {
        imageBuffer = (uint8_t*)malloc(imageSize);
        if (imageBuffer == NULL) {
            file.close();
            return false;
        }
    }

    size_t bytesRead = file.read(imageBuffer, imageSize);
    file.close();

    return (bytesRead == imageSize);
}

// Draw RGB image from SD card
void drawColorImage() {
    if (!imageLoaded) {
        return;
    }

    uint8_t* src = imageBuffer;
    for (int y = 0; y < CompositeColorOutput::YRES; y++) {
        for (int x = 0; x < CompositeColorOutput::XRES; x++) {
            uint8_t r = *src++;
            uint8_t g = *src++;
            uint8_t b = *src++;

            int hue = 0;
            if (r > g && r > b) hue = 0;
            else if (g > r && g > b) hue = 120;
            else if (b > r && b > g) hue = 240;
            else if (r > 0 && g > 0) hue = 60;
            else if (g > 0 && b > 0) hue = 180;
            else if (r > 0 && b > 0) hue = 300;

            int brightness = (r + g + b) / 3;

            graphics.setHue(hue);
            graphics.dot(x, y, brightness);
        }
    }
}

void setup() {
    Serial.begin(115200);
    delay(1000);

    Serial.println("\n\n=== 3D Rotating Cube ===\n");

    esp_pm_lock_handle_t powerManagementLock;
    esp_pm_lock_create(ESP_PM_CPU_FREQ_MAX, 0, "videoLock", &powerManagementLock);
    esp_pm_lock_acquire(powerManagementLock);

    Serial.println("Initializing composite video...");
    composite.init();
    graphics.init();
    graphics.setFont(font);

    // Initialize SD card
    Serial.println("Initializing SD card...");
    if (SD_MMC.begin()) {
        Serial.println("SD card ready");
        if (loadColorImageFromSD("/image1.raw")) {
            imageLoaded = true;
            Serial.println("Images available!");
        }
    } else {
        Serial.println("SD card not available");
    }

    Serial.println("Ready!\n");
}

void drawGradient() {
    // NES 64-color palette gradient
    for (int x = 0; x < CompositeColorOutput::XRES; x++) {
        int hue = (x * 360) / CompositeColorOutput::XRES;
        graphics.setHue(hue);
        graphics.line(x, 0, x, CompositeColorOutput::YRES, 200);
    }
}

// Store multiple squares (for images) - optimized data types
const int MAX_SQUARES = 12250;  // Increased from 4900 with smaller struct
struct Square {
    uint16_t x, y, hue;  // 2 bytes each: x,y fit 0-320, hue fits 0-360
    uint8_t size, brightness;  // 1 byte each: both fit 0-255
};  // Total: 8 bytes per square (was 20)
Square squares[MAX_SQUARES];
int numSquares = 0;
int lastX = 0, lastY = 0;  // Track last position for relative coordinates

void handleSerialCommand() {
    // Process all available commands in buffer (batch handling)
    while (Serial.available()) {
        String cmd = Serial.readStringUntil('\n');
        cmd.trim();
        if (cmd.length() == 0) continue;

    if (cmd.startsWith("COLOR:")) {
        sscanf(cmd.c_str(), "COLOR:%d:%d", &controlHue, &controlBrightness);
        controlMode = 1;
        numSquares = 0;  // Clear squares when setting background
        Serial.println("OK");
    } else if (cmd.startsWith("RSQUARE:")) {
        // Format: RSQUARE:dx:dy:size:hue:brightness (relative coordinates)
        int dx, dy;
        uint8_t size, brightness;
        uint16_t hue;
        if (sscanf(cmd.c_str(), "RSQUARE:%d:%d:%hhu:%hu:%hhu", &dx, &dy, &size, &hue, &brightness) == 5) {
            if (numSquares < MAX_SQUARES) {
                squares[numSquares].x = lastX + dx;
                squares[numSquares].y = lastY + dy;
                squares[numSquares].size = size;
                squares[numSquares].hue = hue;
                squares[numSquares].brightness = brightness;
                lastX = squares[numSquares].x;
                lastY = squares[numSquares].y;
                numSquares++;
                controlMode = 1;
            }
        }
        Serial.println("OK");
    } else if (cmd.startsWith("SQUARE:")) {
        // Format: SQUARE:x:y:size:hue:brightness
        if (numSquares < MAX_SQUARES) {
            uint16_t x, y, hue;
            uint8_t size, brightness;
            sscanf(cmd.c_str(), "SQUARE:%hu:%hu:%hhu:%hu:%hhu",
                   &x, &y, &size, &hue, &brightness);
            squares[numSquares].x = x;
            squares[numSquares].y = y;
            squares[numSquares].size = size;
            squares[numSquares].hue = hue;
            squares[numSquares].brightness = brightness;
            lastX = x;
            lastY = y;
            numSquares++;
            controlMode = 1;
        }
        Serial.println("OK");
    } else if (cmd == "CLEAR" || cmd == "DEMO") {
        controlMode = 0;
        numSquares = 0;
        lastX = 0;
        lastY = 0;
        Serial.println("OK");
    } else {
        Serial.println("?");
    }
    }
}

void drawSolidColor() {
    graphics.setHue(controlHue);
    graphics.fillRect(0, 0, CompositeColorOutput::XRES, CompositeColorOutput::YRES, controlBrightness);

    // Draw all stored squares (with 4-pixel right, 2-pixel up offset)
    for (int i = 0; i < numSquares; i++) {
        graphics.setHue(squares[i].hue);
        graphics.fillRect(squares[i].x + 4, squares[i].y - 2, squares[i].size, squares[i].size, squares[i].brightness);
    }
}

void drawCube() {
    graphics.setHue(frameCount / 10);

    rotX += 0.02;
    rotY += 0.03;
    rotZ += 0.01;

    Vec2 projected[8];
    for (int i = 0; i < 8; i++) {
        Vec3 rotated = rotate(cube_verts[i], rotX, rotY, rotZ);
        projected[i] = project(rotated);
    }

    for (int i = 0; i < 12; i++) {
        int v1 = edges[i][0];
        int v2 = edges[i][1];
        int brightness = 50 + (i * 10) % 200;
        graphics.line((int)projected[v1].x, (int)projected[v1].y,
                     (int)projected[v2].x, (int)projected[v2].y, brightness);
    }

    for (int i = 0; i < 8; i++) {
        int x = (int)projected[i].x;
        int y = (int)projected[i].y;
        graphics.fillRect(x - 2, y - 2, 4, 4, 15);
    }

    graphics.setTextColor(255);

    // Top text
    int topX = (CompositeColorOutput::XRES / 2) - 50;
    int topY = 10;
    graphics.setCursor(topX, topY);
    graphics.print("Load program/image");

    // Bottom text
    int textX = (CompositeColorOutput::XRES / 2) - 40;
    int textY = CompositeColorOutput::YRES - 20;
    graphics.setCursor(textX, textY);
    graphics.print("Hello, World!");
}

void loop() {
    handleSerialCommand();

    graphics.begin(0);

    if (controlMode == 1 || controlMode == 2) {
        // Python control mode: solid color with optional text
        drawSolidColor();
    } else {
        // Demo mode: cycle through demos (cube and images only)
        int numModes = imageLoaded ? (1 + maxImages) : 1;
        int cycle = (frameCount / 300) % numModes;

        if (cycle == 0) {
            drawCube();
        } else if (imageLoaded && cycle >= 1) {
            int imgIdx = cycle - 1;
            if (imgIdx < maxImages) {
                loadColorImageFromSD(imageFiles[imgIdx]);
                drawColorImage();
            }
        }

        if (frameCount % 30 == 0) {
            if (cycle == 0) Serial.println("Cube");
            else if (imageLoaded) Serial.printf("Image %d\n", cycle);
        }
    }

    graphics.end();
    composite.sendFrameHalfResolution(&graphics.frame);

    frameCount++;
    delay(16);
}

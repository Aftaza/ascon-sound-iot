# Setup Guide - Audio Encryption System

Panduan lengkap untuk setup sistem enkripsi audio dengan ESP32 dan desktop subscriber.

## Table of Contents
- [Part 1: ESP32 Publisher Setup](#part-1-esp32-publisher-setup)
- [Part 2: Desktop Subscriber Setup](#part-2-desktop-subscriber-setup)
- [Part 3: ThingSpeak Configuration](#part-3-thingspeak-configuration)

---

## Part 1: ESP32 Publisher Setup

### 1.1 Hardware Preparation

**Required Components:**
- ESP32 DevKit board (atau ESP32-WROOM-32)
- KY-037 Sound Detection Sensor Module
- Breadboard dan jumper wires
- USB cable (micro-USB atau USB-C tergantung board)

**Wiring Diagram:**

```
KY-037          ESP32
------          -----
VCC     →→→     3.3V
GND     →→→     GND
A0      →→→     GPIO 34 (ADC1_CH6)
D0      →→→     (optional, not used)
```

> [!IMPORTANT]
> GPIO 34 adalah ADC1_CH6. Pastikan menggunakan ADC1 pins (GPIO 32-39) karena ADC2 tidak available saat WiFi active di ESP32.

### 1.2 Install MicroPython Firmware

**Step 1: Install esptool**
```bash
pip install esptool
```

**Step 2: Erase existing firmware**
```bash
# Windows
python -m esptool --port COM3 erase_flash

# Linux/Mac
python -m esptool --port /dev/ttyUSB0 erase_flash
```

**Step 3: Download MicroPython firmware**
- Download dari: https://micropython.org/download/esp32/
- Pilih **ESP32_GENERIC** (stable version)

**Step 4: Flash MicroPython**
```bash
# Windows
python -m esptool --chip esp32 --port COM3 write_flash -z 0x1000 esp32-*.bin

# Linux/Mac
python -m esptool --chip esp32 --port /dev/ttyUSB0 write_flash -z 0x1000 esp32-*.bin
```

**Step 5: Verify installation**
```bash
# Windows
python -m esptool --port COM3 flash_id

# Output should show chip info
```

### 1.3 Upload Files to ESP32

**Option A: Using ampy**
```bash
# Install ampy
pip install adafruit-ampy

# Upload ascon.py
ampy --port COM3 put ascon.py

# Upload Publisher.py
ampy --port COM3 put Publisher.py

# Verify files uploaded
ampy --port COM3 ls
```

**Option B: Using Thonny IDE**
1. Download [Thonny](https://thonny.org/)
2. Open Thonny → Tools → Options → Interpreter
3. Select "MicroPython (ESP32)" dan pilih COM port
4. Click "Open" → Navigate ke project folder
5. Right-click `ascon.py` → Upload to /
6. Right-click `Publisher.py` → Upload to /

### 1.4 Configure WiFi and ThingSpeak

**Edit `Publisher.py` pada ESP32:**

```python
# Update these lines in Publisher.py
WIFI_SSID = "YourWiFiName"
WIFI_PASSWORD = "YourWiFiPassword"

THINGSPEAK_CHANNEL_ID = "1234567"  # From ThingSpeak
MQTT_USER = "YourMQTTUsername"     # From ThingSpeak
MQTT_PASSWORD = "YourMQTTPassword" # From ThingSpeak
```

> [!WARNING]
> Pastikan WiFi network memiliki internet access. ESP32 tidak support WiFi 5GHz, gunakan 2.4GHz network.

### 1.5 Test ESP32 Publisher

**Connect to serial monitor:**
```bash
# Using screen (Linux/Mac)
screen /dev/ttyUSB0 115200

# Using putty (Windows)
# Set COM3, 115200 baud, connection type: Serial
```

**Expected output:**
```
Connecting to WiFi..... Connected!
IP Address: 192.168.1.100
Connecting to MQTT broker... Connected!

Tidak merekam
Waiting for trigger...
```

**Trigger recording** → ESP32 will auto-record or wait for button press

```
Sedang merekam: 1s
Sedang merekam: 2s
...
Sedang merekam: 10s
Recording complete!
Total samples: 80000
Preprocessing audio...
Chunking complete: 313 chunks
Encrypting chunk 1/313
Publishing chunk 1/313
...
All chunks published successfully!
Tidak merekam
```

---

## Part 2: Desktop Subscriber Setup

### 2.1 System Requirements

- **Operating System**: Windows 10/11, Linux (Ubuntu 20.04+), macOS 11+
- **Python**: 3.8 or higher
- **RAM**: Minimum 4GB
- **Storage**: 500MB free space

### 2.2 Verify Python Installation

```bash
python --version
# Output: Python 3.8.x or higher

pip --version
# Output: pip 21.x or higher
```

> [!TIP]
> Jika Python belum installed, download dari [python.org](https://www.python.org/downloads/)

### 2.3 Setup Virtual Environment (Recommended)

```bash
# Navigate to project directory
cd d:/Kuliahku/project/keamanan_informasi/ascon

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

# Verify activation (prompt should show (venv))
```

### 2.4 Install Dependencies

```bash
# Install from requirements.txt
pip install -r requirements.txt

# Verify installations
python -c "import paho.mqtt.client; print('MQTT OK')"
python -c "import pygame; print('Pygame OK')"
python -c "import matplotlib; print('Matplotlib OK')"
python -c "import numpy; print('Numpy OK')"
python -c "import tkinter; print('Tkinter OK')"
```

**Common Issues:**

**Tkinter not found (Linux):**
```bash
# Ubuntu/Debian
sudo apt-get install python3-tk

# Fedora
sudo dnf install python3-tkinter
```

**Pygame audio issues (Linux):**
```bash
# Install SDL dependencies
sudo apt-get install libsdl2-mixer-2.0-0
```

**Pygame issues (macOS):**
```bash
# Reinstall with specific version
pip install pygame==2.5.0 --force-reinstall
```

### 2.5 Configure Environment Variables

**Create `.env` file:**
```bash
cp .env.example .env
```

**Edit `.env` file:**
```env
THINGSPEAK_CHANNEL_ID=1234567
THINGSPEAK_MQTT_CLIENT_ID=Subscriber-GUI-001
THINGSPEAK_MQTT_USERNAME=YourUsername
THINGSPEAK_MQTT_PASSWORD=YourPassword
THINGSPEAK_MQTT_HOST=mqtt3.thingspeak.com
THINGSPEAK_MQTT_PORT=8883

ASCON_KEY=asconciphertest1
ASCON_NONCE_PREFIX=asconcipher1test
ASCON_VARIANT=Ascon-128

AUDIO_SAMPLE_RATE=8000
AUDIO_CHANNELS=1
AUDIO_BITS_PER_SAMPLE=16
```

> [!IMPORTANT]
> ASCON_KEY harus sama dengan key di Publisher.py (16 bytes exactly)

### 2.6 Test Subscriber GUI

```bash
python subscriber_gui.py
```

**Expected behavior:**
- GUI window opens dengan title "Audio Decryption Subscriber - Ascon-128"
- Status shows "Disconnected" (red)
- All buttons visible
- Empty text areas

**Test MQTT connection:**
1. Click "Connect to MQTT" button
2. Status should change to "Connected" (green)
3. Console should show: "Subscribed to: channels/..."

---

## Part 3: ThingSpeak Configuration

### 3.1 Create ThingSpeak Account

1. Navigate to [ThingSpeak.com](https://thingspeak.com/)
2. Click "Sign Up" atau "Get Started For Free"
3. Register dengan email atau MathWorks account
4. Verify email address
5. Login to dashboard

### 3.2 Create Channel

1. Click "Channels" → "My Channels"
2. Click "New Channel" button
3. Configure channel:
   - **Name**: Audio Encryption System
   - **Description**: Encrypted audio chunks with Ascon-128
   - **Field 1**: Encrypted Data (hex)
   - **Field 2**: Sequence Number
   - **Field 3**: Total Chunks
   - **Field 4**: Timestamp
   - **Field 5-8**: (optional, kosong)
4. Click "Save Channel"
5. Note **Channel ID** dari URL atau channel settings

### 3.3 Generate MQTT Credentials

**Method 1: via Devices (Recommended)**
1. Go to "Devices" → "MQTT"
2. Click "Add a new device"
3. Configure:
   - **Device Name**: ESP32 Audio Publisher
   - **Description**: Audio encryption device
   - **Authorize this device on channels**: Select your channel
4. Click "Add Device"
5. **IMPORTANT**: Copy dan save credentials yang muncul:
   - Client ID
   - Username  
   - Password
   
   > [!CAUTION]
   > Credentials HANYA ditampilkan SATU KALI. Save immediately!

**Method 2: via Account Settings**
1. Click username (top right) → "My Profile"
2. Scroll to "MQTT API"
3. Click "Generate new MQTT API Key"
4. Copy:
   - Client ID (format: random string)
   - Username (format: username)
   - Password (format: long alphanumeric)

### 3.4 Test MQTT Connection

**Simple Python test:**
```python
import paho.mqtt.client as mqtt
import ssl

BROKER = "mqtt3.thingspeak.com"
PORT = 8883
CLIENT_ID = "your_client_id"
USERNAME = "your_username"
PASSWORD = "your_password"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected successfully!")
    else:
        print(f"Connection failed with code: {rc}")

client = mqtt.Client(client_id=CLIENT_ID)
client.username_pw_set(USERNAME, PASSWORD)
client.tls_set(cert_reqs=ssl.CERT_NONE)
client.on_connect = on_connect

try:
    client.connect(BROKER, PORT, 60)
    client.loop_start()
    import time
    time.sleep(2)
    client.loop_stop()
except Exception as e:
    print(f"Error: {e}")
```

Expected: "Connected successfully!"

### 3.5 Monitor Data in ThingSpeak

**View incoming data:**
1. Go to channel "Private View"
2. Field charts akan update ketika ESP32 publish data
3. Click field untuk zoom/details
4. Export data: Click "Data Export" button

**MQTT Subscribe view:**
1. Go to channel → "API Keys"
2. Under "Subscribe" section, note the topic
3. Use MQTT client (e.g., MQTT Explorer) untuk monitor real-time

---

## Verification Checklist

### ESP32 Publisher ✓
- [ ] MicroPython firmware flashed successfully
- [ ] Files uploaded (ascon.py, Publisher.py)
- [ ] WiFi credentials configured
- [ ] ThingSpeak credentials configured
- [ ] Serial monitor shows "Tidak merekam"
- [ ] Recording triggered successfully
- [ ] Chunks published to ThingSpeak

### Desktop Subscriber ✓
- [ ] Python 3.8+ installed
- [ ] Virtual environment created and activated
- [ ] All dependencies installed (no errors)
- [ ] .env file created and configured
- [ ] GUI launches without errors
- [ ] MQTT connection successful (green status)

### ThingSpeak ✓
- [ ] Account created and verified
- [ ] Channel created with 4 fields
- [ ] MQTT credentials generated and saved
- [ ] MQTT test connection successful
- [ ] Data visible in channel charts

---

## Next Steps

System setup complete! Proceed to:
- [Usage Guide](usage.md) - Cara menggunakan sistem
- [Architecture](architecture.md) - Memahami arsitektur sistem
- [Security](security.md) - Security considerations

## Support

Jika mengalami issues saat setup, lihat troubleshooting di [Usage Guide](usage.md) atau buat issue di repository.

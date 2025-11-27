# Usage Guide - Audio Encryption System

Panduan lengkap penggunaan sistem enkripsi audio ESP32 dan desktop subscriber GUI.

## Table of Contents
- [Using ESP32 Publisher](#using-esp32-publisher)
- [Using Desktop Subscriber GUI](#using-desktop-subscriber-gui)
- [Workflow Example](#workflow-example)
- [Troubleshooting](#troubleshooting)

---

## Using ESP32 Publisher

### Starting the System

1. **Connect ESP32** via USB atau power dengan battery/adapter
2. **Open serial monitor** (115200 baud rate):
   ```bash
   # Using screen (Linux/Mac)
   screen /dev/ttyUSB0 115200
   
   # Using PuTTY (Windows)
   # Set: COM3, 115200 baud, Serial connection
   ```

3. **Monitor startup sequence**:
   ```
   Connecting to WiFi..... Connected!
   IP Address: 192.168.1.100
   Connecting to MQTT broker... Connected!
   
   Tidak merekam
   Waiting for trigger...
   ```

### Recording Audio

**Trigger recording** - ESP32 akan auto-start recording setelah delay atau via button press

**Serial output during recording:**
```
Sedang merekam: 1s
Sedang merekam: 2s
Sedang merekam: 3s
Sedang merekam: 4s
Sedang merekam: 5s
Sedang merekam: 6s
Sedang merekam: 7s
Sedang merekam: 8s
Sedang merekam: 9s
Sedang merekam: 10s
Recording complete!
Total samples: 80000
```

### Processing and Publishing

```
Preprocessing audio...
Preprocessing complete!
Audio data size: 160000 bytes
Chunking complete: 313 chunks
Encrypting chunk 1/313
Publishing chunk 1/313
Encrypting chunk 2/313
Publishing chunk 2/313
...
Encrypting chunk 313/313
Publishing chunk 313/313
All chunks published successfully!
=== Recording cycle complete ===

Tidak merekam
```

> [!IMPORTANT]
> **Recording status indicators:**
> - `Tidak merekam` = Idle state, waiting for trigger
> - `Sedang merekam: Xs` = Currently recording (X = seconds elapsed)
> - `Recording complete!` = Audio capture finished

### Adjusting KY-037 Sensitivity

KY-037 module memiliki potentiometer untuk adjust sensitivity:

1. **Rotate potentiometer** clockwise → increase sensitivity
2. **Rotate potentiometer** counter-clockwise → decrease sensitivity
3. **Test with serial monitor**: speak/make noise, watch ADC values
4. **Optimal range**: ADC values should vary between 500-3500 untuk audio yang jelas

---

## Using Desktop Subscriber GUI

### Launching the Application

```bash
# Navigate to project folder
cd d:/Kuliahku/project/keamanan_informasi/ascon

# Activate virtual environment (if using)
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Run GUI
python subscriber_gui.py
```

### GUI Overview

![Subscriber GUI Layout]

**Main Components:**
1. **Status Panel** (top)
   - Connection status indicator
   - Chunk counter (Received: X/Y chunks)
   - Progress bar

2. **Control Buttons** (below status)
   - Connect to MQTT
   - Disconnect
   - Decrypt Audio
   - Play Audio
   - Download Encrypted
   - Download Decrypted

3. **Encrypted Data Display** (center)
   - Shows received encrypted chunks in hex format
   - Auto-scrolls as data arrives

4. **Chunk Metadata** (below encrypted data)
   - Displays sequence numbers, timestamps, totals

5. **Audio Waveform** (bottom)
   - Visualizes decrypted audio
   - Shows time and amplitude

### Step-by-Step Workflow

#### Step 1: Connect to MQTT

1. Click **"Connect to MQTT"** button
2. Wait for status to change:
   - `Disconnected` (red) → `Connected` (green)
3. Console output:
   ```
   Connecting to ThingSpeak MQTT broker...
   Connected to ThingSpeak MQTT broker
   Subscribed to: channels/1234567/subscribe/fields/+
   ```

> [!TIP]
> Jika connection gagal, verify `.env` credentials dan internet connection

#### Step 2: Receive Encrypted Chunks

**ESP32 mulai publish** → GUI automatically receives chunks

**GUI Updates:**
- Encrypted data text area fills with hex data:
  ```
  --- Chunk 1/313 ---
  Encrypted (hex): a5f3c2d1... (truncated)
  
  --- Chunk 2/313 ---
  Encrypted (hex): 9b8e7f6a...
  ```

- Chunk counter updates: `Chunks: 15/313`
- Progress bar advances: 4.8% → 9.6% → ...
- Metadata displays: `Sequence: 15, Total: 313, Timestamp: 1732685123`

**Completion:**
```
=== All chunks received! Ready to decrypt ===
```

Buttons enabled: **Decrypt Audio**, **Download Encrypted**

#### Step 3: Decrypt Audio

1. Click **"Decrypt Audio"** button
2. Decryption process starts:
   ```
   === Starting decryption ===
   Decrypting chunk 1...
   Decrypting chunk 2...
   ...
   Decrypting chunk 313...
   
   Decryption complete! Total bytes: 160000
   Audio samples: 80000
   Saved WAV file: decrypted_audio_20251127_112345.wav
   ```

3. **Waveform visualization** appears di panel bawah
4. **Success dialog** shows: "Audio decrypted successfully! 80000 samples"

Buttons enabled: **Play Audio**, **Download Decrypted**

#### Step 4: Play Audio

1. Click **"Play Audio"** button
2. Audio plays through speakers/headphones
3. **Playback dialog** shows: "Audio playback started"

**Playback controls:**
- Automatic playback saat button clicked
- To replay: Click "Play Audio" again
- To stop: Close pygame mixer atau wait for completion

#### Step 5: Download Files

**Download Encrypted Chunks:**
1. Click **"Download Encrypted"**
2. File dialog appears
3. Choose location dan filename (default: `encrypted_chunks_YYYYMMDD_HHMMSS.json`)
4. File saved dengan format:
   ```json
   {
     "chunks": {
       "1": {
         "encrypted_hex": "a5f3c2d1...",
         "timestamp": 1732685123,
         "total": 313
       },
       ...
     },
     "metadata": {
       "total_chunks": 313,
       "encryption": "Ascon-128",
       "sample_rate": 8000
     }
   }
   ```

**Download Decrypted Audio:**
1. Click **"Download Decrypted"**
2. File dialog appears
3. Choose location dan filename (default: `decrypted_audio_YYYYMMDD_HHMMSS.wav`)
4. WAV file saved
5. Can be played dengan any media player (VLC, Windows Media Player, etc.)

#### Step 6: Disconnect

1. Click **"Disconnect"** button
2. Status changes: `Connected` (green) → `Disconnected` (red)
3. Console: "Disconnected from MQTT broker"

---

## Workflow Example

### Complete End-to-End Test

**Terminal 1: ESP32 Serial Monitor**
```
Tidak merekam
Waiting for trigger...
```

**Terminal 2: Desktop Subscriber GUI**
```bash
python subscriber_gui.py
```

**Actions:**

1. **GUI**: Click "Connect to MQTT" → Status: Connected ✓

2. **ESP32**: Auto-trigger atau press button → Recording starts
   ```
   Sedang merekam: 1s
   Sedang merekam: 2s
   ...
   Sedang merekam: 10s
   Recording complete!
   ```

3. **ESP32**: Processing dan publishing
   ```
   Chunking complete: 313 chunks
   Publishing chunk 1/313
   Publishing chunk 2/313
   ...
   All chunks published successfully!
   ```

4. **GUI**: Real-time updates
   - Chunks: 50/313 → 100/313 → ... → 313/313
   - Progress bar: 16% → 32% → ... → 100%
   - "All chunks received! Ready to decrypt"

5. **GUI**: Click "Decrypt Audio" → Decryption success

6. **GUI**: Waveform displayed, Click "Play Audio" → Audio plays

7. **GUI**: Click "Download Decrypted" → Save as WAV

8. **Verification**: Play WAV file di external player → Compare dengan original

---

## Troubleshooting

### ESP32 Issues

**Problem: WiFi tidak connect**
```
Connecting to WiFi....................
WiFi connection timeout!
```

**Solutions:**
- Check WiFi SSID dan password di `Publisher.py`
- Ensure WiFi is 2.4GHz (ESP32 tidak support 5GHz)
- Move ESP32 closer ke router
- Check WiFi network has internet access
- Restart ESP32: press EN/RST button

**Problem: MQTT connection failed**
```
MQTT connection failed: -1
```

**Solutions:**
- Verify ThingSpeak credentials di `Publisher.py`
- Check Channel ID benar
- Verify MQTT username/password tidak expired
- Check firewall tidak block outgoing connections
- Test internet connectivity: `ping thingspeak.com`

**Problem: Recording tidak start**
```
Tidak merekam
(stuck in this state)
```

**Solutions:**
- Check auto-trigger delay di code: `time.sleep(5)`
- If using button: verify button wiring dan code
- Check serial output for errors
- Restart ESP32

**Problem: ADC values tidak berubah**
```
Total samples: 80000
(but all values same/constant)
```

**Solutions:**
- Check KY-037 wiring (especially A0 → GPIO 34)
- Verify KY-037 power (VCC connected)
- Adjust sensitivity potentiometer di KY-037
- Test dengan loud noise/music near sensor
- Check ADC pin: must use GPIO 32-39 (ADC1)

### Subscriber GUI Issues

**Problem: Cannot connect to MQTT**
```
ERROR: Connection failed: [Errno 11001] getaddrinfo failed
```

**Solutions:**
- Check internet connection
- Verify hostname resolves: `ping mqtt3.thingspeak.com`
- Check firewall not blocking port 8883
- Verify `.env` file exists dan loaded
- Check credentials di `.env` match ThingSpeak

**Problem: No chunks received**
```
Connected to ThingSpeak MQTT broker
Subscribed to: channels/...
(but no data appears)
```

**Solutions:**
- Verify Channel ID di `.env` matches ESP32
- Check ESP32 actually publishing (monitor serial)
- Verify ESP32 using same Channel ID
- Check ThingSpeak channel field mappings
- Try manually publishing test data via ThingSpeak web interface

**Problem: Decryption fails**
```
Error decrypting chunk 1: Verification failed
```

**Solutions:**
- Check `ASCON_KEY` di `.env` sama dengan Publisher.py (16 bytes exactly)
- Verify `ASCON_NONCE_PREFIX` match
- Check data tidak corrupted during transmission
- Verify sequence numbers correct
- Try re-receiving chunks (disconnect → reconnect)

**Problem: Audio playback error**
```
pygame.error: No available audio device
```

**Solutions:**
- Install/reinstall pygame: `pip install pygame --upgrade`
- Check audio drivers installed di OS
- Test audio output dengan media player
- **Linux**: Install SDL2: `sudo apt-get install libsdl2-mixer-2.0-0`
- **Windows**: Update audio drivers
- Try different audio output device

**Problem: Missing chunks**
```
Chunks: 310/313
(stuck, not completing)
```

**Solutions:**
- Wait longer (network latency)
- Check ESP32 serial: verify all chunks published
- Network packet loss: retry recording
- ThingSpeak rate limiting: wait 15 seconds
- Check WiFi signal strength

### Audio Quality Issues

**Problem: Audio sangat noise**

**Solutions:**
- Adjust KY-037 sensitivity potentiometer
- Move ESP32/sensor away dari electrical noise sources
- Improve audio preprocessing filter di Publisher.py
- Use shielded cables untuk KY-037
- Add hardware low-pass filter

**Problem: Audio terdengar distorted**

**Solutions:**
- Check ADC sampling rate (8kHz adequate untuk voice)
- Verify DC offset removal working
- Check amplification tidak clipping (ADC values 0-4095 range)
- Adjust KY-037 sensitivity (might be too high)
- Verify WAV reconstruction di subscriber

**Problem: Audio volume terlalu rendah**

**Solutions:**
- Increase KY-037 sensitivity
- Speak closer ke microphone
- Adjust pygame mixer volume:
  ```python
  pygame.mixer.music.set_volume(1.0)  # Max volume
  ```
- Amplify audio post-processing

---

## Performance Tips

### Optimizing ESP32

1. **Reduce chunk size** untuk faster publishing
   ```python
   CHUNK_SIZE = 256  # instead of 512
   ```

2. **Increase WiFi transmission power**
   ```python
   sta_if.config(txpower=20)  # Max power (20 dBm)
   ```

3. **Disable unnecessary features**
   - Remove serial print untuk faster execution
   - Reduce preprocessing complexity

### Optimizing Subscriber

1. **Use faster decryption**: Ascon already optimized

2. **Reduce GUI updates**: Batch chunk display updates

3. **Use threading** untuk non-blocking UI (already implemented)

---

## Best Practices

1. **Always monitor ESP32 serial output** saat debugging
2. **Test ThingSpeak credentials** sebelum production use
3. **Keep encryption keys secure** - don't hardcode di public repos
4. **Backup .env file** dengan credentials
5. **Regular testing** untuk verify end-to-end workflow
6. **Network stability important** untuk reliable chunk transmission
7. **Label audio files** dengan timestamps untuk tracking

---

## Next Steps

- Explore [Architecture](architecture.md) untuk memahami sistem design
- Read [Security](security.md) untuk security best practices
- Review [ThingSpeak](thingspeak.md) untuk advanced MQTT features

## Support

Untuk issues atau questions, create issue di repository atau contact maintainer.

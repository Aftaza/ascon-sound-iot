# ESP32 Audio Encryption Publisher with KY-037 Sensor
# Ascon-128 AEAD + ThingSpeak MQTT over TLS
"""
Hardware Setup:
- ESP32 DevKit or similar
- KY-037 Sound Detection Sensor Module
  - VCC → 3.3V
  - GND → GND
  - A0 (Analog) → GPIO 34 (ADC1_CH6)
  - D0 (Digital) → Optional

WiFi and MQTT Configuration:
- Update WIFI_SSID and WIFI_PASSWORD
- Update THINGSPEAK_* credentials from your ThingSpeak account
"""

import binascii
import ascon
import network
import time
from machine import Pin, ADC
import ujson
from umqtt.simple import MQTTClient
import gc

# ==================== CONFIGURATION ====================

# WiFi Configuration
WIFI_SSID = "YOUR_WIFI_SSID"
WIFI_PASSWORD = "YOUR_WIFI_PASSWORD"

# ThingSpeak MQTT Configuration
THINGSPEAK_CHANNEL_ID = "YOUR_CHANNEL_ID"
MQTT_CLIENT_ID = "ESP32-Audio-Publisher"
MQTT_USER = "YOUR_MQTT_USERNAME"
MQTT_PASSWORD = "YOUR_MQTT_PASSWORD"
MQTT_BROKER = "mqtt3.thingspeak.com"
MQTT_PORT = 8883  # TLS port
MQTT_TOPIC = f"channels/{THINGSPEAK_CHANNEL_ID}/publish"

# Ascon-128 Encryption Configuration
ASCON_KEY = b"asconciphertest1"  # 16 bytes (128 bits)
ASCON_NONCE_PREFIX = b"asconcipher1"  # Will be combined with timestamp+seq
ASCON_VARIANT = "Ascon-128"
ASSOCIATED_DATA = b"AUDIO_CHUNK"

# Audio Recording Configuration
ADC_PIN = 34  # GPIO 34 for KY-037 analog output
SAMPLE_RATE = 8000  # 8 kHz (suitable for ESP32 ADC)
RECORDING_DURATION = 10  # seconds (5-10 configurable)
CHUNK_SIZE = 512  # Max chunk size in bytes for MQTT
ADC_SAMPLES_PER_SEC = SAMPLE_RATE // 10  # Sample every 100ms batch

# ==================== HARDWARE SETUP ====================

# Initialize ADC for KY-037
adc = ADC(Pin(ADC_PIN))
adc.atten(ADC.ATTN_11DB)  # Full range: 0-3.3V -> 0-4095
adc.width(ADC.WIDTH_12BIT)  # 12-bit resolution (0-4095)

# Optional: Button to trigger recording (GPIO 0)
# button = Pin(0, Pin.IN, Pin.PULL_UP)

# ==================== HELPER FUNCTIONS ====================

def connect_wifi():
    """Connect to WiFi network"""
    print("Connecting to WiFi", end="")
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)
    sta_if.connect(WIFI_SSID, WIFI_PASSWORD)
    
    timeout = 20  # 20 seconds timeout
    start_time = time.time()
    while not sta_if.isconnected():
        print(".", end="")
        time.sleep(0.5)
        if time.time() - start_time > timeout:
            print("\nWiFi connection timeout!")
            return False
    
    print(" Connected!")
    print(f"IP Address: {sta_if.ifconfig()[0]}")
    return True

def remove_dc_offset(samples):
    """Remove DC offset from audio samples"""
    avg = sum(samples) // len(samples)
    return [s - avg for s in samples]

def moving_average_filter(samples, window=3):
    """Simple moving average filter for noise reduction"""
    filtered = []
    for i in range(len(samples)):
        start = max(0, i - window // 2)
        end = min(len(samples), i + window // 2 + 1)
        filtered.append(sum(samples[start:end]) // (end - start))
    return filtered

def record_audio(duration):
    """
    Record audio from KY-037 for specified duration
    Returns: list of ADC samples (12-bit values)
    """
    print(f"\nStarting audio recording for {duration} seconds...")
    samples = []
    samples_per_loop = SAMPLE_RATE // 10  # Sample 100ms worth per iteration
    
    for second in range(1, duration + 1):
        print(f"Sedang merekam: {second}s")
        
        # Record for 1 second
        for _ in range(10):  # 10 iterations of 100ms each
            batch = []
            for _ in range(samples_per_loop):
                batch.append(adc.read())
                time.sleep_us(125)  # ~8kHz sampling (1/8000 = 125 microseconds)
            samples.extend(batch)
        
        gc.collect()  # Garbage collection to free memory
    
    print("Recording complete!")
    print(f"Total samples: {len(samples)}")
    return samples

def preprocess_audio(samples):
    """Apply basic preprocessing to audio samples"""
    print("Preprocessing audio...")
    
    # Remove DC offset
    samples = remove_dc_offset(samples)
    
    # Apply moving average filter
    samples = moving_average_filter(samples, window=5)
    
    print("Preprocessing complete!")
    return samples

def samples_to_bytes(samples):
    """Convert 12-bit ADC samples to bytes (2 bytes per sample, little-endian)"""
    data = bytearray()
    for sample in samples:
        # Clamp to 12-bit range and convert to 2 bytes
        value = max(0, min(4095, sample))
        data.append(value & 0xFF)  # Low byte
        data.append((value >> 8) & 0xFF)  # High byte
    return bytes(data)

def chunk_audio_data(audio_bytes):
    """
    Split audio data into chunks with metadata
    Returns: list of (chunk_data, sequence, total_chunks)
    """
    chunks = []
    total_chunks = (len(audio_bytes) + CHUNK_SIZE - 1) // CHUNK_SIZE
    
    for i in range(total_chunks):
        start = i * CHUNK_SIZE
        end = min(start + CHUNK_SIZE, len(audio_bytes))
        chunk_data = audio_bytes[start:end]
        chunks.append((chunk_data, i + 1, total_chunks))
    
    print(f"Chunking complete: {total_chunks} chunks")
    return chunks

def encrypt_chunk(chunk_data, sequence, timestamp):
    """
    Encrypt audio chunk using Ascon-128
    Returns: encrypted bytes (ciphertext + tag)
    """
    # Generate unique nonce: prefix + timestamp + sequence
    nonce_str = f"{ASCON_NONCE_PREFIX.decode()}{timestamp}{sequence:04d}"
    nonce = nonce_str[:16].encode().ljust(16, b'0')  # Ensure 16 bytes
    
    # Associated data includes metadata
    associated_data = f"{ASSOCIATED_DATA.decode()}_{sequence}_{timestamp}".encode()
    
    # Encrypt using Ascon-128
    ciphertext = ascon.ascon_encrypt(
        key=ASCON_KEY,
        nonce=nonce,
        associateddata=associated_data,
        plaintext=chunk_data,
        variant=ASCON_VARIANT
    )
    
    return ciphertext

def publish_chunks(client, chunks):
    """
    Publish encrypted chunks to ThingSpeak MQTT
    """
    timestamp = int(time.time())
    
    for chunk_data, sequence, total_chunks in chunks:
        print(f"Encrypting chunk {sequence}/{total_chunks}")
        
        # Encrypt chunk
        encrypted = encrypt_chunk(chunk_data, sequence, timestamp)
        encrypted_hex = binascii.hexlify(encrypted).decode()
        
        # Prepare MQTT payload (ThingSpeak format)
        payload = ujson.dumps({
            "field1": encrypted_hex[:255],  # ThingSpeak field limit
            "field2": str(sequence),
            "field3": str(total_chunks),
            "field4": str(timestamp)
        })
        
        print(f"Publishing chunk {sequence}/{total_chunks}")
        
        try:
            client.publish(MQTT_TOPIC, payload, qos=1)
            time.sleep(0.5)  # Small delay between publishes
        except Exception as e:
            print(f"Error publishing chunk {sequence}: {e}")
            return False
        
        gc.collect()
    
    print("All chunks published successfully!")
    return True

# ==================== MAIN PROGRAM ====================

def main():
    """Main program loop"""
    
    # Connect to WiFi
    if not connect_wifi():
        print("Failed to connect to WiFi. Restarting...")
        time.sleep(5)
        machine.reset()
    
    # Connect to MQTT broker
    print("Connecting to MQTT broker...", end="")
    try:
        client = MQTTClient(
            client_id=MQTT_CLIENT_ID,
            server=MQTT_BROKER,
            port=MQTT_PORT,
            user=MQTT_USER,
            password=MQTT_PASSWORD,
            ssl=True  # Enable TLS
        )
        client.connect()
        print(" Connected!")
    except Exception as e:
        print(f"\nMQTT connection failed: {e}")
        return
    
    # Main loop
    while True:
        print("\nTidak merekam")
        print("Waiting for trigger... (Press Ctrl+C to exit)")
        
        # Wait for button press or auto-trigger after delay
        time.sleep(5)  # Auto-trigger every 5 seconds (change to button.value() == 0 for button trigger)
        
        try:
            # Step 1: Record audio
            samples = record_audio(RECORDING_DURATION)
            
            # Step 2: Preprocess audio
            samples = preprocess_audio(samples)
            
            # Step 3: Convert to bytes
            audio_bytes = samples_to_bytes(samples)
            print(f"Audio data size: {len(audio_bytes)} bytes")
            
            # Step 4: Chunk audio data
            chunks = chunk_audio_data(audio_bytes)
            
            # Step 5: Encrypt and publish chunks
            success = publish_chunks(client, chunks)
            
            if success:
                print("=== Recording cycle complete ===\n")
            else:
                print("=== Publishing failed, retrying... ===\n")
            
            gc.collect()
            
        except KeyboardInterrupt:
            print("\n\nProgram interrupted by user")
            break
        except Exception as e:
            print(f"\nError in recording cycle: {e}")
            time.sleep(2)
    
    # Cleanup
    client.disconnect()
    print("Disconnected from MQTT broker")

# Run main program
if __name__ == "__main__":
    main()

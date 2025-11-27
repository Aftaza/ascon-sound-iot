# Desktop Audio Decryption Subscriber GUI
# Ascon-128 Decryption + ThingSpeak MQTT Subscriber
"""
Desktop GUI application for receiving encrypted audio chunks from ThingSpeak,
decrypting with Ascon-128, and playing back the reconstructed audio.

Features:
- Real-time MQTT subscription from ThingSpeak
- Display encrypted data (hex format)
- Decrypt audio chunks with Ascon-128
- Audio playback with waveform visualization
- Download encrypted/decrypted files
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import threading
import queue
import json
import binascii
import wave
import struct
import os
from datetime import datetime
from dotenv import load_dotenv
import paho.mqtt.client as mqtt
import ascon
import pygame
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# Load environment variables
load_dotenv()

# ==================== CONFIGURATION ====================

# ThingSpeak MQTT Configuration
CHANNEL_ID = os.getenv('THINGSPEAK_CHANNEL_ID', 'YOUR_CHANNEL_ID')
MQTT_CLIENT_ID = os.getenv('THINGSPEAK_MQTT_CLIENT_ID', 'Subscriber-GUI')
MQTT_USER = os.getenv('THINGSPEAK_MQTT_USERNAME', '')
MQTT_PASSWORD = os.getenv('THINGSPEAK_MQTT_PASSWORD', '')
MQTT_BROKER = os.getenv('THINGSPEAK_MQTT_HOST', 'mqtt3.thingspeak.com')
MQTT_PORT = int(os.getenv('THINGSPEAK_MQTT_PORT', '8883'))
MQTT_TOPIC = f"channels/{CHANNEL_ID}/subscribe/fields/+"

# Ascon-128 Decryption Configuration
ASCON_KEY = os.getenv('ASCON_KEY', 'asconciphertest1').encode()
ASCON_NONCE_PREFIX = os.getenv('ASCON_NONCE_PREFIX', 'asconcipher1').encode()
ASCON_VARIANT = os.getenv('ASCON_VARIANT', 'Ascon-128')
ASSOCIATED_DATA_PREFIX = b"AUDIO_CHUNK"

# Audio Configuration
SAMPLE_RATE = int(os.getenv('AUDIO_SAMPLE_RATE', '8000'))
CHANNELS = int(os.getenv('AUDIO_CHANNELS', '1'))
SAMPLE_WIDTH = int(os.getenv('AUDIO_BITS_PER_SAMPLE', '16')) // 8  # bytes

# ==================== SUBSCRIBER GUI CLASS ====================

class AudioSubscriberGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio Decryption Subscriber - Ascon-128")
        self.root.geometry("1000x750")
        self.root.resizable(True, True)
        
        # Data structures
        self.mqtt_client = None
        self.chunks_buffer = {}  # {sequence: (encrypted_hex, timestamp, total_chunks)}
        self.decrypted_audio = None
        self.audio_filename = None
        self.is_connected = False
        self.message_queue = queue.Queue()
        
        # Initialize pygame for audio playback
        pygame.mixer.init(frequency=SAMPLE_RATE, channels=CHANNELS)
        
        # Create GUI
        self.create_widgets()
        
        # Start message processing
        self.process_queue()
    
    def create_widgets(self):
        """Create all GUI widgets"""
        
        # ===== Status Panel =====
        status_frame = ttk.LabelFrame(self.root, text="Connection Status", padding=10)
        status_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.status_label = ttk.Label(status_frame, text="Disconnected", foreground="red", font=("Arial", 10, "bold"))
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        self.chunks_label = ttk.Label(status_frame, text="Chunks: 0/0", font=("Arial", 10))
        self.chunks_label.pack(side=tk.LEFT, padx=20)
        
        self.progress = ttk.Progressbar(status_frame, mode='determinate', length=300)
        self.progress.pack(side=tk.LEFT, padx=10)
        
        # ===== Control Buttons =====
        control_frame = ttk.Frame(self.root, padding=5)
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.btn_connect = ttk.Button(control_frame, text="Connect to MQTT", command=self.connect_mqtt)
        self.btn_connect.pack(side=tk.LEFT, padx=5)
        
        self.btn_disconnect = ttk.Button(control_frame, text="Disconnect", command=self.disconnect_mqtt, state=tk.DISABLED)
        self.btn_disconnect.pack(side=tk.LEFT, padx=5)
        
        self.btn_decrypt = ttk.Button(control_frame, text="Decrypt Audio", command=self.decrypt_audio, state=tk.DISABLED)
        self.btn_decrypt.pack(side=tk.LEFT, padx=5)
        
        self.btn_play = ttk.Button(control_frame, text="Play Audio", command=self.play_audio, state=tk.DISABLED)
        self.btn_play.pack(side=tk.LEFT, padx=5)
        
        self.btn_download_enc = ttk.Button(control_frame, text="Download Encrypted", command=self.download_encrypted, state=tk.DISABLED)
        self.btn_download_enc.pack(side=tk.LEFT, padx=5)
        
        self.btn_download_dec = ttk.Button(control_frame, text="Download Decrypted", command=self.download_decrypted, state=tk.DISABLED)
        self.btn_download_dec.pack(side=tk.LEFT, padx=5)
        
        # ===== Encrypted Data Display =====
        data_frame = ttk.LabelFrame(self.root, text="Encrypted Data (Hex)", padding=10)
        data_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.data_text = scrolledtext.ScrolledText(data_frame, wrap=tk.WORD, height=10, font=("Courier", 9))
        self.data_text.pack(fill=tk.BOTH, expand=True)
        
        # ===== Metadata Display =====
        meta_frame = ttk.LabelFrame(self.root, text="Chunk Metadata", padding=10)
        meta_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.meta_text = scrolledtext.ScrolledText(meta_frame, wrap=tk.WORD, height=4, font=("Courier", 9))
        self.meta_text.pack(fill=tk.BOTH, expand=True)
        
        # ===== Audio Waveform Visualization =====
        wave_frame = ttk.LabelFrame(self.root, text="Audio Waveform", padding=10)
        wave_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.figure = Figure(figsize=(8, 2), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_xlabel('Time (samples)')
        self.ax.set_ylabel('Amplitude')
        self.ax.grid(True, alpha=0.3)
        
        self.canvas = FigureCanvasTkAgg(self.figure, master=wave_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    # ===== MQTT Functions =====
    
    def connect_mqtt(self):
        """Connect to ThingSpeak MQTT broker"""
        self.log_data("Connecting to ThingSpeak MQTT broker...")
        
        try:
            self.mqtt_client = mqtt.Client(client_id=MQTT_CLIENT_ID)
            self.mqtt_client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
            self.mqtt_client.tls_set()  # Enable TLS
            
            # Set callbacks
            self.mqtt_client.on_connect = self.on_connect
            self.mqtt_client.on_message = self.on_message
            self.mqtt_client.on_disconnect = self.on_disconnect
            
            # Connect in separate thread
            thread = threading.Thread(target=self._connect_thread, daemon=True)
            thread.start()
            
        except Exception as e:
            self.log_data(f"Connection error: {e}")
            messagebox.showerror("Connection Error", str(e))
    
    def _connect_thread(self):
        """Thread function for MQTT connection"""
        try:
            self.mqtt_client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
            self.mqtt_client.loop_start()
        except Exception as e:
            self.message_queue.put(('error', f"Connection failed: {e}"))
    
    def on_connect(self, client, userdata, flags, rc):
        """Callback when connected to MQTT broker"""
        if rc == 0:
            self.message_queue.put(('connected', None))
            client.subscribe(MQTT_TOPIC, qos=1)
            self.message_queue.put(('log', f"Subscribed to: {MQTT_TOPIC}"))
        else:
            self.message_queue.put(('error', f"Connection failed with code {rc}"))
    
    def on_message(self, client, userdata, msg):
        """Callback when message received from MQTT broker"""
        try:
            payload = json.loads(msg.payload.decode())
            self.message_queue.put(('chunk', payload))
        except Exception as e:
            self.message_queue.put(('log', f"Error parsing message: {e}"))
    
    def on_disconnect(self, client, userdata, rc):
        """Callback when disconnected from MQTT broker"""
        self.message_queue.put(('disconnected', None))
    
    def disconnect_mqtt(self):
        """Disconnect from MQTT broker"""
        if self.mqtt_client:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
            self.is_connected = False
            self.update_connection_status(False)
            self.log_data("Disconnected from MQTT broker")
    
    # ===== Data Processing =====
    
    def process_chunk(self, payload):
        """Process received encrypted chunk"""
        try:
            encrypted_hex = payload.get('field1', '')
            sequence = int(payload.get('field2', 0))
            total_chunks = int(payload.get('field3', 0))
            timestamp = int(payload.get('field4', 0))
            
            # Store chunk
            self.chunks_buffer[sequence] = (encrypted_hex, timestamp, total_chunks)
            
            # Update UI
            received = len(self.chunks_buffer)
            self.chunks_label.config(text=f"Chunks: {received}/{total_chunks}")
            
            if total_chunks > 0:
                progress = (received / total_chunks) * 100
                self.progress['value'] = progress
            
            # Display encrypted data
            self.log_data(f"\n--- Chunk {sequence}/{total_chunks} ---")
            self.log_data(f"Encrypted (hex): {encrypted_hex[:100]}...")
            
            # Display metadata
            self.log_metadata(f"Sequence: {sequence}, Total: {total_chunks}, Timestamp: {timestamp}")
            
            # Enable decrypt button if all chunks received
            if received == total_chunks and total_chunks > 0:
                self.btn_decrypt.config(state=tk.NORMAL)
                self.btn_download_enc.config(state=tk.NORMAL)
                self.log_data("\n=== All chunks received! Ready to decrypt ===")
            
        except Exception as e:
            self.log_data(f"Error processing chunk: {e}")
    
    def decrypt_audio(self):
        """Decrypt all received chunks and reconstruct audio"""
        self.log_data("\n\n=== Starting decryption ===")
        
        try:
            # Sort chunks by sequence
            sorted_chunks = sorted(self.chunks_buffer.items())
            
            if not sorted_chunks:
                messagebox.showwarning("No Data", "No chunks to decrypt")
                return
            
            decrypted_data = bytearray()
            
            for sequence, (encrypted_hex, timestamp, _) in sorted_chunks:
                self.log_data(f"Decrypting chunk {sequence}...")
                
                # Convert hex to bytes
                encrypted_bytes = binascii.unhexlify(encrypted_hex)
                
                # Generate nonce (same as publisher)
                nonce_str = f"{ASCON_NONCE_PREFIX.decode()}{timestamp}{sequence:04d}"
                nonce = nonce_str[:16].encode().ljust(16, b'0')
                
                # Associated data
                associated_data = f"{ASSOCIATED_DATA_PREFIX.decode()}_{sequence}_{timestamp}".encode()
                
                # Decrypt
                try:
                    plaintext = ascon.ascon_decrypt(
                        key=ASCON_KEY,
                        nonce=nonce,
                        associateddata=associated_data,
                        ciphertext=encrypted_bytes,
                        variant=ASCON_VARIANT
                    )
                    
                    if plaintext is None:
                        raise Exception(f"Decryption failed for chunk {sequence}")
                    
                    decrypted_data.extend(plaintext)
                    
                except Exception as e:
                    self.log_data(f"Error decrypting chunk {sequence}: {e}")
                    messagebox.showerror("Decryption Error", f"Failed to decrypt chunk {sequence}: {e}")
                    return
            
            self.log_data(f"\nDecryption complete! Total bytes: {len(decrypted_data)}")
            
            # Convert bytes to audio samples
            samples = []
            for i in range(0, len(decrypted_data), 2):
                if i + 1 < len(decrypted_data):
                    # Read 2 bytes as little-endian 12-bit value
                    value = decrypted_data[i] | (decrypted_data[i+1] << 8)
                    # Convert to signed 16-bit for WAV
                    signed_value = (value - 2048) * 8  # Center around 0 and scale
                    samples.append(signed_value)
            
            self.decrypted_audio = samples
            self.log_data(f"Audio samples: {len(samples)}")
            
            # Save to WAV file
            self.save_wav_file(samples)
            
            # Visualize waveform
            self.visualize_waveform(samples)
            
            # Enable playback and download
            self.btn_play.config(state=tk.NORMAL)
            self.btn_download_dec.config(state=tk.NORMAL)
            
            messagebox.showinfo("Success", f"Audio decrypted successfully!\n{len(samples)} samples")
            
        except Exception as e:
            self.log_data(f"Decryption error: {e}")
            messagebox.showerror("Error", f"Decryption failed: {e}")
    
    def save_wav_file(self, samples, filename=None):
        """Save audio samples as WAV file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"decrypted_audio_{timestamp}.wav"
        
        self.audio_filename = filename
        
        with wave.open(filename, 'wb') as wav_file:
            wav_file.setnchannels(CHANNELS)
            wav_file.setsampwidth(SAMPLE_WIDTH)
            wav_file.setframerate(SAMPLE_RATE)
            
            # Convert samples to bytes
            frames = struct.pack('<' + 'h' * len(samples), *samples)
            wav_file.writeframes(frames)
        
        self.log_data(f"Saved WAV file: {filename}")
    
    def visualize_waveform(self, samples):
        """Display audio waveform"""
        self.ax.clear()
        self.ax.plot(samples, linewidth=0.5)
        self.ax.set_xlabel(f'Time (samples @ {SAMPLE_RATE}Hz)')
        self.ax.set_ylabel('Amplitude')
        self.ax.set_title(f'Audio Waveform ({len(samples)} samples, {len(samples)/SAMPLE_RATE:.2f}s)')
        self.ax.grid(True, alpha=0.3)
        self.canvas.draw()
    
    def play_audio(self):
        """Play decrypted audio"""
        if self.audio_filename and os.path.exists(self.audio_filename):
            try:
                pygame.mixer.music.load(self.audio_filename)
                pygame.mixer.music.play()
                self.log_data("Playing audio...")
                messagebox.showinfo("Playing", "Audio playback started")
            except Exception as e:
                messagebox.showerror("Playback Error", f"Failed to play audio: {e}")
        else:
            messagebox.showwarning("No Audio", "No decrypted audio available")
    
    # ===== File Download =====
    
    def download_encrypted(self):
        """Download encrypted chunks as JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"encrypted_chunks_{timestamp}.json"
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile=default_filename
        )
        
        if filename:
            try:
                data = {
                    "chunks": {seq: {"encrypted_hex": enc, "timestamp": ts, "total": total}
                              for seq, (enc, ts, total) in self.chunks_buffer.items()},
                    "metadata": {
                        "total_chunks": len(self.chunks_buffer),
                        "encryption": "Ascon-128",
                        "sample_rate": SAMPLE_RATE
                    }
                }
                
                with open(filename, 'w') as f:
                    json.dump(data, f, indent=2)
                
                messagebox.showinfo("Saved", f"Encrypted data saved to:\n{filename}")
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save: {e}")
    
    def download_decrypted(self):
        """Download decrypted audio as WAV file"""
        if not self.decrypted_audio:
            messagebox.showwarning("No Audio", "No decrypted audio available")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"decrypted_audio_{timestamp}.wav"
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".wav",
            filetypes=[("WAV files", "*.wav"), ("All files", "*.*")],
            initialfile=default_filename
        )
        
        if filename:
            try:
                self.save_wav_file(self.decrypted_audio, filename)
                messagebox.showinfo("Saved", f"Decrypted audio saved to:\n{filename}")
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save: {e}")
    
    # ===== UI Updates =====
    
    def process_queue(self):
        """Process messages from background threads"""
        try:
            while True:
                msg_type, data = self.message_queue.get_nowait()
                
                if msg_type == 'connected':
                    self.update_connection_status(True)
                    self.log_data("Connected to ThingSpeak MQTT broker")
                elif msg_type == 'disconnected':
                    self.update_connection_status(False)
                    self.log_data("Disconnected from MQTT broker")
                elif msg_type == 'chunk':
                    self.process_chunk(data)
                elif msg_type == 'log':
                    self.log_data(data)
                elif msg_type == 'error':
                    self.log_data(f"ERROR: {data}")
                    
        except queue.Empty:
            pass
        
        # Schedule next check
        self.root.after(100, self.process_queue)
    
    def update_connection_status(self, connected):
        """Update connection status display"""
        self.is_connected = connected
        if connected:
            self.status_label.config(text="Connected", foreground="green")
            self.btn_connect.config(state=tk.DISABLED)
            self.btn_disconnect.config(state=tk.NORMAL)
        else:
            self.status_label.config(text="Disconnected", foreground="red")
            self.btn_connect.config(state=tk.NORMAL)
            self.btn_disconnect.config(state=tk.DISABLED)
    
    def log_data(self, message):
        """Log message to encrypted data text area"""
        self.data_text.insert(tk.END, message + "\n")
        self.data_text.see(tk.END)
    
    def log_metadata(self, message):
        """Log message to metadata text area"""
        self.meta_text.insert(tk.END, message + "\n")
        self.meta_text.see(tk.END)

# ==================== MAIN ====================

def main():
    """Main function"""
    root = tk.Tk()
    app = AudioSubscriberGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()

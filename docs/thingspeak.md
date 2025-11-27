# ThingSpeak Configuration Guide

Panduan lengkap setup dan konfigurasi ThingSpeak untuk MQTT broker dalam sistem enkripsi audio.

## Table of Contents
- [What is ThingSpeak?](#what-is-thingspeak)
- [Create Account](#create-account)
- [Create Channel](#create-channel)
- [Generate MQTT Credentials](#generate-mqtt-credentials)
- [Topic Structure](#topic-structure)
- [Monitoring Data](#monitoring-data)

---

## What is ThingSpeak?

**ThingSpeak** adalah IoT platform dari MathWorks yang menyediakan:
- **Data Collection**: Store sensor data di cloud
- **MQTT Broker**: Publish/subscribe messaging
- **Visualization**: Charts dan graphs
- **MATLAB Analytics**: Data processing (optional)
- **API Access**: RESTful dan MQTT APIs

**Why ThingSpeak untuk project ini:**
- ✅ Free tier available
- ✅ MQTT over TLS support
- ✅ Easy setup dan configuration
- ✅ Web-based monitoring dashboard
- ✅ No server maintenance required

**Free Tier Limits:**
- Messages: 3 juta per year
- 4 MQTT devices
- Channel updates: ~ 1 update every 15 seconds
- Data retention: Unlimited (with account)

---

## Create Account

### 1. Sign Up

1. Navigate to [https://thingspeak.com](https://thingspeak.com)
2. Click **"Get Started For Free"** atau **"Sign Up"**
3. Choose registration method:
   - **MathWorks Account** (recommended untuk academics)
   - **Email + Password**
4. Fill form:
   - Email address
   - Password (min 8 characters)
   - First name, Last name
   - Country
5. Click **"Continue"**
6. **Verify email**: Check inbox untuk verification link
7. Click verification link → Account activated

### 2. Login

1. Go to [thingspeak.com](https://thingspeak.com)
2. Click **"Sign In"**
3. Enter credentials
4. Landing di **ThingSpeak Dashboard**

---

## Create Channel

Channel adalah container untuk data fields. Satu channel dapat memiliki maximum 8 fields.

### 1. Create New Channel

1. Di dashboard, click **"Channels"** → **"My Channels"**
2. Click **"New Channel"** button
3. Fill **Channel Settings**:

#### Basic Settings
- **Name**: `Audio Encryption System`
- **Description**: `Encrypted audio chunks transmitted via Ascon-128 AEAD`

#### Field Configuration
Configure 4 fields untuk audio chunk data:

- **Field 1**: `Encrypted Data (Hex)`
  - Description: Hexadecimal representation of encrypted audio chunk
  
- **Field 2**: `Sequence Number`
  - Description: Chunk sequence number (1-N)
  
- **Field 3**: `Total Chunks`
  - Description: Total number of chunks dalam recording
  
- **Field 4**: `Timestamp`
  - Description: Unix timestamp saat recording
  
- **Field 5-8**: (kosongkan atau optional metadata)

#### Optional Settings
- **Metadata**: (optional) Key-value pairs
- **Tags**: `audio`, `encryption`, `ascon`, `iot`
- **URL**: (optional) Link ke documentation
- **Video**: (optional)

4. **Save Channel** → Channel created!

### 2. Note Channel Details

Setelah channel created, note ini:
- **Channel ID**: Number di URL (e.g., `channels/1234567`)
- **Author**: Your username
- **Access**: Private (default)

Channel ID akan digunakan di:
- ESP32 Publisher.py
- Desktop Subscriber .env file
- MQTT topics

---

## Generate MQTT Credentials

ThingSpeak menyediakan 2 methods untuk MQTT credentials:

### Method 1: MQTT Devices (Recommended)

**Step 1: Navigate to Devices**
1. Click **"Devices"** di top menu
2. Click **"MQTT"** tab
3. Click **"Add a new device"**

**Step 2: Configure Device**
- **Device Name**: `ESP32 Audio Publisher`
- **Description**: `ESP32 with KY-037 sensor for audio encryption`
- **Authorize channels**: 
  - Select **your channel** dari dropdown
  - Permission: **Publish** (untuk ESP32)
  
- Click **"Add Channel"**
- Click **"Add Device"**

**Step 3: Save Credentials**

> [!CAUTION]
> **Credentials ditampilkan HANYA SATU KALI!** Copy dan save sekarang.

Screen akan show:
```
Client ID: randomstring123
Username: yourusername
Password: longalphanumericstring456
```

**Copy dan save** credentials ini ke:
- Notepad/text file
- Password manager
- .env file (subscriber)
- Publisher.py (ESP32)

**Step 4: Create Second Device (optional)**
Untuk subscriber, ulangi process:
- Device Name: `Desktop Subscriber`
- Permission: **Subscribe**

### Method 2: Account-Level MQTT API Key

**Alternative method** (not per-device):

1. Click **username** (top right) → **"My Profile"**
2. Scroll ke **"MQTT API"** section
3. Click **"Generate new MQTT API Key"**
4. Copy credentials:
   - **Client ID**
   - **Username**
   - **Password**

> [!WARNING]
> Account-level key memiliki full access ke all channels. Less secure than device-specific keys.

---

## Topic Structure

ThingSpeak menggunakan topic structure khusus untuk MQTT.

### Publish Topics (ESP32 → ThingSpeak)

**Format:**
```
channels/<channel_id>/publish
channels/<channel_id>/publish/<api_key>
```

**Example:**
```
channels/1234567/publish
```

**Payload format (JSON):**
```json
{
  "field1": "value1",
  "field2": "value2",
  "field3": "value3",
  "field4": "value4"
}
```

**Field limits:**
- Maximum field value: 255 characters
- Fields: field1 sampai field8
- Status (optional): status field untuk notes

**Our implementation:**
```json
{
  "field1": "a5f3c2d1...",  // hex encrypted chunk
  "field2": "1",            // sequence
  "field3": "313",          // total chunks
  "field4": "1732685123"    // timestamp
}
```

### Subscribe Topics (ThingSpeak → Desktop)

**Format untuk semua fields:**
```
channels/<channel_id>/subscribe/fields/+
```

**Format untuk specific field:**
```
channels/<channel_id>/subscribe/fields/field1
```

**Example:**
```
channels/1234567/subscribe/fields/+
```

**Wildcard:**
- `+`: Single-level wildcard (semua fields)
- `#`: Multi-level wildcard (semua topics under path)

### QoS Levels

ThingSpeak supports MQTT QoS:
- **QoS 0**: At most once (fire and forget)
- **QoS 1**: At least once (acknowledged) - **Recommended**
- **QoS 2**: Exactly once (not supported di ThingSpeak)

**Our implementation uses QoS 1** untuk reliability.

---

## Monitoring Data

### View Channel Data

1. Go to **"Channels"** → **"My Channels"**
2. Click your channel name
3. **Private View** tab shows:
   - Field charts dengan time-series data
   - Latest values
   - Export options

### Field Charts

Each field memiliki chart:
- **X-axis**: Timestamp
- **Y-axis**: Field value
- **Zoom**: Click dan drag untuk zoom
- **Export**: Download data as CSV

**Field 1 (Encrypted Data):**
- Chart shows hex strings (truncated untuk display)
- Hover untuk full value

**Field 2 (Sequence):**
- Line chart showing sequence progression
- Verify sequential order (1, 2, 3, ...)

**Field 3 (Total Chunks):**
- Constant value (should be same untuk all chunks)
- Example: 313

**Field 4 (Timestamp):**
- Unix timestamp values
- Increases monotonically

### Channel Stats

Di channel settings:
- **Views**: Number of chart views
- **Updates**: Total data points
- **Created**: Channel creation date
- **Last Entry**: Most recent update

### MATLAB Visualization (Optional)

ThingSpeak supports MATLAB visualizations:
1. Click **"Apps"** → **"MATLAB Visualization"**
2. Choose visualization type:
   - Custom (MATLAB code)
   - 2D line chart
   - 3D surface
3. Write MATLAB code untuk process data
4. Save dan view

**Example - Audio waveform reconstruction:**
```matlab
% Read data from channel
data = thingSpeakRead(channelID, 'ReadKey', readAPIKey);

% Process encrypted data
% (decrypt using MATLAB crypto toolbox)

% Plot waveform
plot(audioSamples);
title('Decrypted Audio Waveform');
```

### Data Export

**Export channel data:**
1. Channel page → **"Data Export"** button
2. Choose format:
   - **CSV**: Comma-separated values
   - **JSON**: Structured data
   - **XML**: Markup format
3. Select date range
4. Click **"Export"**
5. Download file

**CSV structure:**
```csv
created_at,entry_id,field1,field2,field3,field4
2025-11-27 10:30:00,1,a5f3c2d1...,1,313,1732685123
2025-11-27 10:30:01,2,9b8e7f6a...,2,313,1732685123
...
```

### API Access

**Read API** (untuk retrieve data programmatically):
```
GET https://api.thingspeak.com/channels/{channel_id}/feeds.json?api_key={read_key}&results=100
```

**Write API** (alternative ke MQTT untuk testing):
```
POST https://api.thingspeak.com/update?api_key={write_key}&field1=value1
```

---

## Security Best Practices

### 1. Keep Credentials Private

- ❌ **Don't commit** MQTT credentials ke public repos
- ✅ **Use environment variables** (.env file)
- ✅ **Use .gitignore** untuk exclude .env

### 2. Use Device-Specific Keys

- ✅ **Create separate devices** untuk publisher dan subscriber
- ✅ **Minimum permissions** (publish-only untuk ESP32)
- ❌ **Avoid** account-level API keys

### 3. Monitor Usage

- ✅ **Check channel stats** regularly
- ✅ **Set up alerts** untuk unusual activity
- ✅ **Review access logs** (if available)

### 4. Rotate Credentials

- ✅ **Regenerate keys** periodically
- ✅ **Delete unused devices**
- ✅ **Update credentials** di both publisher dan subscriber

### 5. Private Channels

- ✅ **Keep channels private** (default)
- ❌ **Don't share** channel links publicly
- ✅ **Use read keys** untuk controlled access

---

## Troubleshooting

### Cannot Create Channel

**Error**: "Maximum channels reached"

**Solution:**
- Free tier: 4 channels max
- Delete unused channels
- Upgrade to paid tier (if needed)

### MQTT Connection Refused

**Error**: Connection failed with code 5

**Solutions:**
- Check credentials (username, password, client ID)
- Verify device authorized on channel
- Check TLS enabled (port 8883)
- Firewall not blocking port

### Data Not Appearing

**Problem**: Publishing hangs successful, but no data di channel

**Solutions:**
- Verify Channel ID correct
- Check field names (field1, field2, etc.)
- Payload format JSON valid
- Check rate limiting (15 sec between updates)

### Rate Limiting

**Error**: "Rate limit exceeded"

**Solutions:**
- Free tier: max 1 update per 15 seconds
- Add delay antara publishes: `time.sleep(0.5)`
- Batch multiple values dalam single publish
- Upgrade plan untuk higher rate limit

---

## Advanced Features

### 1. Triggers & Actions (ThingReact)

Setup automatic actions based on data:
- **TweetControl**: Post tweet saat threshold met
- **Act Website**: HTTP request к external API
- **ThingHTTP**: Custom HTTP actions

### 2. TimeControl

Schedule actions:
- Daily data summary
- Weekly cleanup
- Periodic notifications

### 3. MATLAB Analysis

Run scheduled MATLAB code:
- Data aggregation
- Anomaly detection
- Predictive analytics

### 4. Webhooks

Receive notifications:
- SSL/TLS webhooks
- JSON payload
- Custom endpoints

---

## Summary

ThingSpeak Configuration Checklist:
- [x] Create ThingSpeak account
- [x] Create channel dengan 4 fields
- [x] Generate MQTT device credentials
- [x] Save credentials securely
- [x] Note Channel ID
- [x] Understand topic structure
- [x] Configure channel visualizations

Next steps:
- Update ESP32 Publisher.py dengan credentials
- Update Desktop Subscriber .env dengan credentials
- Test MQTT connection
- Monitor incoming data

---

## References

- [ThingSpeak Documentation](https://www.mathworks.com/help/thingspeak/)
- [MQTT API Documentation](https://www.mathworks.com/help/thingspeak/mqtt-api.html)
- [MATLAB Analytics](https://www.mathworks.com/help/thingspeak/analyze-channel-data-with-matlab-code.html)
- [REST API Reference](https://www.mathworks.com/help/thingspeak/rest-api.html)

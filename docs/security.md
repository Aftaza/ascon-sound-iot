# Security Considerations - Ascon-128 Audio Encryption System

Dokumentasi security untuk sistem enkripsi audio dengan focus pada cryptography, key management, dan threat mitigation.

## Table of Contents
- [Ascon-128 Algorithm Overview](#ascon-128-algorithm-overview)
- [Cryptographic Properties](#cryptographic-properties)
- [Key Management](#key-management)
- [Nonce Uniqueness](#nonce-uniqueness)
- [Threat Model](#threat-model)
- [Attack Mitigations](#attack-mitigations)
- [Security Best Practices](#security-best-practices)

---

## Ascon-128 Algorithm Overview

### What is Ascon?

**Ascon** adalah keluarga authenticated encryption dan hashing algorithms yang menjadi **winner of NIST Lightweight Cryptography Competition 2023**.

**Designed for:**
- ✅ Lightweight embedded systems
- ✅ IoT devices dengan limited resources
- ✅ High performance di both hardware dan software
- ✅ Side-channel attack resistance

### Ascon-128 Specification

**Algorithm**: Ascon-128 AEAD (Authenticated Encryption with Associated Data)

**Parameters:**
```
Key Size:     128 bits (16 bytes)
Nonce Size:   128 bits (16 bytes)
Tag Size:     128 bits (16 bytes)
Rate:         64 bits (8 bytes per permutation)
Capacity:     256 bits
Rounds:       12 (initialization), 6 (intermediate), 12 (finalization)
```

**Security Level**: 128-bit security (equivalent to AES-128)

### Why Ascon untuk Project Ini?

| Requirement | Ascon-128 Advantage |
|-------------|---------------------|
| **Lightweight** | Optimized untuk ESP32 limited RAM/CPU |
| **Authenticated** | Built-in integrity check (AEAD) |
| **Fast** | Faster than AES di software implementations |
| **Secure** | NIST-selected, peer-reviewed |
| **Simple** | Single pass encryption+authentication |
| **Side-channel resistant** | Designed untuk embedded systems |

---

## Cryptographic Properties

### 1. Confidentiality

**Property**: Ciphertext tidak reveal plaintext information

**Ascon-128 provides:**
- **128-bit security**: ~2^128 operations untuk brute force
- **Semantic security**: Identical plaintexts produce different ciphertexts (dengan different nonce)
- **IND-CPA**: Indistinguishable under chosen-plaintext attack

**In our system:**
```python
plaintext_chunk = b"audio_data_here..."  # 512 bytes
ciphertext = ascon_encrypt(key, nonce, AD, plaintext_chunk)
# Adversary cannot recover plaintext_chunk from ciphertext without key
```

### 2. Authenticity

**Property**: Ciphertext integrity dan authenticity verified

**Ascon-128 provides:**
- **128-bit tag**: Cryptographic MAC attached to ciphertext
- **AEAD**: Simultaneous encryption dan authentication
- **INT-CTXT**: Integrity of ciphertext guaranteed

**Verification:**
```python
plaintext = ascon_decrypt(key, nonce, AD, ciphertext)
if plaintext is None:
    # Tag verification failed → tampering detected
    raise IntegrityError("Ciphertext modified!")
```

**Protection against:**
- ❌ Ciphertext modification
- ❌ Chunk swapping
- ❌ Bit flipping attacks
- ❌ Padding oracle attacks

### 3. Associated Data Protection

**Property**: Metadata binds to ciphertext

**Our implementation:**
```python
associated_data = f"AUDIO_CHUNK_{sequence}_{timestamp}"
```

**Binds:**
- Sequence number → prevents chunk reordering
- Timestamp → replay attack detection
- Metadata → context authentication

**Attack prevented:**
```
Attacker cannot:
- Swap chunk 1 with chunk 2 (AD different)
- Replay old chunk (timestamp different)
- Inject fake chunk (AD verification fails)
```

---

## Key Management

### Current Implementation

**Key Storage:**
```python
# ESP32 Publisher.py
ASCON_KEY = b"asconciphertest1"  # 16 bytes hardcoded

# Desktop Subscriber .env
ASCON_KEY=asconciphertest1
```

**Distribution**: Pre-shared key (manual configuration)

### Security Analysis

**Strengths:**
- ✅ Simple implementation
- ✅ No key exchange complexity
- ✅ Suitable untuk proof-of-concept

**Weaknesses:**
- ❌ Key hardcoded di source code
- ❌ No forward secrecy
- ❌ No key rotation
- ❌ Manual distribution prone to errors
- ❌ If key compromised, all data compromised

### Best Practices for Key Management

#### 1. Secure Key Generation

```python
import secrets

# Generate cryptographically secure random key
key = secrets.token_bytes(16)  # 16 bytes = 128 bits
print(key.hex())  # Save securely
```

**Requirements:**
- Use cryptographically secure random generator
- Sufficient entropy (128 bits minimum)
- Unique per deployment

#### 2. Secure Key Storage

**ESP32:**
```python
# Option 1: ESP32 flash encryption
# Enable flash encryption di ESP-IDF menuconfig

# Option 2: Secure storage partition
from esp32 import NVS
nvs = NVS("encryption")
key = nvs.get_blob("ascon_key")
```

**Desktop:**
```python
# Option 1: Environment variables (.env)
ASCON_KEY=hex_key_here  # ✓ Current implementation

# Option 2: OS keyring
import keyring
key = keyring.get_password("ascon_system", "encryption_key")

# Option 3: Hardware security module (HSM)
# Store key di dedicated hardware
```

**Never:**
- ❌ Commit keys to version control (use .gitignore)
- ❌ Log keys di console/files
- ❌ Send keys via insecure channels (email, plaintext)

#### 3. Key Rotation

**Why rotate keys:**
- Limit impact of key compromise
- Meet compliance requirements
- Best practice untuk long-term systems

**Implementation strategy:**
```python
# Version key dengan timestamp
KEY_VERSION = "v1_2025_11"
ASCON_KEY = load_key(KEY_VERSION)

# Publish key version dengan chunk
associated_data = f"AUDIO_CHUNK_{sequence}_{timestamp}_{KEY_VERSION}"

# Subscriber checks key version
if key_version != current_version:
    key = load_old_key(key_version)
```

#### 4. Key Derivation (Advanced)

**Derive per-session keys dari master key:**
```python
import hashlib

master_key = b"master_secret_16"
session_id = b"session_20251127"

# Derive session key using HKDF
session_key = hashlib.pbkdf2_hmac('sha256', master_key, session_id, 100000, 16)
```

**Benefits:**
- Master key never directly used
- Different key per session
- Forward secrecy (session keys deleted)

---

## Nonce Uniqueness

### Why Nonce Uniqueness Critical

**Nonce reuse vulnerability:**
```
If encrypt(key, nonce, AD1, P1) and encrypt(key, nonce, AD2, P2):
    Adversary can:
    - XOR ciphertexts → leak plaintext XOR
    - Recover keystream
    - Forge tags
```

**Result**: **Complete security failure**

### Our Nonce Strategy

**Generation:**
```python
nonce_str = f"{prefix}{timestamp}{sequence:04d}"[:16].ljust(16, '0')
# Example: "asconcipher11732685123001"
```

**Components:**
- **Prefix**: "asconcipher1" (constant)
- **Timestamp**: Unix epoch (1732685123 = 10 digits)
- **Sequence**: 4-digit zero-padded (0001-9999)

**Uniqueness guarantee:**
```
Nonce space: 10^10 timestamps × 10^4 sequences = 10^14 unique nonces
Collision probability: Negligible if:
    - Timestamps don't repeat (system clock accurate)
    - Sequence resets per timestamp
```

### Security Analysis

**Strengths:**
- ✅ Deterministic (no random, reproducible)
- ✅ Large nonce space (10^14)
- ✅ Easy implementation
- ✅ Synchronized between publisher/subscriber

**Weaknesses:**
- ❌ Clock dependency (if clock resets, nonce reuse)
- ❌ Limited to 9999 chunks per second
- ❌ Timestamp collision if multiple devices

### Improvements

**Option 1: Add device ID**
```python
device_id = "ESP001"
nonce_str = f"{device_id}{timestamp}{sequence:04d}"[:16]
```

**Option 2: Random nonce (transmit dengan chunk)**
```python
nonce = secrets.token_bytes(16)
# Publish nonce dengan ciphertext
payload = {"ciphertext": ct_hex, "nonce": nonce_hex}
```

**Option 3: Counter-based (stateful)**
```python
global nonce_counter
nonce_counter += 1
nonce = nonce_counter.to_bytes(16, 'big')
```

---

## Threat Model

### Adversary Capabilities

**Assumptions:**
- Adversary can **eavesdrop** on MQTT traffic
- Adversary can **capture** encrypted chunks
- Adversary can **inject** fake messages
- Adversary can **replay** old messages
- Adversary can **reorder** chunks
- Adversary **cannot** break TLS encryption (assumed secure)
- Adversary **cannot** break Ascon-128 encryption
- Adversary **does not have** encryption key

### Assets to Protect

1. **Audio Content**: Plaintext audio data
2. **Audio Integrity**: Unmodified, authentic audio
3. **Metadata**: Sequence, timestamp information
4. **Encryption Key**: Secret key untuk Ascon-128

### Security Goals

| Goal | Requirement | Ascon-128 Provides |
|------|-------------|-------------------|
| **Confidentiality** | Audio content secret | ✅ Yes (128-bit encryption) |
| **Integrity** | Audio unmodified | ✅ Yes (AEAD tag) |
| **Authenticity** | Audio dari legitimate source | ✅ Yes (AEAD tag) |
| **Replay Prevention** | Old chunks tidak reused | ⚠️ Partial (timestamp) |
| **Sequence Integrity** | Chunks di correct order | ✅ Yes (AD binding) |

---

## Attack Mitigations

### 1. Eavesdropping Attack

**Attack**: Adversary intercepts MQTT messages

**Mitigation:**
- **TLS encryption**: MQTT over port 8883
- **Ascon-128**: Audio chunks encrypted
- **Result**: Adversary sees encrypted data only

**Effectiveness**: ✅ Strong (depend on TLS + Ascon security)

### 2. Tampering Attack

**Attack**: Adversary modifies ciphertext

**Mitigation:**
- **AEAD tag**: 128-bit authentication tag
- **Verification**: Decryption fails jika tag invalid

**Example:**
```python
# Adversary flips bit in ciphertext
modified_ciphertext = ciphertext[:-1] + b'\xFF'

# Subscriber attempts decrypt
plaintext = ascon_decrypt(key, nonce, AD, modified_ciphertext)
# plaintext == None → tampering detected
```

**Effectiveness**: ✅ Strong (cryptographic MAC)

### 3. Replay Attack

**Attack**: Adversary replays old encrypted chunks

**Mitigation (current):**
- **Timestamp verification** (not fully implemented)
- **Nonce includes timestamp**

**Improvement needed:**
```python
# Subscriber checks timestamp freshness
MAX_AGE = 60  # seconds
current_time = time.time()
if abs(current_time - chunk_timestamp) > MAX_AGE:
    raise ReplayError("Chunk too old!")
```

**Effectiveness**: ⚠️ Partial (requires implementation)

### 4. Chunk Reordering Attack

**Attack**: Adversary swaps chunk positions

**Mitigation:**
- **Sequence numbers** dalam AD
- **AD verification** binds sequence ke ciphertext

**Example:**
```python
# Chunk 1: AD = "AUDIO_CHUNK_1_1732685123"
# Chunk 2: AD = "AUDIO_CHUNK_2_1732685123"

# Adversary swaps → Decryption fails (AD mismatch)
```

**Effectiveness**: ✅ Strong (AD binding)

### 5. Man-in-the-Middle (MITM)

**Attack**: Adversary intercepts dan modifies communication

**Mitigation:**
- **TLS**: Server certificate verification
- **ThingSpeak**: Trusted broker

**Limitation**:
- No mutual TLS (client certificate)
- Broker trust dependency

**Effectiveness**: ✅ Strong (TLS + trusted broker)

### 6. Brute Force Attack

**Attack**: Try all possible keys

**Mitigation:**
- **128-bit key space**: 2^128 = 3.4×10^38 keys
- **Computational infeasible**: Billions of years

**Effectiveness**: ✅ Strong (large key space)

### 7. Side-Channel Attacks

**Attack**: Timing, power analysis untuk leak key

**Mitigation:**
- **Ascon designed** untuk resistance
- **Constant-time operations** dalam implementation

**Considerations:**
- ESP32 not fully protected
- Physical access required

**Effectiveness**: ⚠️ Moderate (ESP32 limitations)

---

## Security Best Practices

### For Production Deployment

#### 1. Key Management
- ✅ Use HSM atau secure key storage
- ✅ Implement key rotation policy
- ✅ Derive session keys dari master key
- ✅ Audit key access logs

#### 2. Nonce Management
- ✅ Ensure clock synchronization (NTP)
- ✅ Add device ID ke nonce
- ✅ Implement nonce tracking (detect reuse)
- ✅ Use random nonces dengan transmission

#### 3. Timestamp Validation
- ✅ Implement replay window check
- ✅ Synchronize clocks (NTP)
- ✅ Log rejected old chunks
- ✅ Alert di suspicious patterns

#### 4. Access Control
- ✅ Use device-specific MQTT credentials
- ✅ Minimum privilege (publish-only, subscribe-only)
- ✅ Rotate MQTT passwords regularly
- ✅ Monitor unauthorized access attempts

#### 5. Code Security
- ✅ Review ascon.py implementation
- ✅ Use official Ascon reference code
- ✅ Static analysis untuk vulnerabilities
- ✅ Regular security updates

#### 6. Network Security
- ✅ TLS 1.3 (if supported)
- ✅ Certificate pinning (broker certificate)
- ✅ Disable weak cipher suites
- ✅ Monitor network untuk anomalies

#### 7. Logging & Monitoring
- ✅ Log all encryption/decryption events
- ✅ Monitor failed authentications
- ✅ Alert di unusual patterns
- ✅ Audit trail untuk forensics

#### 8. Incident Response
- ✅ Plan untuk key compromise
- ✅ Procedure untuk key rollover
- ✅ Backup encrypted data
- ✅ Regular security assessments

---

## Compliance Considerations

### Data Protection

| Regulation | Requirement | Our Implementation |
|------------|-------------|-------------------|
| **GDPR** | Data encryption | ✅ Ascon-128 encryption |
| **HIPAA** | PHI protection | ✅ If audio contains health data |
| **PCI DSS** | Key management | ⚠️ Needs improvement |

### Encryption Standards

- **NIST**: Ascon-128 selected untuk LWC (2023)
- **FIPS**: Not yet FIPS-validated (consider AES untuk FIPS compliance)
- **ISO**: Pending standardization

---

## Limitations & Future Work

### Current Limitations

1. **Static key**: Pre-shared key without rotation
2. **No forward secrecy**: Past data vulnerable if key compromised
3. **Replay protection**: Not fully implemented
4. **Single device**: No multi-device key distribution
5. **No user authentication**: System-level only

### Future Improvements

1. **Diffie-Hellman key exchange**: Dynamic session keys
2. **Perfect forward secrecy**: Ephemeral keys per session
3. **Multi-party encryption**: Support multiple publishers/subscribers
4. **Hardware security**: Use ESP32 secure boot dan flash encryption
5. **Zero-knowledge proofs**: Prove authenticity without revealing data

---

## References

### Ascon Specification
- [Official Ascon Website](https://ascon.iaik.tugraz.at/)
- [NIST LWC Competition](https://csrc.nist.gov/projects/lightweight-cryptography)
- [Ascon Paper](https://ascon.iaik.tugraz.at/files/asconv12-nist.pdf)

### Cryptography Standards
- [NIST SP 800-38D (GCM)](https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication800-38d.pdf)
- [RFC 5116 (AEAD)](https://tools.ietf.org/html/rfc5116)

### Best Practices
- [OWASP Cryptographic Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html)
- [NIST Key Management Guidelines](https://csrc.nist.gov/publications/detail/sp/800-57-part-1/rev-5/final)

---

**Last Updated**: November 2025  
**Security Review**: Recommended before production deployment

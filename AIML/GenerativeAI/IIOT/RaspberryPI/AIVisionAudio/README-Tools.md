# Raspberry Pi Audio-Visual AI Project 🎥🎤

Real-time video and audio streaming from Raspberry Pi to OpenAI GPT-4o for intelligent scene analysis and speech recognition.

---

## 📋 Hardware Requirements

### Essential Components
- **Raspberry Pi 4 or 5**
  - Minimum 8 GB RAM
  - 128 GB Micro SD Card
  - Latest Raspberry Pi OS (Debian-based)
- **Raspberry Pi Camera Module**
  - V2.1 module or V3.0 module
- **USB Microphone**
  - Any USB audio input device

### Initial Setup
1. Flash latest Raspberry Pi OS to SD card
2. Enable required services:
   - SSH
   - VNC
   - I2C
   - Camera interface
3. 📖 [Official Getting Started Guide](https://www.raspberrypi.com/documentation/computers/getting-started.html)

---

## 🚀 Quick Start

### Install Dependencies

```bash
# System packages
sudo apt-get update
sudo apt-get install -y portaudio19-dev python3-pyaudio

# Python environment (using uv)
cd ~/DevOps/CameraDev/
uv init pi_stream
cd pi_stream
uv venv
source .venv/bin/activate
uv add openai python-dotenv flask pillow pyaudio
```

### Configure OpenAI API Key

```bash
# Create .env file in project root
echo "OPENAI_API_KEY=your-api-key-here" > .env
```

### Run the Application

```bash
cd src/OpenAIDev
python streaming_openaivis_audio.py
```

Open your browser to: `http://<raspberry-pi-ip>:5000`

---

## 📁 Project Files

| File | Description |
|------|-------------|
| `streaming_openaivis.py` | Video-only streaming with GPT-4o vision analysis |
| `streaming_openaivis_audio.py` | **Full audio + video streaming with AI analysis** |
| `test_audio_only.py` | Audio-only test with Whisper transcription |
| `hello_world.py` | Simple test script |

---

## 🧪 Camera Testing Commands

### Basic Tests

```bash
# Capture single image
rpicam-jpeg --output test.jpg

# Capture with custom resolution
rpicam-jpeg --output test.jpg --timeout 2000 --width 640 --height 480

# Record 10 second video
rpicam-vid -t 10s -o test.h264

# Play recorded video
ffplay test.h264
```

### Network Streaming

#### UDP Streaming

**On Raspberry Pi:**
```bash
rpicam-vid -t 0 -n --inline -o udp://<laptop-ip>:<port>
```

**On Laptop:**
```bash
# Using ffplay
ffplay udp://<raspberry-pi-ip>:<port> -fflags nobuffer -flags low_delay -framedrop

# Using VLC
vlc udp://<raspberry-pi-ip>:<port>
```

#### TCP Streaming

**On Raspberry Pi:**
```bash
rpicam-vid -t 0 -n --width 1280 --height 720 --framerate 10 --inline --listen -o tcp://<laptop-ip>:5555
```

**On Laptop:**
```bash
# Using ffplay
ffplay tcp://<raspberry-pi-ip>:5555 -fflags nobuffer -flags low_delay -framedrop

# Using VLC (macOS)
/Applications/VLC.app/Contents/MacOS/VLC tcp://<raspberry-pi-ip>:5555 :demux=h264
```

---

## 🤖 How It Works

### Audio + Video Processing Pipeline

1. **Video Capture**: `rpicam-vid` streams MJPEG frames from Pi camera
2. **Audio Capture**: PyAudio records from USB microphone (44.1kHz, mono)
3. **Audio Transcription**: OpenAI Whisper converts speech to text
4. **Vision Analysis**: GPT-4o analyzes video frame
5. **Combined Response**: AI describes scene and responds to speech
6. **Web Interface**: Flask streams video to browser at port 5000

### AI Models Used

- **GPT-4o**: Multimodal vision analysis
- **Whisper-1**: Audio transcription and speech recognition

---

## 🔧 Troubleshooting

### Audio Device Not Found
```bash
# List audio devices
python -c "import pyaudio; p = pyaudio.PyAudio(); [print(f'{i}: {p.get_device_info_by_index(i)[\"name\"]}') for i in range(p.get_device_count())]"

# Update DEVICE_INDEX in code if needed
```

### Camera Not Working
```bash
# Enable camera interface
sudo raspi-config
# Navigate to: Interface Options → Camera → Enable

# Test camera
rpicam-hello
```

### ALSA Warnings
ALSA warnings (PCM errors) are normal on Raspberry Pi and don't affect functionality.

---

## 📚 References

- [Raspberry Pi Documentation](https://www.raspberrypi.com/documentation/)
- [rpicam-apps Documentation](https://www.raspberrypi.com/documentation/computers/camera_software.html#rpicam-apps)
- [OpenAI API Documentation](https://platform.openai.com/docs/)
- [PyAudio Documentation](https://people.csail.mit.edu/hubert/pyaudio/docs/)

---

## 📝 License

MIT License - Feel free to use and modify for your projects!

---

**Built with ❤️ on Raspberry Pi**

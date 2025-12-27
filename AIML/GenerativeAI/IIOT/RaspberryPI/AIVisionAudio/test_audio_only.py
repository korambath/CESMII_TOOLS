#!/usr/bin/env python3
"""
Simple audio-only test - captures audio from USB mic and sends to OpenAI
"""

import pyaudio
import wave
import os
import time
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Audio settings
CHUNK = 4096  # Increased buffer size to prevent overflow
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100  # USB microphone's native sample rate
RECORD_SECONDS = 5  # Record 5 seconds at a time
DEVICE_INDEX = 2  # Your USB microphone

def list_audio_devices():
    """List all available audio devices"""
    p = pyaudio.PyAudio()
    print("\n=== Available Audio Devices ===")
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        print(f"{i}: {info['name']} (inputs: {info['maxInputChannels']})")
    p.terminate()
    print()

def record_audio(duration=5):
    """Record audio from USB microphone"""
    p = pyaudio.PyAudio()
    
    print(f"Recording {duration} seconds from device {DEVICE_INDEX}...")
    
    stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        input_device_index=DEVICE_INDEX,
        frames_per_buffer=CHUNK,
        stream_callback=None
    )
    
    frames = []
    for i in range(0, int(RATE / CHUNK * duration)):
        try:
            data = stream.read(CHUNK, exception_on_overflow=False)
            frames.append(data)
        except Exception as e:
            print(f"Warning: {e}")
            continue
    
    print("Recording finished!")
    
    stream.stop_stream()
    stream.close()
    p.terminate()
    
    # Save to temporary file
    temp_file = "/tmp/audio_test.wav"
    wf = wave.open(temp_file, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()
    
    return temp_file

def transcribe_audio(audio_file):
    """Send audio to OpenAI for transcription"""
    print("Sending audio to OpenAI...")
    
    try:
        with open(audio_file, "rb") as audio:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio,
                response_format="text"
            )
        return transcript
    except Exception as e:
        return f"Error: {e}"

def main():
    print("=" * 50)
    print("OpenAI Audio Test - USB Microphone")
    print("=" * 50)
    
    # Show available devices
    list_audio_devices()
    
    print(f"Using device {DEVICE_INDEX} for recording")
    print(f"Starting in 2 seconds... Get ready to speak!")
    time.sleep(2)
    
    while True:
        # Record audio
        audio_file = record_audio(RECORD_SECONDS)
        
        # Transcribe with OpenAI
        transcript = transcribe_audio(audio_file)
        
        # Display result
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"\n[{timestamp}] You said: {transcript}")
        print("-" * 50)
        
        # Wait a bit before next recording
        time.sleep(2)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nStopped by user.")

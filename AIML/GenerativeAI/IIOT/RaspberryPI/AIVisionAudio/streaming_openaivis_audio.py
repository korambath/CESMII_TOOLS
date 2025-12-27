import subprocess
import threading
import time
from flask import Flask, Response
from io import BytesIO
from PIL import Image
import base64
import pyaudio
import wave
import tempfile

import os
import requests
import openai
import json
from dotenv import load_dotenv
from openai import OpenAI
from datetime import datetime
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- CONFIG ---
#MODEL_ID = "gpt-4o"  # OpenAI vision model (supports images, not audio in API yet)
MODEL_ID = "gpt-5.2"  # OpenAI vision model (supports images, not audio in API yet)

# Audio settings
AUDIO_FORMAT = pyaudio.paInt16
AUDIO_CHANNELS = 1
AUDIO_RATE = 44100  # USB microphone's native sample rate
AUDIO_CHUNK = 4096  # Larger buffer to prevent overflow
AUDIO_RECORD_SECONDS = 5  # Capture 5 seconds of audio with each frame

app = Flask(__name__)
last_frame_data = None 
audio = pyaudio.PyAudio()

def capture_audio_snippet():
    """Capture a short audio snippet from USB microphone."""
    try:
        # Open audio stream (device 2 is USB PnP Sound Device)
        stream = audio.open(
            format=AUDIO_FORMAT,
            channels=AUDIO_CHANNELS,
            rate=AUDIO_RATE,
            input=True,
            input_device_index=2,  # USB microphone
            frames_per_buffer=AUDIO_CHUNK
        )
        
        print(f"[Audio] Recording {AUDIO_RECORD_SECONDS} seconds...")
        frames = []
        
        for i in range(0, int(AUDIO_RATE / AUDIO_CHUNK * AUDIO_RECORD_SECONDS)):
            try:
                data = stream.read(AUDIO_CHUNK, exception_on_overflow=False)
                frames.append(data)
            except Exception as e:
                continue
        
        stream.stop_stream()
        stream.close()
        
        # Save to temporary WAV file
        temp_wav = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        wf = wave.open(temp_wav.name, 'wb')
        wf.setnchannels(AUDIO_CHANNELS)
        wf.setsampwidth(audio.get_sample_size(AUDIO_FORMAT))
        wf.setframerate(AUDIO_RATE)
        wf.writeframes(b''.join(frames))
        wf.close()
        
        # Read and encode to base64
        with open(temp_wav.name, 'rb') as f:
            audio_data = f.read()
        
        os.unlink(temp_wav.name)  # Clean up temp file
        
        return base64.b64encode(audio_data).decode('utf-8')
        
    except Exception as e:
        print(f"[Audio Error]: {e}")
        return None

def ai_worker():
    """Thread that samples the camera feed and audio for OpenAI."""
    global last_frame_data
    print(f"AI Worker started using {MODEL_ID}...")
    print(f"Capturing video + audio every 10 seconds...")
    
    while True:
        if last_frame_data:
            try:
                # Convert image to base64
                base64_image = base64.b64encode(last_frame_data).decode('utf-8')
                
                # Capture audio
                base64_audio = capture_audio_snippet()
                
                # First transcribe the audio with Whisper
                audio_transcription = ""
                if base64_audio:
                    try:
                        # Decode audio and save temporarily
                        temp_wav = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
                        temp_wav.write(base64.b64decode(base64_audio))
                        temp_wav.close()
                        
                        # Transcribe with Whisper
                        with open(temp_wav.name, "rb") as audio_file:
                            transcript = client.audio.transcriptions.create(
                                model="whisper-1",
                                file=audio_file,
                                response_format="text"
                            )
                        audio_transcription = transcript
                        os.unlink(temp_wav.name)
                    except Exception as e:
                        print(f"[Whisper Error]: {e}")
                
                # Build prompt with audio context
                prompt_text = "What is currently happening in this camera feed? Describe what you see."
                if audio_transcription:
                    prompt_text += f"\n\nAudio detected: \"{audio_transcription}\""
                    prompt_text += "\n\nPlease describe both what you see in the image and respond to what was said."
                
                # Call OpenAI Vision API
                response = client.chat.completions.create(
                    model=MODEL_ID,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": prompt_text
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{base64_image}"
                                    }
                                }
                            ]
                        }
                    ],
                    #max_tokens=500
                    max_completion_tokens=5000
                )
                
                ai_response = response.choices[0].message.content
                timestamp = datetime.now().strftime('%H:%M:%S')
                print(f"\n{'='*60}")
                print(f"[{MODEL_ID} - {timestamp}]:")
                print(f"{ai_response}")
                print(f"{'='*60}\n")
                
            except Exception as e:
                print(f"[AI Error]: {e}")
                import traceback
                traceback.print_exc()
        
        # Wait 10 seconds between captures
        time.sleep(10)

def get_video_stream():
    global last_frame_data
    # Optimized rpicam command for Pi 4/5
    cmd = [
        'rpicam-vid', '-t', '0', '--inline', '--codec', 'mjpeg',
        '--width', '854', '--height', '480', '--framerate', '20',
        '--nopreview', '-o', '-'
    ]
    
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=0)
    buffer = b""
    
    try:
        while True:
            chunk = proc.stdout.read(4096)
            if not chunk: break
            buffer += chunk
            
            # Find JPEG boundaries
            start = buffer.find(b'\xff\xd8')
            end = buffer.find(b'\xff\xd9')
            
            if start != -1 and end != -1 and end > start:
                frame = buffer[start:end+2]
                buffer = buffer[end+2:]
                
                # Feed the AI thread the latest frame
                last_frame_data = frame
                
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    finally:
        proc.terminate()

@app.route('/')
def home():
    return '<html><body style="background:#000; color:#0f0; text-align:center; font-family:monospace;">' \
           '<h1>RPi + OpenAI Vision + Audio (GPT-4o) Live</h1>' \
           '<img src="/video" style="border:2px solid #0f0; max-width:90%;">' \
           '<p>AI analysis (video + audio) appearing in terminal...</p>' \
           '<p style="color:#ff0;">🎤 Microphone active - Speak to the camera!</p></body></html>'

@app.route('/video')
def video():
    return Response(get_video_stream(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    print("\n" + "="*60)
    print("Starting OpenAI Vision + Audio Analysis")
    print("="*60)
    print("🎥 Video: Raspberry Pi Camera")
    print("🎤 Audio: USB Microphone")
    print("🤖 Model: GPT-4o Audio Preview")
    print("="*60 + "\n")
    
    # Start AI thread in background
    threading.Thread(target=ai_worker, daemon=True).start()
    # Start web server
    app.run(host='0.0.0.0', port=5000, threaded=True)

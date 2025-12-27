import subprocess
import threading
import time
from flask import Flask, Response
from io import BytesIO
from PIL import Image
import base64

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
#MODEL_ID = "gpt-4o"  # Latest OpenAI vision model
MODEL_ID = "gpt-5-nano"

app = Flask(__name__)
last_frame_data = None 

def ai_worker():
    """Thread that samples the camera feed for OpenAI Vision."""
    global last_frame_data
    print(f"AI Worker started using {MODEL_ID}...")
    
    while True:
        if last_frame_data:
            try:
                # Convert image to base64
                base64_image = base64.b64encode(last_frame_data).decode('utf-8')
                
                # Call OpenAI Vision API
                response = client.chat.completions.create(
                    model=MODEL_ID,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "What is currently happening in this camera feed? Describe what you see in detail."
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
                    #max_tokens=300
                    max_completion_tokens=3000
                )
                
                ai_response = response.choices[0].message.content
                print(f"\n[{MODEL_ID} - {datetime.now().strftime('%H:%M:%S')}]: {ai_response}")
                
            except Exception as e:
                print(f"[AI Error]: {e}")
        
        # Wait 10 seconds between snapshots to respect rate limits
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
           '<h1>RPi + OpenAI Vision (GPT-4o) Live</h1>' \
           '<img src="/video" style="border:2px solid #0f0; max-width:90%;">' \
           '<p>AI analysis appearing in terminal...</p></body></html>'

@app.route('/video')
def video():
    return Response(get_video_stream(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    # Start AI thread in background
    threading.Thread(target=ai_worker, daemon=True).start()
    # Start web server
    app.run(host='0.0.0.0', port=5000, threaded=True)

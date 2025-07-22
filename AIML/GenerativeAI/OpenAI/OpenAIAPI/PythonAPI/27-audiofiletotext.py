import os
from openai import OpenAI
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_APIUC_KEY"))

# Open .m4a audio file
audio_file_path = "converted_audio.wav"
with open(audio_file_path, "rb") as audio_file:
    # Send the audio file for transcription
    transcription = client.audio.transcriptions.create(
        model="gpt-4o-transcribe",
        file=audio_file
    )

# Save the transcription to a text file
output_file_path = "transcription.txt"
with open(output_file_path, "w", encoding="utf-8") as f:
    f.write(transcription.text)

print(f"Transcription saved to {output_file_path}")


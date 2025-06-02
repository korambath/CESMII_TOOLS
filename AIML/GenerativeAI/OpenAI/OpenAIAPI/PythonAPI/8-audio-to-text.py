import os
import requests
import json
from dotenv import load_dotenv
from openai import OpenAI
import os

from pathlib import Path
file_name = "example.txt"


load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


model = "gpt-4o"

client = OpenAI(api_key=os.getenv("OPENAI_APIUC_KEY"))

directory = Path('.')  # Current directory, or replace with Path('/your/path')
mp3_files = list(directory.glob('*.mp3'))
for file in mp3_files:
    print(file.resolve())


def transcribe_audio(file_path):
    audio_file= open(file_path, "rb")

    transcription = client.audio.transcriptions.create(
        #model="gpt-4o-transcribe", 
        model="whisper-1",
        file=audio_file
    )
    return transcription.text
    
if __name__ == "__main__":
    try:
        while True:
            text = input("\nEnter the name of audiofile (type 'quit' to exit): ")
            full_path = os.path.abspath(text)
            print(full_path)
            if text.lower() == "quit":
                print("Exiting the program...")
                break
            transcript = transcribe_audio(text)
            print(f" Transcript is {transcript}")
    except Exception as e:
        print(f"Error: {str(e)}")



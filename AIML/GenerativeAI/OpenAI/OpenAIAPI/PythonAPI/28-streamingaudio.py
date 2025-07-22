import os
from openai import OpenAI
from dotenv import load_dotenv
from pydub import AudioSegment
from tempfile import NamedTemporaryFile

# Load environment variables
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_APIUC_KEY"))

# Load the full audio file
audio = AudioSegment.from_file("audio1477139941.m4a")

# Split into 30-second chunks (adjust as needed)
chunk_length_ms = 30 * 1000
chunks = [audio[i:i+chunk_length_ms] for i in range(0, len(audio), chunk_length_ms)]

print("Streaming transcription...\n")

for idx, chunk in enumerate(chunks):
    with NamedTemporaryFile(suffix=".m4a", delete=True) as temp_audio:
        chunk.export(temp_audio.name, format="m4a")
        with open(temp_audio.name, "rb") as audio_file:
            response = client.audio.transcriptions.create(
                model="gpt-4o-transcribe",
                file=audio_file
            )
            print(f"[Chunk {idx + 1}] {response.text.strip()}")


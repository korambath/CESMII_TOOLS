# https://platform.openai.com/docs/guides/text-to-speech
import os
from openai import OpenAI, OpenAIError
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
load_dotenv()
#client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
client = OpenAI(api_key=os.getenv("OPENAI_APIUC_KEY"))

speech_file_path = Path(__file__).parent / "speech.mp3"

with client.audio.speech.with_streaming_response.create(
    model="gpt-4o-mini-tts",
    voice="coral",
    input="Today is a wonderful day to build something people love!",
    instructions="Speak in a cheerful and positive tone.",
) as response:
    response.stream_to_file(speech_file_path)

# listen using open speech.mp3 -a QuickTime\ Player 

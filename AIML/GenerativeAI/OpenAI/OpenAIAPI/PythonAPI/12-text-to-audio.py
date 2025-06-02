import os
from openai import OpenAI, OpenAIError
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
load_dotenv()
#client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
client = OpenAI(api_key=os.getenv("OPENAI_APIUC_KEY"))

with client.audio.speech.with_streaming_response.create(
    model="tts-1",
    voice="alloy",
    input="""I see skies of blue and clouds of white
             The bright blessed days, the dark sacred nights
             And I think to myself
             What a wonderful world""",
) as response:
    response.stream_to_file("audio.mp3")

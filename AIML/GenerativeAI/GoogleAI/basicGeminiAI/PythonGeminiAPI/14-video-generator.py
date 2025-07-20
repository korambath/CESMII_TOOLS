from google import genai
import os
import requests
import json
from dotenv import load_dotenv
load_dotenv()

# The client gets the API key from the environment variable `GEMINI_API_KEY`.
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
      raise ValueError("GOOGLE_API_KEY environment variable not set.")
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
model = "gemini-2.5-flash"

import time
from google import genai
from google.genai import types

client = genai.Client()

operation = client.models.generate_videos(
    model="veo-3.0-generate-preview",
    prompt="A Panoromic wide shot of a setting sun slowly disappearing over the horizon from a sea beach",
    config=types.GenerateVideosConfig(
        person_generation="allow_all",  # "allow_adult" and "dont_allow" for Veo 2 only
        aspect_ratio="16:9",  # "16:9", and "9:16" for Veo 2 only
    ),
)

while not operation.done:
    time.sleep(20)
    operation = client.operations.get(operation)

for n, generated_video in enumerate(operation.response.generated_videos):
    client.files.download(file=generated_video.video)
    generated_video.video.save(f"sunsetvideo{n}.mp4")



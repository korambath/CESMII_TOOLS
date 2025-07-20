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

myfile = client.files.upload(file='textspeech.mp3')
prompt = 'Generate a transcript of the speech.'
# Create a prompt containing timestamps.
prompt = "Provide a transcript of the speech from 00:30 to 01:29."

response = client.models.generate_content(
  model='gemini-2.5-flash',
  contents=[prompt, myfile]
)

print(response.text)


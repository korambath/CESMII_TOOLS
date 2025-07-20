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

from google import genai

client = genai.Client()

myfile = client.files.upload(file="out.wav")

response = client.models.generate_content(
    model="gemini-2.5-flash", contents=["Describe this audio clip", myfile]
)

print(response.text)


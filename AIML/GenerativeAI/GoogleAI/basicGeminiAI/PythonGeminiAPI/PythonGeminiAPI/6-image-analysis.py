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

from PIL import Image
from google import genai

client = genai.Client()

#image = Image.open("text-english.png")
image = Image.open("google-airport.png")
image = Image.open("spanish-meal.png")
# Open the image file
image.show()


prompt = '''
Provide a list of all the following attributes:
ingredients, type of cuisine, vegetarian or not, in JSON format
'''
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=[image, prompt]
)
print(response.text)



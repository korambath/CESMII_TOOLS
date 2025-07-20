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
from google.genai import types
from PIL import Image
from io import BytesIO

client = genai.Client()

response = client.models.generate_images(
    model='imagen-4.0-generate-preview-06-06',
    prompt='Robot holding a red skateboard',
    config=types.GenerateImagesConfig(
        number_of_images= 4,
    )
)
i=0
for generated_image in response.generated_images:
  generated_image.image.show()
  img_name = f"img_{i}.png"
  print(f"Image name is {img_name}")
  generated_image.image.save(img_name)
  i=i+1



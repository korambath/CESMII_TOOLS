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
model = "gemini-2.0-flash-preview-image-generation"

from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
import base64

client = genai.Client()

prompt_list = ['a plate of pasta, 100mm Macro lens', 
               'A photo of coffee beans in a kitchen on a wooden surface', 
               'A zoomed out photo of a small bag of coffee beans in a messy kitchen',
               'A photo of a chocolate bar on a kitchen counter',
               'generate an image in the style of an impressionist painting: a wind farm',
               'generate an image in the style of a renaissance painting: a wind farm',
               '4k HDR beautiful photo of a corn stalk taken by a professional photographer',
               'a photo of a corn stalk' ]


for index, value in enumerate(prompt_list):
    print(f" Prompt is {value}")
    response = client.models.generate_content(
        model=model,
        contents=value,
        config=types.GenerateContentConfig(
          response_modalities=['TEXT', 'IMAGE']
        )
    )

    for part in response.candidates[0].content.parts:
      if part.text is not None:
        print(part.text)
      elif part.inline_data is not None:
        img_name = f"image{index}.png"
        image = Image.open(BytesIO((part.inline_data.data)))
        image.save(img_name)
        image.show()


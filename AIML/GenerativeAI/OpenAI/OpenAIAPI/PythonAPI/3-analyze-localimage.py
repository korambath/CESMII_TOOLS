
import os
import requests
import openai
import json
from dotenv import load_dotenv
from openai import OpenAI
import openai
import base64
from pathlib import Path
load_dotenv()
#client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
#client = OpenAI()
client = OpenAI(api_key=os.getenv("OPENAI_APIUC_KEY"))

# Path to the image
image_path = Path('text-english.png')

from PIL import Image

# Open the image file
image = Image.open(image_path)

# Display the image
image.show()


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

base64_image = encode_image(image_path)

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "What is in this image?",
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                },
            ],
        }
    ],
)



#print(response.choices[0])

print(response.choices[0].message.content)



import textwrap

def print_wrapped(text, width=80):
    wrapped_text = textwrap.fill(text, width=width)
    print(wrapped_text)

#print_wrapped(str(response.choices[0].message))







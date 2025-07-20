import time
from google import genai
from google.genai import types
from google import genai
import os
import requests
import json
from dotenv import load_dotenv
load_dotenv()
import os
from PIL import Image
from datetime import datetime
from io import BytesIO

import PIL.Image


# The client gets the API key from the environment variable `GEMINI_API_KEY`.
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
      raise ValueError("GOOGLE_API_KEY environment variable not set.")
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
model = "gemini-2.5-flash"


def save_image_with_timestamp(image_path):
    """
    Opens an image, adds a timestamp to its filename, and saves it.

    Args:
        image_path (str): The path to the original image file.
    """
    try:
        # Open the image
        img = Image.open(image_path)

        # Get the current date and time and format it
        # You can customize the format string as needed
        current_datetime = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

        # Split the original path into root and extension
        root, ext = os.path.splitext(image_path)

        # Create the new filename with the timestamp
        new_filename = f"{root}_{current_datetime}{ext}"

        # Save the image with the new filename
        img.save(new_filename)
        print(f"Image saved successfully as: {new_filename}")
        img.show()

    except FileNotFoundError:
        print(f"Error: Image file not found at {image_path}")
    except Exception as e:
        print(f"An error occurred: {e}")

prompt="Panning wide shot of a calico kitten sleeping in the sunshine"

imagen = client.models.generate_images(
    model="imagen-3.0-generate-002",
    prompt=prompt,
    config=types.GenerateImagesConfig(
      aspect_ratio="16:9",
      number_of_images=1
    )
)

image_path="image1.png"
imagen.generated_images[0].image
imagen.generated_images[0].image.show()
imagen.generated_images[0].image.save(image_path)

save_image_with_timestamp(image_path)

operation = client.models.generate_videos(
    model="veo-2.0-generate-001",
    prompt=prompt,
    image = imagen.generated_images[0].image,
    config=types.GenerateVideosConfig(
      person_generation="dont_allow",  # "dont_allow" or "allow_adult"
      aspect_ratio="16:9",  # "16:9" or "9:16"
      number_of_videos=2
    ),
)

# Wait for videos to generate
while not operation.done:
  time.sleep(20)
  operation = client.operations.get(operation)

for n, video in enumerate(operation.response.generated_videos):
    fname = f'with_image_input{n}.mp4'
    print(fname)
    client.files.download(file=video.video)
    video.video.save(fname)


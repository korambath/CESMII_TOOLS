import os
from dotenv import load_dotenv
import anthropic
import base64
import rich
from PIL import Image

# 1. Load environment variables from the .env file
load_dotenv()

# 2. Get the API key from the environment variable
api_key = os.getenv("ANTHROPIC_API_KEY")

# Check if the API key was loaded successfully
if not api_key:
    raise ValueError("ANTHROPIC_API_KEY not found in .env file.")

# 3. Initialize the Anthropic client with the API key
client = anthropic.Anthropic(
    api_key=api_key,
)


# Replace 'path/to/your/local/image.jpg' with the actual path to your image file.
# You also need to manually specify the correct media type for your image.
image1_path = "images/Camponotus_flavomarginatus_ant.jpg"
image1_media_type = "image/jpeg"


# Open the image file
image = Image.open(image1_path)

# Display the image
image.show()


# Open the local image file in binary read mode ('rb')
with open(image1_path, "rb") as image_file:
    # Read the file and encode its content to base64
    image1_data = base64.b64encode(image_file.read()).decode("utf-8")

message = client.messages.create(
    max_tokens=1024,
    messages=[
      {
        "role": "user",
        "content": [
          {
            "type": "image",
            "source": {
              "type": "base64",
              "media_type": image1_media_type,
              "data": image1_data,
            },
          },
          {
            "type": "text",
            "text": "Describe this image."
          }
        ],
      }
    ],
    model="claude-sonnet-4-20250514",
)
print(f"\nJSON Ouptut \n {message.model_dump_json(indent=2)}")

rich.print(f"\nrich Output \n { message}")

print(f"\nText Only: \n {message.content[0].text}")


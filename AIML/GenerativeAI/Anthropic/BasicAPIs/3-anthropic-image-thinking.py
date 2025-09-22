import os
from dotenv import load_dotenv
import anthropic
import base64
import rich
from PIL import Image

#Docs: https://docs.claude.com/en/docs/build-with-claude/extended-thinking

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

response = client.messages.create(
    max_tokens=2048,
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
     thinking={
     "type": "enabled",
     "budget_tokens": 1024
    },
    model="claude-sonnet-4-20250514",
)

print(f"\nJSON Ouptut \n {response.model_dump_json(indent=2)}")

rich.print(f"\nrich Output \n {response}")

print(f"\nThinking Only: \n {response.content[0].thinking}")

# The response will contain summarized thinking blocks and text blocks
for block in response.content:
    if block.type == "thinking":
        print(f"\nThinking summary: {block.thinking}")
    elif block.type == "text":
        print(f"\nResponse: {block.text}")


print("\n Count tokens \n")

response = client.messages.count_tokens(
    model="claude-opus-4-1-20250805",
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
                    "text": "Describe this image"
                }
            ],
        }
    ],
)
print(f"\nJSON Ouptut \n {response.model_dump_json(indent=2)}")

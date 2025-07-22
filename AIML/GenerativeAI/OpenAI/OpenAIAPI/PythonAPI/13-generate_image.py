# https://platform.openai.com/docs/guides/image-generation?image-generation-model=gpt-image-1#generate-images
import os
from openai import OpenAI, OpenAIError
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
import base64
load_dotenv()
from PIL import Image
#client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
client = OpenAI(api_key=os.getenv("OPENAI_APIUC_KEY"))


#client = OpenAI() 

#model="gpt-4.1-mini"
model="gpt-4o"
prompt="Generate an image of Person on ucla campus"
imagename="ppk2.png"
response = client.responses.create(
    model=model,
    input=prompt,
    tools=[{"type": "image_generation"}],
)

print("saving image")
# Save the image to a file
image_data = [
    output.result
    for output in response.output
    if output.type == "image_generation_call"
]

if image_data:
    image_base64 = image_data[0]
    with open(imagename, "wb") as f:
        f.write(base64.b64decode(image_base64))

# Open the image file
image = Image.open(imagename)
# Display the image
image.show()

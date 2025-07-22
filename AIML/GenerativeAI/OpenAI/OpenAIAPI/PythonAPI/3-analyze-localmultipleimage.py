import os
import base64
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image # For opening/validating images, though not strictly needed for base64 encoding

# Load environment variables from .env file (e.g., OPENAI_API_KEY)
load_dotenv()

# Initialize the OpenAI client. It will automatically pick up the API key
# from the OPENAI_API_KEY environment variable.
client = OpenAI()

# --- Configuration ---
# Define the directory where your images are located.
# Make sure to change this to the actual path on your system.
IMAGE_DIRECTORY = Path('/Users/ppk/DevOps/GenerativeAIDev/OpenAIDev/UVNotebooks/basicGenAI/src/PythonAPIs/Images')

# Supported image file extensions
SUPPORTED_EXTENSIONS = ['.png', '.jpg', '.jpeg']

from PIL import Image




# --- Helper Function to Encode Image ---
def encode_image(image_path):
    """
    Encodes an image file to a base64 string.
    Args:
        image_path (Path): The path to the image file.
    Returns:
        str: The base64 encoded string of the image.
    """
    # Open the image file
    image = Image.open(image_path)
    # Display the image
    image.show()
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except FileNotFoundError:
        print(f"Error: Image file not found at {image_path}")
        return None
    except Exception as e:
        print(f"Error encoding image {image_path}: {e}")
        return None

# --- Main Processing Logic ---
def process_images_in_directory(directory_path):
    """
    Processes all supported image files in a given directory using OpenAI's GPT-4o-mini.
    Args:
        directory_path (Path): The path to the directory containing images.
    """
    if not directory_path.is_dir():
        print(f"Error: Directory not found at {directory_path}")
        return

    print(f"Starting image processing in directory: {directory_path}\n")

    processed_count = 0
    skipped_count = 0

    # Iterate through all files in the specified directory
    for image_file in directory_path.iterdir():
        # Check if the file is a regular file and has a supported image extension
        if image_file.is_file() and image_file.suffix.lower() in SUPPORTED_EXTENSIONS:
            print(f"--- Processing image: {image_file.name} ---")

            # Optional: Open and display the image (for debugging, uncomment if needed)
            # try:
            #     image = Image.open(image_file)
            #     image.show() # This will open a new window for each image, can be intrusive
            # except Exception as e:
            #     print(f"Warning: Could not open/display image {image_file.name}: {e}")

            base64_image = encode_image(image_file)

            if base64_image:
                try:
                    # Make the API call to OpenAI
                    response = client.chat.completions.create(
                        #model="gpt-4o-mini",
                        model="gpt-4.1",
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": "What is in this image? Provide a concise description.",
                                    },
                                    {
                                        "type": "image_url",
                                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                                    },
                                ],
                            }
                        ],
                    )
                    # Print the AI's response
                    print(f"AI Description for {image_file.name}:\n{response.choices[0].message.content}\n")
                    processed_count += 1
                except openai.APIError as e:
                    print(f"API Error processing {image_file.name}: {e}\n")
                except Exception as e:
                    print(f"An unexpected error occurred for {image_file.name}: {e}\n")
            else:
                print(f"Skipping {image_file.name} due to encoding error.\n")
                skipped_count += 1
        else:
            # Skip directories or unsupported file types
            print(f"Skipping {image_file.name} (not a supported image file).\n")
            skipped_count += 1

    print(f"--- Processing Complete ---")
    print(f"Processed {processed_count} images.")
    print(f"Skipped {skipped_count} items (either not images or had errors).\n")

# --- Run the Image Processor ---
if __name__ == "__main__":
    process_images_in_directory(IMAGE_DIRECTORY)

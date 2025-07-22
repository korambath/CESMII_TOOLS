import os
from openai import OpenAI, OpenAIError
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
client = OpenAI(api_key=os.getenv("OPENAI_APIUC_KEY"))

speech_file_path = Path(__file__).parent / "textspeech.mp3"
input_text_file_path = Path(__file__).parent / "sample_document.txt" # Define the path to your input text file

# --- Read input from file ---
try:
    with open(input_text_file_path, "r", encoding="utf-8") as f:
        text_input = f.read()
except FileNotFoundError:
    print(f"Error: The input file '{input_text_file_path}' was not found.")
    print("Please create an 'input.txt' file in the same directory as this script and add your text there.")
    exit()
except Exception as e:
    print(f"An error occurred while reading the input file: {e}")
    exit()
# --- End read input from file ---

if not text_input.strip(): # Check if the file is empty or only contains whitespace
    print("Warning: The input file is empty. No audio will be generated.")
    exit()

print(f"Reading input from: {input_text_file_path}")
print(f"Text to convert: \n---\n{text_input.strip()}\n---")


try:
    with client.audio.speech.with_streaming_response.create(
        model="gpt-4o-mini-tts",
        voice="coral",
        input=text_input, # Use the text read from the file here
        instructions="Speak in a cheerful and positive tone.",
    ) as response:
        response.stream_to_file(speech_file_path)
    print(f"Speech saved to: {speech_file_path}")

except OpenAIError as e:
    print(f"An OpenAI API error occurred: {e}")
    if "rate limit" in str(e).lower():
        print("You might have hit a rate limit. Please wait a moment and try again.")
    elif "invalid api key" in str(e).lower():
        print("Please check your OPENAI_APIUC_KEY in your .env file. It might be incorrect or expired.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")


# listen using open speech.mp3 -a QuickTime\ Player

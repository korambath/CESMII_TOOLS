import openai
import os
from openai import OpenAI

# Set your OpenAI API key (replace with your actual key or load from environment)
# It's recommended to load from an environment variable for security.
# For example: openai.api_key = os.getenv("OPENAI_API_KEY")
#openai.api_key = "YOUR_OPENAI_API_KEY" 

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_APIUC_KEY"))


def transcribe_audio_m4a(audio_file_path):
    """
    Transcribes an M4A audio file to text using OpenAI's Whisper model.

    Args:
        audio_file_path (str): The path to the M4A audio file.

    Returns:
        str: The transcribed text or None if there was an error.
    """
    # Check if the file size exceeds the limit (26MB max for Whisper API)
    file_size = os.path.getsize(audio_file_path)
    max_file_size = 25 * 1024 * 1024  # 25MB in bytes

    if file_size > max_file_size:
        print(f"Error: File size ({file_size} bytes) exceeds the maximum allowed size of 25MB.")
        return None

    try:
        with open(audio_file_path, "rb") as audio_file:
            transcript = openai.Audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text"  # Request plain text output
            )
        return transcript['text']  # Return the transcribed text
    except openai.error.InvalidRequestError as e:
        print(f"Invalid request error: {e}")
        return None
    except openai.error.APIError as e:
        print(f"API error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

if __name__ == "__main__":
    m4a_file = "audio1477139941.m4a"  # Replace with the actual path to your .m4a file

    transcribed_text = transcribe_audio_m4a(m4a_file)

    if transcribed_text:
        print("Transcription successful:")
        print(transcribed_text)
        
        # Optionally, save the transcription to a text file
        output_filename = "transcription.txt"
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(transcribed_text)
        print(f"\nTranscription saved to {output_filename}")
    else:
        print("Transcription failed.")


import openai
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Set up OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

def transcribe_audio_m4a(audio_file_path):
    """
    Transcribes an M4A audio file to text using OpenAI's Whisper model.

    Args:
        audio_file_path (str): The path to the M4A audio file.

    Returns:
        str: The transcribed text or None if there was an error.
    """
    # Check if the file size exceeds the limit (25 MiB max for Whisper API, which is 26,214,400 bytes)
    file_size = os.path.getsize(audio_file_path)
    # The API limit is 26,214,400 bytes. Your code uses 25 * 1024 * 1024 which is also 26,214,400.
    # The error message shows 26,214,400 as the limit.
    max_file_size = 25 * 1024 * 1024 # 25 MiB in bytes (26,214,400 bytes)

    if file_size > max_file_size:
        print(f"Error: File size ({file_size} bytes) exceeds the maximum allowed size of {max_file_size} bytes (25 MiB).")
        return None

    try:
        with open(audio_file_path, "rb") as audio_file:
            transcript = openai.Audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text"
            )
        # The OpenAI Python library for Audio.transcriptions.create directly returns the text if response_format="text"
        # It doesn't return a dictionary with a 'text' key like some older versions or other API calls might.
        return transcript
    except openai.APIStatusError as e: # Catch APIStatusError for HTTP errors like 413
        print(f"API status error during transcription: {e}")
        print(f"Error details: {e.response.json()}") # Print more details from the API response
        return None
    except openai.APIConnectionError as e:
        print(f"API connection error: Could not connect to OpenAI API: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error during transcription: {e}")
        return None

if __name__ == "__main__":
    m4a_file = "audio1477139941.m4a"  # Replace with the actual path to your .m4a file

    # --- IMPORTANT: Ensure 'audio1477139941.m4a' is indeed smaller than 25MB (26,214,400 bytes) ---
    # You will need to process your audio file externally to reduce its size if it's currently over.

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

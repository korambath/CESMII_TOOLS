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
model = "gemini-2.5-flash"


from google import genai
from google.genai import types

client = genai.Client()

import wave

# Set up the wave file to save the output:
def wave_file(filename, pcm, channels=1, rate=24000, sample_width=2):
   with wave.open(filename, "wb") as wf:
      wf.setnchannels(channels)
      wf.setsampwidth(sample_width)
      wf.setframerate(rate)
      wf.writeframes(pcm)


transcript = client.models.generate_content(
   model="gemini-2.0-flash",
   contents="""Generate a short transcript around 100 words that reads
            like it was clipped from a podcast by excited herpetologists.
            The hosts names are Dr. Anya and Liam.""").text

response = client.models.generate_content(
   model="gemini-2.5-flash-preview-tts",
   contents=transcript,
   config=types.GenerateContentConfig(
      response_modalities=["AUDIO"],
      speech_config=types.SpeechConfig(
         multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
            speaker_voice_configs=[
               types.SpeakerVoiceConfig(
                  speaker='Dr. Anya',
                  voice_config=types.VoiceConfig(
                     prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name='Kore',
                     )
                  )
               ),
               types.SpeakerVoiceConfig(
                  speaker='Liam',
                  voice_config=types.VoiceConfig(
                     prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name='Puck',
                     )
                  )
               ),
            ]
         )
      )
   )
)

# ...Code to stream or save the output

data = response.candidates[0].content.parts[0].inline_data.data

file_name='outg.wav'
wave_file(file_name, data) # Saves the file to current directory

import pygame
# Initialize Pygame and the mixer 
pygame.init()
pygame.mixer.init()
      
# Load the sound effect (replace 'path/to/your/sound.wav' with your file)

sound = pygame.mixer.Sound(file_name)
# Play the sound effect
sound.play()
         
# Keep the program running long enough for the sound to play
# In a full game, you would have a game loop handling this.
pygame.time.wait(4000) # waits for 2 seconds
   
# Quit Pygame
pygame.quit()

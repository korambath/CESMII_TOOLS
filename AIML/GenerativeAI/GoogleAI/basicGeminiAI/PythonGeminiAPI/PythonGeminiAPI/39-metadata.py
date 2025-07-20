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


myfile = client.files.upload(file='out.wav')
file_name = myfile.name
myfile = client.files.get(name=file_name)
print(myfile)


print('My files:')
for f in client.files.list():
    print(' ', f.name)


client.files.delete(name=myfile.name)


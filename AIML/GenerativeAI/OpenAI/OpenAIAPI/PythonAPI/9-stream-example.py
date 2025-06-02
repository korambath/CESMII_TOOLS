import os
import requests
import json
from dotenv import load_dotenv
from openai import OpenAI
import os

from pathlib import Path
file_name = "example.txt"


load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


model = "gpt-4o"

client = OpenAI(api_key=os.getenv("OPENAI_APIUC_KEY"))

from openai import OpenAI

stream = client.chat.completions.create(
    model=model,
    messages=[{"role": "user", "content": "Explain why sky is blue."}],
    stream=True,
)
for chunk in stream:
    if chunk.choices[0].delta.content is not None:
        print(chunk.choices[0].delta.content, end="")

#https://platform.openai.com/docs/guides/embeddings?lang=python
import os
import requests
import openai
import json
from dotenv import load_dotenv
from openai import OpenAI
load_dotenv()
#client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
client = OpenAI(api_key=os.getenv("OPENAI_APIUC_KEY"))

response = client.embeddings.create(
    input="Hello World!",
    model="text-embedding-3-small"
)

#print(response.data[0].embedding)
print(response.model_dump_json(indent=4))


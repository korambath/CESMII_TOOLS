import os
import requests
import openai
import json
from dotenv import load_dotenv
from openai import OpenAI
load_dotenv()
#client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
client = OpenAI()
client = OpenAI(api_key=os.getenv("OPENAI_APIUC_KEY"))

from openai import OpenAI

response = client.responses.create(
    model="gpt-4.1",
    input="Write a one-sentence bedtime story about a unicorn.",

)

#print(response.output_text)
print(response.model_dump_json(indent=4))
print(response.output)
print(response.output_text)



exit()

  

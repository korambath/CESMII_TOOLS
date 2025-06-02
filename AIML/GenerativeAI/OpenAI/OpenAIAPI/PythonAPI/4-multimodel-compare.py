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

models = ["gpt-4o", "gpt-4.1", "gpt-4o", "gpt-4o-mini" ]

for element in models:
    print("\n model = ", element)
    response = client.chat.completions.create(
               model=element,
               response_format={ "type": "json_object" },
               messages=[
                 {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
                 {"role": "user", "content": "Who won the world series in 2020?"}
               ]
    )   
    print(response.choices[0].message.content)

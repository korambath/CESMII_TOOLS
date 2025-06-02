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
model="gpt-4.1"

response = client.chat.completions.create(
    model=model,
       messages=[
         {
           "role": "system",
           "content": "You are a helpful assistant.",
        },
         {
           "role": "user",
           "content": "Tell me about the solar system",
         }
       ],
       temperature=0.7,
       max_tokens=64,
       top_p=1
    )

print(response.model_dump_json(indent=4))
print (response.choices[0].message.content)


completion = client.chat.completions.create(
        model="gpt-4.1",
        response_format={"type": "json_object"},
        messages=[
            {
               "role": "user",
               "content": "translate this message to french, italian, spanish, greek: Hello, nice to meet you, reply in json object with key is the language code"
            }
        ]
    )
print(completion.choices[0].message.content)
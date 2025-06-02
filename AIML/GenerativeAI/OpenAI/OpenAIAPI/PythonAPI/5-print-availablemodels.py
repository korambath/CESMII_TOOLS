
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

models = client.models.list()

for model in models.data:
     print(model.model_dump_json(indent=4))  # Uncomment to see full model details in JSON format
    # Uncomment the following line to see the full model details in JSON format
    #print(json.dumps(model.model_dump(), indent=4))  # Print model details in a more readable JSON format
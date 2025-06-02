import os
import requests
import openai
import json
from dotenv import load_dotenv
from openai import OpenAI
load_dotenv()
from openai import AsyncOpenAI
import asyncio
#client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
client = OpenAI(api_key=os.getenv("OPENAI_APIUC_KEY"))

from openai import OpenAI
model="gpt-4.1"

client = AsyncOpenAI(api_key=os.getenv("OPENAI_APIUC_KEY"))

async def main():
    stream = await client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": "Write a tagline for an ice cream shop."}],
        stream=True,
    )
    async for chunk in stream:
        print(chunk.choices[0].delta.content or "", end="")


asyncio.run(main())

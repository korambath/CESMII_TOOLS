import os
from dotenv import load_dotenv
import anthropic

# 1. Load environment variables from the .env file
load_dotenv()

# 2. Get the API key from the environment variable
api_key = os.getenv("ANTHROPIC_API_KEY")

# Check if the API key was loaded successfully
if not api_key:
    raise ValueError("ANTHROPIC_API_KEY not found in .env file.")

# 3. Initialize the Anthropic client with the API key
client = anthropic.Anthropic(
    api_key=api_key,
)

stream = client.messages.create(
    max_tokens=1024,
    messages=[
        {
            "role": "user",
            "content": "Say Hello World!.",
        }
    ],
    model="claude-sonnet-4-20250514",
    stream=True,
)
for event in stream:
    print(event.type)

with client.messages.stream(
 max_tokens=1024,
 messages=[
   {
     "role": "user",
     "content": "Send me a recipe for banana bread.",
   }
 ],
 model="claude-sonnet-4-20250514",
) as stream:
 for text in stream.text_stream:
   print(text)


#import anthropic
#client = anthropic.Anthropic()

print("\nThinking Example\n")

with client.messages.stream(
    model="claude-opus-4-1-20250805",
    max_tokens=20000,
    thinking={
        "type": "enabled",
        "budget_tokens": 16000
    },
    messages=[
        {
            "role": "user",
            "content": "What is 27 * 453?"
        }
    ],
) as stream:
    for event in stream:
        if event.type == "content_block_delta":
            if event.delta.type == "thinking_delta":
                print(event.delta.thinking, end="", flush=True)
            elif event.delta.type == "text_delta":
                print(event.delta.text, end="", flush=True)

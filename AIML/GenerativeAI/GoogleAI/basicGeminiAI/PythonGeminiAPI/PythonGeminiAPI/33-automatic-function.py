from google import genai
import os
import requests
import json
from dotenv import load_dotenv
import asyncio
from google.genai import types

load_dotenv()

# The client gets the API key from the environment variable `GEMINI_API_KEY`.
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY environment variable not set.")

# Configure the generative AI library with the API key
#genai.configure(api_key=api_key)
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

model_name = "gemini-2.5-flash" # Model name

from google import genai
from google.genai import types

# Define the function with type hints and docstring
def get_current_temperature(location: str) -> dict:
    """Gets the current temperature for a given location.

    Args:
        location: The city and state, e.g. San Francisco, CA

    Returns:
        A dictionary containing the temperature and unit.
    """
    # ... (implementation) ...
    return {"temperature": 25, "unit": "Celsius"}

# Configure the client
client = genai.Client()
config = types.GenerateContentConfig(
    tools=[get_current_temperature]
)  # Pass the function itself

#config = types.GenerateContentConfig(
#    tools=[get_current_temperature],
#    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
#)


# Make the request
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="What's the temperature in Boston, MA?",
    config=config,
)

print(response.text)  # The SDK handles the function call and returns the final text


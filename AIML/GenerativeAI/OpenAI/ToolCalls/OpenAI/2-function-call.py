from openai import OpenAI
from dotenv import load_dotenv
import os
import requests
from geopy.geocoders import Nominatim
from typing import Optional, Dict, Any
import json
from litellm import completion
import litellm

# Load environment variables (ensure your .env file has OPENAI_API_KEY)
load_dotenv()

# Check if OpenAI API Key is set
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
print(f"OpenAI API Key set: {'Yes' if OPENAI_API_KEY else 'No (Please set your OPENAI_API_KEY in a .env file)'}")

# Initialize OpenAI client
USE_Ollama=False
if USE_Ollama:
   client = OpenAI(
       base_url="http://localhost:11434/v1",  # Local Ollama API
       api_key="ollama"                       # Dummy key
   )
   model_name="gpt-oss"
else:
   client = OpenAI()
   model_name="gpt-4o"

print(f"Use Ollama? {USE_Ollama} and the model name is {model_name}")


def get_current_weather(location: str, fahrenheit: Optional[bool] = False) -> Dict[str, Any]:
    """
    Get current weather data for a given location.

    Args:
        location: The city and country (e.g., "Los Angeles, CA").
        fahrenheit: If True, temperature will be in Fahrenheit. Otherwise, Celsius.
    Returns:
        A dictionary containing current weather data, or an error message.
    """
    geolocator = Nominatim(user_agent="weather_app_geocoding")
    geo_location = geolocator.geocode(location)

    if not geo_location:
        return {"error": f"Could not find coordinates for location: {location}"}

    latitude = geo_location.latitude
    longitude = geo_location.longitude

    # Construct the API URL for Open-Meteo
    # Note: 'current' parameters for specific data points
    # 'temperature_unit' is correctly handled by Open-Meteo
    unit_param = "fahrenheit" if fahrenheit else "celsius"
    weather_api_url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={latitude}&longitude={longitude}&current=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m&"
        f"temperature_unit={unit_param}"
    )

    try:
        response = requests.get(weather_api_url)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        data = response.json()

        if "current" in data:
            return data["current"]
        else:
            return {"error": "Weather data not found in the API response."}

    except requests.exceptions.RequestException as e:
        return {"error": f"Error fetching weather data: {e}"}
    except json.JSONDecodeError:
        return {"error": "Failed to decode JSON from weather API response."}


# Define the tools for OpenAI API
tools = [{
    "type": "function",
    "function": {  # Use "function" key directly under "type" as per new OpenAI API syntax
        "name": "get_current_weather",
        "description": "Get current temperature and other weather details for a given location.",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City and country, e.g., 'Los Angeles, Paris, France' or 'London, UK'",
                },
                "fahrenheit": {
                    "type": "boolean",
                    "description": "Set to true to get temperature in Fahrenheit. Defaults to Celsius.",
                    "default": False
                }
            },
            "required": ["location"],
            "additionalProperties": False
        }
    }
}]

# Input messages for the OpenAI API call
input_messages = [{"role": "user", "content": "What's the weather like in Los Angeles today, in Fahrenheit?"}]

# Make the initial OpenAI API call
response = client.chat.completions.create( # Use client.chat.completions.create for chat models
    model=model_name,  # gpt-4.1 is not a standard model, consider gpt-4o or gpt-4
    messages=input_messages,
    tools=tools,
    tool_choice="auto" # This is the default, but explicit for clarity
)
print(f"Initial Response: {response}")

# Extract the tool call from the response
# The structure of the response has changed in newer OpenAI Python client versions
tool_calls = response.choices[0].message.tool_calls

if tool_calls:
    for tool_call in tool_calls:
        if tool_call.type == "function":
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)

            print(f"Detected Function Call:")
            print(f"  Function Name: {name}")
            print(f"  Function Arguments: {args}")

            # Call the corresponding Python function
            if name == "get_current_weather":
                function_result = get_current_weather(**args)
                print(f"  Function Result: {function_result}")

                # Optionally, you can send the function result back to the model
                # to get a more natural language response
                messages_with_tool_output = [
                    {"role": "user", "content": input_messages[0]["content"]},
                    {"role": "assistant", "tool_calls": [tool_call]}, # Include the tool_call from the first response
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": name,
                        "content": json.dumps(function_result)
                    }
                ]
                final_response = client.chat.completions.create(
                #final_response = completion(
                    model=model_name,
                    messages=messages_with_tool_output
                )
                print(f"Final AI Response: {final_response.choices[0].message.content}")
            else:
                print(f"Error: Unknown function requested: {name}")
else:
    print("No tool call detected in the response.")
    print(f"AI's direct response: {response.choices[0].message.content}")

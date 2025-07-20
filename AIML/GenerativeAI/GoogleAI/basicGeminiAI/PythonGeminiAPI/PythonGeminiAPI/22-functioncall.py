import datetime
from zoneinfo import ZoneInfo
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
from datetime import datetime
import pytz
import json
import requests
import os
import sys

from google import genai
import os
import requests
import json
from dotenv import load_dotenv
load_dotenv()

# The client gets the API key from the environment variable `GEMINI_API_KEY`.
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
      raise ValueError("GOOGLE_API_KEY environment variable not set.")
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
model = "gemini-2.5-flash"

from google import genai
from google.genai import types

def get_current_time(location: str) -> dict:
    try:
        # Get coordinates for the location
        city = location
        geolocator = Nominatim(user_agent="time_finder")
        location = geolocator.geocode(location)

        if not location:
            return {"error": "City not found"}

        # Get timezone based on coordinates
        tf = TimezoneFinder()
        timezone_str = tf.timezone_at(lng=location.longitude, lat=location.latitude)

        if not timezone_str:
            return {"error": "Timezone not found"}

        # Get current time in that timezone
        timezone = pytz.timezone(timezone_str)
        current_time = datetime.now(timezone)

            #"location": location,
        return {
            "location": city,
            "timezone": timezone_str,
            "local_time": current_time.strftime("%Y-%m-%d %H:%M:%S")
        }

    except Exception as e:
        return {"error": str(e)}



def get_weather(location: str) -> dict:
    try:
        # Step 1: Get coordinates from city name
        geolocator = Nominatim(user_agent="weather_finder")
        geo_data = geolocator.geocode(location)
        
        if not geo_data:
            return {"error": "City location not found"}

        latitude = geo_data.latitude
        longitude = geo_data.longitude

        # Step 2: Fetch weather data from Open-Meteo API
        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={latitude}&longitude={longitude}"
            f"&current=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m"
            f"&temperature_unit=fahrenheit"
        )

        response = requests.get(url)
        data = response.json()

        if "current" not in data:
            return {"error": "Weather data unavailable"}

        current = data["current"]

        return {
            "location": location,
            "latitude": latitude,
            "longitude": longitude,
            "temperature_f": current.get("temperature_2m"),
            "humidity_percent": current.get("relative_humidity_2m"),
            "precipitation_mm": current.get("precipitation"),
            "wind_speed_mph": current.get("wind_speed_10m")
        }

    except Exception as e:
        return {"error": str(e)}



# Define the function declaration for the model
weather_function = {
    "name": "get_weather",
    "description": "Gets the weather for a given location.",
    "parameters": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "The city name, e.g. San Francisco",
            },
        },
        "required": ["location"],
    },
}
# Define the function declaration for the model
time_function = {
    "name": "get_current_time",
    "description": "Gets the current time for a given location.",
    "parameters": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "The city name, e.g. San Francisco",
            },
        },
        "required": ["location"],
    },
}

# Configure the client and tools
client = genai.Client()
tools = types.Tool(function_declarations=[weather_function, time_function])
config = types.GenerateContentConfig(tools=[tools])


# Define user prompt
contents = [
    types.Content(
        role="user", parts=[types.Part(text="What's the current time in London?")]
    )
]

# Send request with function declarations
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=contents,
    config=config,
)

# Check for a function call
if response.candidates[0].content.parts[0].function_call:
    function_call = response.candidates[0].content.parts[0].function_call
    print(f"Function to call: {function_call.name}")
    print(f"Arguments: {function_call.args}")
    #  In a real app, you would call your function here:
    #  result = get_current_temperature(**function_call.args)
    if function_call.name == "get_weather":
       result = get_weather(**function_call.args)
    elif function_call.name == "get_current_time":
       result = get_current_time(**function_call.args)
    print (result)
else:
    print("No function call found in the response.")
    print(response.text)

city="Los Angeles"
#print (get_weather(city))
#print (get_current_time(city))

# Extract tool call details, it may not be in the first part.
tool_call = response.candidates[0].content.parts[0].function_call
print(f"Function to call: {tool_call.name}")
print(f"Arguments: {tool_call.args}")

if tool_call.name == "get_weather":
    result = get_weather(**tool_call.args)
    print(f"Function execution result: {result}")

if tool_call.name == "get_current_time":
    result = get_current_time(**tool_call.args)
    print(f"Function execution result: {result}")


# Create a function response part
function_response_part = types.Part.from_function_response(
    name=tool_call.name,
    response={"result": result},
)

#print(f"DEBUG: {response.candidates[0].content}")
#print(f"DEBUG: {function_response_part}")
# Append function call and result of the function execution to contents
contents.append(response.candidates[0].content) # Append the content from the model's response.
contents.append(types.Content(role="user", parts=[function_response_part])) # Append the function response

final_response = client.models.generate_content(
    model="gemini-2.5-flash",
    config=config,
    contents=contents,
)

print(final_response.text)


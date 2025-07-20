import datetime
from zoneinfo import ZoneInfo
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
from datetime import datetime
import pytz
import json
import requests
import os
from google import genai
from google.genai import types

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

def get_current_time(location: str) -> dict:
    """
    Gets the current time for a given location.
    """
    try:
        # Get coordinates for the location
        geolocator = Nominatim(user_agent="time_finder_app") # Use a unique user_agent
        geo_location = geolocator.geocode(location)

        if not geo_location:
            return {"error": "City not found"}

        # Get timezone based on coordinates
        tf = TimezoneFinder()
        timezone_str = tf.timezone_at(lng=geo_location.longitude, lat=geo_location.latitude)

        if not timezone_str:
            return {"error": "Timezone not found for the given location"}

        # Get current time in that timezone
        timezone = pytz.timezone(timezone_str)
        current_time = datetime.now(timezone)

        return {
            "location": geo_location.address, # Use geo_location.address for a more readable location
            "timezone": timezone_str,
            "local_time": current_time.strftime("%Y-%m-%d %H:%M:%S")
        }

    except Exception as e:
        return {"error": f"An error occurred while getting time: {str(e)}"}


def get_weather(location: str) -> dict:
    """
    Gets the weather for a given location.
    """
    try:
        # Step 1: Get coordinates from city name
        geolocator = Nominatim(user_agent="weather_finder_app") # Use a unique user_agent
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
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        data = response.json()

        if "current" not in data:
            return {"error": "Weather data unavailable from API response"}

        current = data["current"]

        return {
            "location": geo_data.address, # Use geo_data.address for a more readable location
            "latitude": latitude,
            "longitude": longitude,
            "temperature_f": current.get("temperature_2m"),
            "humidity_percent": current.get("relative_humidity_2m"),
            "precipitation_mm": current.get("precipitation"),
            "wind_speed_mph": current.get("wind_speed_10m")
        }

    except requests.exceptions.RequestException as req_err:
        return {"error": f"Network or API request error: {str(req_err)}"}
    except Exception as e:
        return {"error": f"An error occurred while getting weather: {str(e)}"}


# --- New: Define a mapping of available functions ---
# This is your whitelist for functions the AI can call.
AVAILABLE_FUNCTIONS = {
    "get_weather": get_weather,
    "get_current_time": get_current_time,
}


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

# Send request with function declarations
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="What's the weather in London?", # Or try "What time is it in Tokyo?"
    config=config,
)

# --- Modified Logic for Function Call ---
if response.candidates and response.candidates[0].content.parts[0].function_call:
    function_call = response.candidates[0].content.parts[0].function_call
    
    print(f"Function to call: {function_call.name}")
    print(f"Arguments: {function_call.args}")

    function_name = function_call.name
    function_args = function_call.args

    if function_name in AVAILABLE_FUNCTIONS:
        target_function = AVAILABLE_FUNCTIONS[function_name]
        try:
            # You can optionally add argument validation here using inspect.signature
            # For example:
            # sig = inspect.signature(target_function)
            # for arg_name, _ in sig.parameters.items():
            #     if arg_name not in function_args:
            #         print(f"Warning: Missing expected argument '{arg_name}' for function '{function_name}'.")
            #         # Decide how to handle this, e.g., raise an error or fill with default

            result = target_function(**function_args)
            print("Function call result:")
            print(result)
        except TypeError as e:
            print(f"Error calling function '{function_name}' with args {function_args}: {e}")
            print("Please check if the function signature matches the arguments provided by the model.")
        except Exception as e:
            print(f"An unexpected error occurred during function call '{function_name}': {e}")
    else:
        print(f"Error: Function '{function_name}' is not recognized or allowed for execution.")
        print("This function is not in the list of AVAILABLE_FUNCTIONS.")
else:
    print("No function call found in the response.")
    print(f"Model's text response: {response.text}")

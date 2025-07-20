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
print(f"Today's date is {datetime.today()}")

# Initialize the generative model with the defined tools
# Changed 'model' variable name to 'model_name' to avoid conflict later
model_name = "gemini-2.5-flash"

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
    Adds a timeout check for the external API.
    """
    try:
        # Step 1: Get coordinates from city name
        geolocator = Nominatim(user_agent="weather_finder_app") 
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

        # --- MODIFICATION START ---
        # Define a timeout in seconds (e.g., 5 seconds)
        API_TIMEOUT_SECONDS = 30 
        print(f"Timeout for this API is {API_TIMEOUT_SECONDS} seconds")
        
        try:
            response = requests.get(url, timeout=API_TIMEOUT_SECONDS) # Add timeout here
            response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
            data = response.json()

            if "current" not in data:
                return {"error": "Weather data unavailable from API response"}

            current = data["current"]

            return {
                "location": geo_data.address, 
                "latitude": latitude,
                "longitude": longitude,
                "temperature_f": current.get("temperature_2m"),
                "humidity_percent": current.get("relative_humidity_2m"),
                "precipitation_mm": current.get("precipitation"),
                "wind_speed_mph": current.get("wind_speed_10m")
            }
        except requests.exceptions.Timeout:
            return {"error": f"Weather API request timed out after {API_TIMEOUT_SECONDS} seconds."}
        # --- MODIFICATION END ---

    except requests.exceptions.RequestException as req_err:
        return {"error": f"Network or API request error (not a timeout): {str(req_err)}"}
    except Exception as e:
        return {"error": f"An unexpected error occurred while getting weather: {str(e)}"}

def get_weather_forecast(location: str, date: str):
    """Retrieves the weather using Open-Meteo API for a given location (city) and a date (yyyy-mm-dd). Returns a list dictionary with the time and temperature for each hour."""
    geolocator = Nominatim(user_agent="weather-app")
    location = geolocator.geocode(location)
    if location:
        try:
            response = requests.get(f"https://api.open-meteo.com/v1/forecast?latitude={location.latitude}&longitude={location.longitude}&hourly=temperature_2m&start_date={date}&end_date={date}")
            data = response.json()
            return {time: temp for time, temp in zip(data["hourly"]["time"], data["hourly"]["temperature_2m"])}
        except Exception as e:
            return {"error": str(e)}
    else:
        return {"error": "Location not found"}


# --- New: Define a mapping of available functions ---
# This is your whitelist for functions the AI can call.
AVAILABLE_FUNCTIONS = {
    "get_weather": get_weather,
    "get_current_time": get_current_time,
    "get_weather_forecast": get_weather_forecast,
}


# Define the function declaration for the model
weather_function = {
    "name": "get_weather",
    #"description": "Gets the weather for a given location.",
    "description": "Gets the current weather conditions for a given location, including temperature, humidity, precipitation, and wind speed. Use this when asked about 'weather', 'temperature', 'humidity', 'wind', or 'precipitation'.", # <--- MODIFIED DESCRIPTION
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

weather_forecast_function = {
    "name": "get_weather_forecast",
    "description": "Gets the current weather conditions for a given location, (city) and a date (yyyy-mm-dd). Returns a list dictionary with the time and temperature for each hour.",
    "parameters": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "The city name, e.g. San Francisco",
            },
            "date": {
                "type": "string",
                "description": "today's date ",
            },
        },
        "required": ["location", "date"],
    },
}
# Define the function declaration for the model
# Configure the client and tools
client = genai.Client()
tools = types.Tool(function_declarations=[weather_function, time_function, weather_forecast_function])
config = types.GenerateContentConfig(tools=[tools])

print("Welcome! You can ask about weather or time. Type 'exit' to quit.")

while True:
    user_query = input("\nYour query: ")
    if user_query.lower() == 'exit' or user_query.lower() == 'quit':
        print("Exiting chat. Goodbye!")
        break
    # Send request with function declarations
# Define user prompt
    contents = [
        types.Content(
            role="user", parts=[types.Part(text=user_query)]
        )
    ]

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=contents,
        config=config,
    )

    # See thought signatures
    for part in response.candidates[0].content.parts:
      if part.thought_signature:
        print("Thought signature:")
        print(part.thought_signature)


    if response.candidates and response.candidates[0].content.parts[0].function_call:
        function_call = response.candidates[0].content.parts[0].function_call
        
        print(f"DEBUG: Function to call: {function_call.name}")
        print(f"DEBUG: Arguments: {function_call.args}")

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
                # Create a function response part
                function_response_part = types.Part.from_function_response(
                    name=function_call.name,
                    response={"result": result},
                )

                # Append function call and result of the function execution to contents
                contents.append(response.candidates[0].content) # Append the content from the model's response.
                contents.append(types.Content(role="user", parts=[function_response_part])) # Append the function response

                final_response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    config=config,
                    contents=contents,
                )

                print(final_response.text)


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
        print("No function call or text response found in the model's reply.")
        print(f"Model's text response: {response.text}")

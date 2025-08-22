from openai import OpenAI
from dotenv import load_dotenv
import os
import requests
from geopy.geocoders import Nominatim
from typing import Optional, Dict, Any
import json

# Load environment variables (ensure your .env file has OPENAI_API_KEY)
load_dotenv()

# Check if OpenAI API Key is set
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
print(f"OpenAI API Key set: {'Yes' if OPENAI_API_KEY else 'No (Please set your OPENAI_API_KEY in a .env file)'}")

# Initialize OpenAI client
client = OpenAI()

def get_n_day_weather_forecast(location: str, fahrenheit: Optional[bool] = False, num_days: int = 7) -> Dict[str, Any]:
    """
    Get weather data for a given location for the specified number of days.

    Args:
        location: The city and country (e.g., "Paris, France").
        fahrenheit: If True, temperature will be in Fahrenheit. Otherwise, Celsius.
        num_days: Number of days weather is requested. Defaults to 7.
    Returns:
        A dictionary containing the forecast data, or an error message.
    """
    geolocator = Nominatim(user_agent="weather_app_geocoding")
    geo_location = geolocator.geocode(location)

    if not geo_location:
        return {"error": f"Could not find coordinates for location: {location}"}

    latitude = geo_location.latitude
    longitude = geo_location.longitude

    unit_param = "fahrenheit" if fahrenheit else "celsius"
    
    # Corrected Open-Meteo API URL for daily forecast
    # We request daily max/min temperature and precipitation sum
    weather_api_url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={latitude}&longitude={longitude}&"
        f"daily=temperature_2m_max,temperature_2m_min,precipitation_sum&"
        f"temperature_unit={unit_param}&"
        f"forecast_days={num_days}"
    )

    try:
        response = requests.get(weather_api_url)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        data = response.json()

        if "daily" in data:
            # Prepare the result dictionary
            forecast_result = {
                "location": location,
                "unit": "Fahrenheit" if fahrenheit else "Celsius",
                "forecast_days": num_days,
                "daily_data": []
            }
            
            # Open-Meteo returns lists for each daily variable
            times = data["daily"]["time"]
            max_temps = data["daily"]["temperature_2m_max"]
            min_temps = data["daily"]["temperature_2m_min"]
            prec_sums = data["daily"]["precipitation_sum"]

            for i in range(len(times)):
                forecast_result["daily_data"].append({
                    "date": times[i],
                    "max_temperature": max_temps[i],
                    "min_temperature": min_temps[i],
                    "precipitation_sum": prec_sums[i]
                })
            return forecast_result
        else:
            return {"error": "Daily weather data not found in the API response."}

    except requests.exceptions.RequestException as e:
        return {"error": f"Error fetching weather data: {e}"}
    except json.JSONDecodeError:
        return {"error": "Failed to decode JSON from weather API response."}
    except KeyError as e:
        return {"error": f"Missing expected key in API response: {e}. Response: {data}"}


def get_current_weather(location: str, fahrenheit: Optional[bool] = False) -> Dict[str, Any]:
    """
    Get current weather data for a given location.

    Args:
        location: The city and country (e.g., "Paris, France").
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
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "Get current temperature and other weather details for a given location.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City and country, e.g., 'Paris, France' or 'London, UK'",
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
    },
    {
        "type": "function",
        "function": {
            "name": "get_n_day_weather_forecast",
            "description": "Get an N-day weather forecast for a given location, including max/min temperatures and precipitation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and country, e.g., 'San Francisco, USA'",
                    },
                    "fahrenheit": {
                        "type": "boolean",
                        "description": "Set to true to get temperature in Fahrenheit. Defaults to Celsius.",
                        "default": False
                    },
                    "num_days": {
                        "type": "integer",
                        "description": "The number of days to forecast (1 to 16 days).",
                        "minimum": 1,
                        "maximum": 16 # Open-Meteo typically supports up to 16 days forecast
                    }
                },
                # Corrected required parameters: fahrenheit, num_days
                "required": ["location", "num_days"] 
            },
        }
    },
]

# Input messages for the OpenAI API call
# Example for get_current_weather
#input_messages = [{"role": "user", "content": "What's the weather like in Los Angeles, CA  today, in Fahrenheit?"}]

# Example for get_n_day_weather_forecast
input_messages = [{"role": "user", "content": "What's the 3-day weather forecast for Los Angeles, CA  in Celsius?"}]


# Make the initial OpenAI API call
response = client.chat.completions.create(
    model="gpt-4o",
    messages=input_messages,
    tools=tools,
    tool_choice="auto"
)
print(f"Initial Response: {response}")

# Extract the tool call from the response
tool_calls = response.choices[0].message.tool_calls

if tool_calls:
    for tool_call in tool_calls:
        if tool_call.type == "function":
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)

            print(f"Detected Function Call:")
            print(f"  Function Name: {name}")
            print(f"  Function Arguments: {args}")

            # Call the corresponding Python function dynamically
            if name == "get_current_weather":
                function_result = get_current_weather(**args)
            elif name == "get_n_day_weather_forecast":
                function_result = get_n_day_weather_forecast(**args)
            else:
                function_result = {"error": f"Unknown function requested: {name}"}

            print(f"  Function Result: {function_result}")

            # Send the function result back to the model for a natural language response
            messages_with_tool_output = [
                {"role": "user", "content": input_messages[0]["content"]},
                {"role": "assistant", "tool_calls": [tool_call]},
                {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": name,
                    "content": json.dumps(function_result) # Ensure content is a string
                }
            ]
            final_response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages_with_tool_output
            )
            print(f"Final AI Response: {final_response.choices[0].message.content}")
else:
    print("No tool call detected in the response.")
    print(f"AI's direct response: {response.choices[0].message.content}")

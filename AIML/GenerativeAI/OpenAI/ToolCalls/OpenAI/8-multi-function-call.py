from openai import OpenAI
from dotenv import load_dotenv
import os
import requests
from geopy.geocoders import Nominatim
from typing import Optional, Dict, Any
import json
from datetime import datetime
from timezonefinder import TimezoneFinder
import pytz

# Load environment variables (ensure your .env file has OPENAI_API_KEY)
load_dotenv()

# Check if OpenAI API Key is set
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") # Corrected variable name from OPENAI_APIUC_KEY
print(f"OpenAI API Key set: {'Yes' if OPENAI_API_KEY else 'No (Please set your OPENAI_API_KEY in a .env file)'}")

# Initialize OpenAI client
client = OpenAI()

def get_current_time(location: str) -> dict:
    """
    Gets the current time for a given location.

    Args:
        location: The city and country (e.g., "Paris, France").
    Returns:
        A dictionary containing the location, timezone, and local time, or an error message.
    """
    try:
        # Get coordinates for the location
        geolocator = Nominatim(user_agent="time_finder_app")
        geo_location = geolocator.geocode(location)

        if not geo_location:
            return {"error": f"Could not find coordinates for location: {location}"}

        # Get timezone based on coordinates
        tf = TimezoneFinder()
        timezone_str = tf.timezone_at(lng=geo_location.longitude, lat=geo_location.latitude)

        if not timezone_str:
            return {"error": f"Timezone not found for the given location: {location}"}

        # Get current time in that timezone
        timezone = pytz.timezone(timezone_str)
        current_time = datetime.now(timezone)

        return {
            "location": geo_location.address,
            "timezone": timezone_str,
            "local_time": current_time.strftime("%Y-%m-%d %H:%M:%S")
        }

    except Exception as e:
        return {"error": f"An error occurred while getting time: {str(e)}"}


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
            forecast_result = {
                "location": location,
                "unit": "Fahrenheit" if fahrenheit else "Celsius",
                "forecast_days": num_days,
                "daily_data": []
            }
            
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

def send_email(to: str, subject: str, body: str) -> Dict[str, Any]:
    """
    Sends an email to a specified recipient with a given subject and body.
    This is a placeholder function and does not actually send an email.

    Args:
        to: The recipient's email address.
        subject: The subject line of the email.
        body: The main content of the email.
    Returns:
        A dictionary indicating success or failure.
    """
    print(f"\n--- Simulating Email Send ---")
    print(f"To: {to}")
    print(f"Subject: {subject}")
    print(f"Body:\n{body}")
    print(f"-----------------------------\n")
    return {"status": "success", "message": f"Email simulated content {body} to be sent to {to} with subject '{subject}'."}


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
                        "maximum": 16
                    }
                },
                "required": ["location", "num_days"]
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Gets the current time for a given location.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and country, e.g., 'San Francisco, USA'",
                    },
                },
                "required": ["location"]
            },
        }
    },
    {
        "type": "function",
        "function": { # Added "function" key here
            "name": "send_email",
            "description": "Send an email to a given recipient with a subject and message.",
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {
                        "type": "string",
                        "description": "The recipient email address."
                    },
                    "subject": {
                        "type": "string",
                        "description": "Email subject line."
                    },
                    "body": {
                        "type": "string",
                        "description": "Body of the email message."
                    }
                },
                "required": [
                    "to",
                    "subject",
                    "body"
                ],
                "additionalProperties": False
            }
        }
    },
]

# Main loop for user input
while True:
    print("\nAsk about weather (e.g., 'What's the weather in Paris today?' or 'What's the 5-day forecast for London?'),")
    print("ask about time (e.g., 'What time is it in Tokyo?'), or send an email (e.g., 'Send an email to john@example.com about meeting with subject Project Update and body The meeting is rescheduled to tomorrow.').")
    user_input = input("Type 'quit' to exit: ")
    if user_input.lower() == 'quit' or user_input.lower() == 'exit':
        break

    input_messages = [{"role": "user", "content": user_input}]

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=input_messages,
        tools=tools,
        tool_choice="auto"
    )

    tool_calls = response.choices[0].message.tool_calls

    if tool_calls:
        # Collect all function call results
        tool_messages = []
        
        for tool_call in tool_calls:
            if tool_call.type == "function":
                name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)

                print(f"\nDetected Function Call:")
                print(f"  Function Name: {name}")
                print(f"  Function Arguments: {args}")

                function_result = None
                if name == "get_current_weather":
                    function_result = get_current_weather(**args)
                elif name == "get_n_day_weather_forecast":
                    function_result = get_n_day_weather_forecast(**args)
                elif name == "get_current_time":
                    function_result = get_current_time(**args)
                elif name == "send_email": # Added condition for send_email
                    function_result = send_email(**args)
                else:
                    function_result = {"error": f"Unknown function requested: {name}"}

                print(f"  Function Result: {function_result}")

                # Add this tool call result to our collection
                tool_messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": name,
                    "content": json.dumps(function_result)
                })

        # Now send ALL function call results together to get the final response
        messages_with_all_tool_outputs = [
            {"role": "user", "content": user_input},
            {"role": "assistant", "tool_calls": tool_calls},
        ] + tool_messages
        
        final_response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages_with_all_tool_outputs
        )
        print(f"\nFinal AI Response: {final_response.choices[0].message.content}\n")
    else:
        print("No tool call detected in the response.")
        print(f"AI's direct response: {response.choices[0].message.content}\n")

print("Exiting weather application. Goodbye!")

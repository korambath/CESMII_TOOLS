#!/usr/bin/env python
import datetime
from zoneinfo import ZoneInfo
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
from datetime import datetime
from typing import Optional, Dict, Any
import pytz
import json
import requests
import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
load_dotenv()
import yfinance as yf

# The client gets the API key from the environment variable `GEMINI_API_KEY`.
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY environment variable not set.")
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
model = "gemini-2.5-flash"
print(f"Today's date is {datetime.today()}")

# Initialize the generative model with the defined tools
model_name = "gemini-2.5-flash"

def get_stock_price(ticker: str) -> dict:
    """
    Fetches the current price of a given stock ticker.

    Args:
        ticker (str): The stock ticker symbol (e.g., 'AAPL').

    Returns:
        dict: A dictionary containing the stock price and ticker,
              or an error message if the operation fails.
    """
    try:
        stock = yf.Ticker(ticker)
        # Fetching info might raise an exception if the ticker is invalid or no data
        stock_info = stock.info

        price = stock_info.get("currentPrice")
        if price is None:
            price = "Price not available"
            error_message = f"Warning: Could not find 'currentPrice' for {ticker}. Data might be incomplete or key name changed."
        else:
            error_message = None

        return {
            "ticker": ticker,
            "price": price,
            "error": error_message
        }
    except Exception as e:
        return {
            "ticker": ticker,
            "price": "Error fetching price",
            "error": f"An unexpected error occurred: {e}"
        }

def get_stock_info(ticker: str) -> dict:
    """
    Fetches basic information (company name, sector) for a given stock ticker.

    Args:
        ticker (str): The stock ticker symbol (e.g., 'AAPL').

    Returns:
        dict: A dictionary containing the stock ticker, company name, sector,
              and any error messages if the operation fails.
    """
    try:
        stock = yf.Ticker(ticker)
        # Fetching info might raise an exception if the ticker is invalid or no data
        stock_info = stock.info

        company_name = stock_info.get("shortName")
        if company_name is None:
            company_name = "Name not available"
            name_error = f"Warning: Could not find 'shortName' for {ticker}."
        else:
            name_error = None

        sector = stock_info.get("sector")
        if sector is None:
            sector = "Sector not available"
            sector_error = f"Warning: Could not find 'sector' for {ticker}."
        else:
            sector_error = None
        
        # Combine potential warnings
        error_message = []
        if name_error:
            error_message.append(name_error)
        if sector_error:
            error_message.append(sector_error)

        return {
            "ticker": ticker,
            "company_name": company_name,
            "sector": sector,
            "error": " | ".join(error_message) if error_message else None
        }
    except Exception as e:
        return {
            "ticker": ticker,
            "company_name": "Error fetching info",
            "sector": "Error fetching info",
            "error": f"An unexpected error occurred: {e}"
        }


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


def get_weather(location: str, fahrenheit: Optional[bool] = True) -> dict:
    """
    Retrieves the current weather report for a specified city which is passed as location argument 
    This funcion also has a timeout check for the external API which is used to retrieve the information.
    Users can also choose to add a boolean argument for fahrenheit to return the data in celsius if it is set to false.
    Args:
        location (str): The name of the city (e.g., "New York", "London", "Tokyo").
        fahrenheit: If True, temperature will be in Fahrenheit. Otherwise, Celsius.

    Returns:
        dict: A dictionary containing the weather information.
              If 'success', includes a 'report' key with weather details.
              If 'error', includes an 'error_message' key.
    """
    print(f"--- Tool: get_weather called for city: {location} ---") # Log tool execution
    try:
        # Step 1: Get coordinates from city name
        geolocator = Nominatim(user_agent="weather_finder_app") 
        geo_data = geolocator.geocode(location)
        
        if not geo_data:
            return {"error": "City location not found"}

        latitude = geo_data.latitude
        longitude = geo_data.longitude

        # Determine temperature unit based on fahrenheit parameter
        temp_unit = "fahrenheit" if fahrenheit else "celsius"
        temp_key = "temperature_f" if fahrenheit else "temperature_c"
        unit_display = "°F" if fahrenheit else "°C"

        # Step 2: Fetch weather data from Open-Meteo API
        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={latitude}&longitude={longitude}"
            f"&current=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m"
            f"&temperature_unit={temp_unit}"
        )

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
                "temperature_unit": unit_display,
                temp_key: current.get("temperature_2m"),
                "humidity_percent": current.get("relative_humidity_2m"),
                "precipitation_mm": current.get("precipitation"),
                "wind_speed_mph": current.get("wind_speed_10m")
            }
        except requests.exceptions.Timeout:
            return {"error": f"Weather API request timed out after {API_TIMEOUT_SECONDS} seconds."}

    except requests.exceptions.RequestException as req_err:
        return {"error": f"Network or API request error (not a timeout): {str(req_err)}"}
    except Exception as e:
        return {"error": f"An unexpected error occurred while getting weather: {str(e)}"}

def get_weather_forecast(location: str, date: str, fahrenheit: Optional[bool] = True) -> dict:
    """
    Retrieves the weather using Open-Meteo API for a given location (city) and a date (yyyy-mm-dd). 
    Returns hourly weather data including temperature, precipitation, and humidity.
    Args:
        location (str): The name of the city (e.g., "New York", "London", "Tokyo").
        date (str): A date for which weather forecast is needed.
        fahrenheit: If True, temperature will be in Fahrenheit. Otherwise, Celsius.

    Returns:
        dict: A dictionary containing the weather information.
              If 'success', includes a 'report' key with weather details.
              If 'error', includes an 'error_message' key.
    """
    geolocator = Nominatim(user_agent="weather-app")
    geo_location = geolocator.geocode(location)
    if geo_location:
        try:
            # Determine temperature unit based on fahrenheit parameter
            temp_unit = "fahrenheit" if fahrenheit else "celsius"
            temp_key = "temperature_f" if fahrenheit else "temperature_c"
            unit_display = "°F" if fahrenheit else "°C"
            
            # Enhanced API call to include temperature, precipitation, and humidity
            response = requests.get(
                f"https://api.open-meteo.com/v1/forecast?"
                f"latitude={geo_location.latitude}&longitude={geo_location.longitude}&"
                f"hourly=temperature_2m,relative_humidity_2m,precipitation&"
                f"temperature_unit={temp_unit}&"
                f"start_date={date}&end_date={date}"
            )
            response.raise_for_status()
            data = response.json()
            
            if "hourly" not in data:
                return {"error": "Hourly weather data not available"}
            
            hourly_data = data["hourly"]
            times = hourly_data.get("time", [])
            temperatures = hourly_data.get("temperature_2m", [])
            humidity = hourly_data.get("relative_humidity_2m", [])
            precipitation = hourly_data.get("precipitation", [])
            
            # Create comprehensive hourly forecast
            forecast_result = {
                "location": location,
                "date": date,
                "temperature_unit": unit_display,
                "hourly_forecast": []
            }
            
            for i in range(len(times)):
                forecast_result["hourly_forecast"].append({
                    "time": times[i],
                    temp_key: temperatures[i] if i < len(temperatures) else None,
                    "humidity_percent": humidity[i] if i < len(humidity) else None,
                    "precipitation_mm": precipitation[i] if i < len(precipitation) else None
                })
            
            return forecast_result
            
        except requests.exceptions.RequestException as e:
            return {"error": f"API request failed: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
    else:
        return {"error": "Location not found"}


def get_n_day_weather_forecast(location: str, fahrenheit: Optional[bool] = False, num_days: int = 7) -> Dict[str, Any]:
    """
    Get weather data for a given location for the specified number of days.

    Args:
        location: The city and country (e.g., "Paris, France").
        fahrenheit: If True, temperature will be in Fahrenheit. Otherwise, Celsius.
        num_days: Number of days weather is requested. Defaults to 7.
    Returns:
        dict: A dictionary containing the forecast data, or an error message.
        If 'success', includes a 'report' key with weather details.
        If 'error', includes an 'error_message' key.
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

def get_exchange_rate(currency_from: str, currency_to: str, currency_date: str) -> Dict[str, Any]:
    """
    Get the exchange rate for currencies between countries

    Args:
        currency_from: Exchange currency from (e.g., 'EUR', 'GBP')
        currency_to: Exchange currency to (e.g., 'USD', 'JPY')
        currency_date: Exchange date in YYYY-MM-DD format or 'latest'
    Returns:
        A dictionary containing the currency exchange rate and related information
    """
    try:
        # Build the API URL
        if currency_date.lower() == 'latest':
            url = "https://api.frankfurter.app/latest"
        else:
            url = f"https://api.frankfurter.app/{currency_date}"
        
        # Set up parameters for the API call
        params = {
            'from': currency_from.upper(),
            'to': currency_to.upper()
        }
        
        # Make the API request
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        # Parse the JSON response
        data = response.json()
        
        # Extract the exchange rate
        if 'rates' in data and currency_to.upper() in data['rates']:
            exchange_rate = data['rates'][currency_to.upper()]
            return {
                "success": True,
                "date": data.get('date', currency_date),
                "base_currency": data.get('base', currency_from.upper()),
                "target_currency": currency_to.upper(),
                "exchange_rate": exchange_rate,
                "conversion_info": f"1 {currency_from.upper()} = {exchange_rate} {currency_to.upper()}"
            }
        else:
            return {
                "success": False,
                "error": f"Exchange rate not found for {currency_from.upper()} to {currency_to.upper()}",
                "available_currencies": list(data.get('rates', {}).keys()) if 'rates' in data else []
            }
            
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"API request failed: {str(e)}"
        }
    except json.JSONDecodeError as e:
        return {
            "success": False,
            "error": f"Failed to parse API response: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"An unexpected error occurred: {str(e)}"
        }

# --- Define a mapping of available functions ---
# This is your whitelist for functions the AI can call.
AVAILABLE_FUNCTIONS = {
    "get_weather": get_weather,
    "get_current_time": get_current_time,
    "get_weather_forecast": get_weather_forecast,
    "get_n_day_weather_forecast": get_n_day_weather_forecast,
    "get_exchange_rate": get_exchange_rate,
    "get_stock_price": get_stock_price,
    "get_stock_info": get_stock_info,
}

# Define the function declarations for the model

stock_price_function = {
    "name": "get_stock_price",
    "description": "Gets the current stock price for a ticker or stock symbol, an abbreviation used to uniquely identify publicly traded shares of a particular stock.",
    "parameters": {
        "type": "object",
        "properties": {
            "ticker": {
                "type": "string",
                "description": "The stock symbol AAPL e.g. for Apple Inc.  ",
            },
        },
        "required": ["ticker"],
    },
}

stock_info_function = {
    "name": "get_stock_info",
    "description": "Gets the stock information for a ticker or stock symbol, an abbreviation used to uniquely identify publicly traded shares of a particular stock.",
    "parameters": {
        "type": "object",
        "properties": {
            "ticker": {
                "type": "string",
                "description": "The stock symbol AAPL e.g. for Apple Inc.  ",
            },
        },
        "required": ["ticker"],
    },
}
weather_function = {
    "name": "get_weather",
    "description": "Gets the current weather conditions for a given location, including temperature, humidity, precipitation, and wind speed. Temperature can be in Fahrenheit or Celsius. Use this when asked about 'weather', 'temperature', 'humidity', 'wind', or 'precipitation'.",
    "parameters": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "The city name, e.g. San Francisco",
            },
            "fahrenheit": {
                "type": "boolean",
                "description": "Set to true to get temperature in Fahrenheit, false for Celsius. Defaults to Fahrenheit (true).",
                "default": True
            },
        },
        "required": ["location"],
    },
}

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
    "description": "Gets hourly weather forecast for a given location (city) and specific date (yyyy-mm-dd). Returns detailed hourly data including temperature, humidity (%), and precipitation (mm) for each hour of the specified day. Temperature can be in Fahrenheit or Celsius.",
    "parameters": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "The city name, e.g. San Francisco",
            },
            "date": {
                "type": "string",
                "description": "Specific date in YYYY-MM-DD format, e.g. 2024-07-29",
            },
            "fahrenheit": {
                "type": "boolean",
                "description": "Set to true to get temperature in Fahrenheit, false for Celsius. Defaults to Fahrenheit (true).",
                "default": True
            },
        },
        "required": ["location", "date"],
    },
}

n_day_weather_forecast_function = {
    "name": "get_n_day_weather_forecast",
    "description": "Get an N-day weather forecast for a given location, including max/min temperatures and precipitation.. Returns a list dictionary with the temperature, precipitation, humidity, wind speed for each day.",
    "parameters": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "The city name, e.g. San Francisco",
            },
            "fahrenheit": {
                "type": "boolean",
                "description": "Set to true to get temperature in Fahrenheit. Defaults to Celsius.",
                "default": False
            },
            "num_days": {
                "type": "integer",
                "description": "The number of days to forecast (1 to 16 days).",
            },
        },
        "required": ["location", "num_days"],
    },
}

exchange_rate_function = {
    "name": "get_exchange_rate",
    "description": "Get the exchange rate for currencies between countries",
    "parameters": {
        "type": "object",
        "properties": {
            "currency_date": {
                "type": "string",
                "description": "A date that must always be in YYYY-MM-DD format or the value 'latest' if a time period is not specified"
            },
            "currency_from": {
                "type": "string",
                "description": "The currency to convert from in ISO 4217 format"
            },
            "currency_to": {
                "type": "string",
                "description": "The currency to convert to in ISO 4217 format"
            },
        },
        "required": [
            "currency_from",
            "currency_to",
            "currency_date",
        ],
    },
}

# Configure the client and tools
client = genai.Client()
tools = types.Tool(function_declarations=[
    weather_function, 
    time_function, 
    weather_forecast_function,
    n_day_weather_forecast_function,
    exchange_rate_function,
    stock_price_function,
    stock_info_function,
])
config = types.GenerateContentConfig(tools=[tools])

# Initialize conversation history
conversation_history = []

print("🌍 Welcome to the Smart Travel Assistant with Chat Memory! 🌍")
print("I can help you with travel-related information and remember our conversation!")
print("Available services:")
print("what are the tools you have?")
print("• Current weather and forecasts for multiple cities")
print("• Local time in different cities")
print("• Currency exchange rates, stock prices or stock informaton")
print("• Multi-city weather comparisons")
print("• Location recommendations based on weather")
print("\nSmart Chat Features:")
print("• I remember previous queries and can build upon them")
print("• Compare weather across multiple cities")
print("• Make location decisions based on weather conditions")
print("• Remember currencies and exchange rates from our conversation")
print("• Type 'clear' to clear conversation history")
print("• Type 'history' to see our conversation")
print("• Type 'exit' to quit")
print("\nMulti-City Weather Examples:")
print("- 'What's the weather in Paris?'")
print("- 'What about London?' (I'll remember Paris from previous query)")
print("- 'What's the latest currency exchange rate beween EUR and USD?'")
print("- 'What is the stock price for AAPL?'")
print("- 'Give me stock information for AAPL?'")
print("- 'Which city has better weather?' (I'll compare the cities we discussed)")
print("- 'Should I visit there?' (I'll refer to the most recent location)")
print("- 'Compare weather in Tokyo, Seoul, and Bangkok'")
print("- 'Which of these cities is warmest?' (after discussing multiple cities)")
print("\nLocation Decision Examples:")
print("- 'I'm planning a trip - check weather in Rome and Barcelona'")
print("- 'Which would be better for outdoor activities?'")
print("- 'What about the exchange rates for those countries?'")
print("- 'Show me the 3-day forecast for the city with better weather'")
print("-" * 70)

def process_query(user_query, conversation_history):
    """Process a user query with conversation context"""
    
    # Add user query to conversation history
    conversation_history.append({
        "role": "user",
        "content": user_query,
        "timestamp": datetime.now().strftime("%H:%M:%S")
    })
    
    # Build the conversation context for the AI
    # Include recent conversation history for context
    context_messages = []
    
    # Enhanced system instruction for multi-city weather and location decisions
    system_instruction = """You are a helpful travel assistant with memory of our conversation. You can access weather, time, and exchange rate information for multiple locations. 

Key capabilities:
- Remember previous cities, weather conditions, and currencies or stock information discussed
- Compare weather across multiple cities when asked
- Help make location decisions based on weather conditions
- Use context like 'there', 'also', 'what about', 'compared to', 'better weather', etc.
- When user asks about weather in multiple cities, call the weather function for each city
- When user asks for location recommendations, consider weather data from previous queries
- Remember exchange rates and currencies from previous conversations

Examples of contextual understanding:
- If user asks "What's the weather in Paris?" then "What about London?", check both cities
- If user asks "Which city has better weather?" compare the most recently discussed cities
- If user asks "Should I go there?" refer to the most recent location discussed
- Remember currency pairs and dates for follow-up exchange rate queries"""
    
    # Add recent conversation history (last 20 exchanges to keep context manageable)
    recent_history = conversation_history[-20:] if len(conversation_history) > 20 else conversation_history
    
    for entry in recent_history[:-1]:  # Exclude the current query
        if entry["role"] == "user":
            context_messages.append(types.Content(role="user", parts=[types.Part(text=entry["content"])]))
        elif entry["role"] == "assistant":
            context_messages.append(types.Content(role="model", parts=[types.Part(text=entry["content"])]))
    
    # Add the current query
    context_messages.append(types.Content(role="user", parts=[types.Part(text=user_query)]))
    
    return context_messages

def display_conversation_history():
    """Display the conversation history"""
    if not conversation_history:
        print("No conversation history yet.")
        return
    
    print("\n📜 Conversation History:")
    print("-" * 40)
    for entry in conversation_history:
        role_icon = "🙋" if entry["role"] == "user" else "🤖"
        print(f"{role_icon} [{entry['timestamp']}] {entry['role'].upper()}: {entry['content'][:100]}{'...' if len(entry['content']) > 100 else ''}")
    print("-" * 40)

def get_recent_locations():
    """Extract recently mentioned locations from conversation history"""
    recent_locations = []
    location_keywords = ['weather', 'time', 'forecast', 'temperature', 'rain', 'sunny', 'cloudy']
    
    # Look through recent conversation for location mentions
    for entry in conversation_history[-10:]:  # Last 10 entries
        if entry["role"] == "user":
            content = entry["content"].lower()
            # Simple extraction - in a real app, you'd use NLP
            for keyword in location_keywords:
                if keyword in content:
                    # Extract potential city names (this is a simple heuristic)
                    words = content.split()
                    for i, word in enumerate(words):
                        if keyword in word and i > 0:
                            potential_location = words[i-1].strip('.,?!')
                            if len(potential_location) > 2 and potential_location not in recent_locations:
                                recent_locations.append(potential_location.title())
    
    return recent_locations[:5]  # Return up to 5 recent locations

def show_conversation_summary():
    """Show a summary of the conversation including recent locations and topics"""
    if not conversation_history:
        print("No conversation history yet.")
        return
    
    print("\n📊 Conversation Summary:")
    print("-" * 40)
    print(f"Total exchanges: {len([h for h in conversation_history if h['role'] == 'user'])}")
    
    recent_locations = get_recent_locations()
    if recent_locations:
        print(f"Recent locations discussed: {', '.join(recent_locations)}")
    
    # Count function types used
    function_calls = []
    for entry in conversation_history:
        if "function: get_weather" in entry.get("content", "").lower():
            function_calls.append("weather")
        elif "function: get_current_time" in entry.get("content", "").lower():
            function_calls.append("time")
        elif "function: get_exchange_rate" in entry.get("content", "").lower():
            function_calls.append("exchange_rate")
    
    if function_calls:
        print(f"Services used: {', '.join(set(function_calls))}")
    
    print("-" * 40)

while True:
    user_query = input("\n💬 Your travel query: ")
    
    # Handle special commands
    if user_query.lower() == 'exit' or user_query.lower() == 'quit':
        print("Safe travels! Goodbye! ✈️")
        break
    elif user_query.lower() == 'clear':
        conversation_history = []
        print("🧹 Conversation history cleared!")
        continue
    elif user_query.lower() == 'history':
        display_conversation_history()
        continue
    elif user_query.lower() == 'summary':
        show_conversation_summary()
        continue
    elif user_query.lower() == 'help':
        print("\n🆘 Available Commands:")
        print("• 'clear' - Clear conversation history")
        print("• 'history' - Show full conversation history")
        print("• 'summary' - Show conversation summary with recent locations")
        print("• 'help' - Show this help message")
        print("• 'exit' or 'quit' - Exit the application")
        print("\n💡 Multi-City Weather Tips:")
        print("• Ask about weather in one city, then say 'What about [other city]?'")
        print("• Say 'Compare weather in [city1] and [city2]'")
        print("• Ask 'Which has better weather?' after discussing multiple cities")
        print("• Say 'Should I go there?' to get recommendations for recent locations")
        continue
    elif not user_query.strip():
        print("Please enter a valid query or type 'help' for available commands.")
        continue

    try:
        # Process the query with conversation context
        contents = process_query(user_query, conversation_history)
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config=config,
        )

        # Check if there are any function calls in the response
        function_calls_found = False
        function_response_parts = []
        
        #print(f"DEBUG: {response.candidates[0].content.parts}")
        if response.candidates and response.candidates[0].content.parts:
            # Iterate through all parts to find function calls
            for part in response.candidates[0].content.parts:
                if part.function_call:
                    function_calls_found = True
                    function_call = part.function_call
                    
                    print(f"🔧 Calling function: {function_call.name}")
                    # print(f"   Arguments: {function_call.args}")

                    function_name = function_call.name
                    function_args = function_call.args

                    if function_name in AVAILABLE_FUNCTIONS:
                        target_function = AVAILABLE_FUNCTIONS[function_name]
                        try:
                            result = target_function(**function_args)
                            print(f"✅ Got {function_name} data")
                            
                            # Create a function response part
                            function_response_part = types.Part.from_function_response(
                                name=function_call.name,
                                response={"result": result},
                            )
                            function_response_parts.append(function_response_part)
                            
                        except TypeError as e:
                            print(f"❌ Error calling function '{function_name}': {e}")
                        except Exception as e:
                            print(f"❌ Unexpected error during function call '{function_name}': {e}")
                    else:
                        print(f"❌ Function '{function_name}' is not available.")
        
        # Generate final response
        final_response_text = ""
        if function_calls_found and function_response_parts:
            # Append function call and results to contents
            contents.append(response.candidates[0].content)  # Append the model's response
            contents.append(types.Content(role="user", parts=function_response_parts))  # Append all function responses

            # Generate final response with all function results
            final_response = client.models.generate_content(
                model="gemini-2.5-flash",
                config=config,
                contents=contents,
            )
            final_response_text = final_response.text
            print(f"\n🎯 {final_response_text}")
        elif not function_calls_found:
            final_response_text = response.text
            print(f"\n🤖 {final_response_text}")
        else:
            final_response_text = "I found some information but couldn't process it properly. Please try again."
            print(f"\n⚠️ {final_response_text}")
        
        # Add assistant response to conversation history
        conversation_history.append({
            "role": "assistant",
            "content": final_response_text,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })
            
    except Exception as e:
        error_msg = f"An error occurred: {e}"
        print(f"\n❌ {error_msg}")
        conversation_history.append({
            "role": "assistant",
            "content": error_msg,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })
    
    print("\n" + "="*60)

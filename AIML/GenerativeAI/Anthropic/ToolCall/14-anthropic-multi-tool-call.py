import anthropic

import os
from dotenv import load_dotenv
import anthropic
from geopy.geocoders import Nominatim
import json
import requests
from typing import Optional, Dict, Any
import rich
import yfinance as yf
from datetime import datetime
import pytz
from timezonefinder import TimezoneFinder


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

def get_current_time(city: str) -> dict:
    """
      Returns the current date at the city
    """
    try:
        # Get coordinates for the city
        geolocator = Nominatim(user_agent="time_finder")
        location = geolocator.geocode(city)
        
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

        return {
            "city": city,
            "timezone": timezone_str,
            "local_time": current_time.strftime("%Y-%m-%d %H:%M:%S")
        }

    except Exception as e:
        return {"error": str(e)}


def get_exchange_rate(currency_from: str, currency_to: str, currency_date: str) -> Dict[str, Any]:
    """
    Get the exchange rate for currencies between countries. Give the latest or current value if not date is given

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


def get_stock_price(ticker: str) -> dict:
    """
    Fetches the current (latest) price of a given stock ticker.

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

def get_weather(location: str, unit: str = "fahrenheit") -> dict:
    """
    Calls an external weather API with location information and returns the current weather data
    
    Args:
        location (str): The city and state, e.g. San Francisco, CA
        unit (str): Temperature unit, either "celsius" or "fahrenheit" (default: "fahrenheit")
    
    Returns:
        dict: Weather data including temperature, humidity, precipitation, and wind speed
    """
    try:
        # Validate temperature unit
        if unit.lower() not in ["celsius", "fahrenheit"]:
            return {"error": f"Invalid temperature unit: {unit}. Must be 'celsius' or 'fahrenheit'"}
        
        # Step 1: Get coordinates from city name
        geolocator = Nominatim(user_agent="weather_finder")
        geo_data = geolocator.geocode(location)

        if not geo_data:
            return {"error": "City not found"}

        latitude = geo_data.latitude
        longitude = geo_data.longitude

        # Step 2: Fetch weather data from Open-Meteo API
        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={latitude}&longitude={longitude}"
            f"&current=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m"
            f"&temperature_unit={unit.lower()}"
        )

        response = requests.get(url)
        data = response.json()

        if "current" not in data:
            return {"error": "Weather data unavailable"}

        current = data["current"]

        # Determine temperature key based on unit
        temp_key = "temperature_f" if unit.lower() == "fahrenheit" else "temperature_c"
        temp_unit_symbol = "°F" if unit.lower() == "fahrenheit" else "°C"

        return {
            "location": location,
            "latitude": latitude,
            "longitude": longitude,
            temp_key: current.get("temperature_2m"),
            "temperature_unit": temp_unit_symbol,
            "humidity_percent": current.get("relative_humidity_2m"),
            "precipitation_mm": current.get("precipitation"),
            "wind_speed_mph": current.get("wind_speed_10m")
        }

    except Exception as e:
        return {"error": str(e)}

def get_n_day_weather_forecast(location: str, unit: str = "fahrenheit", num_days: int = 7) -> Dict[str, Any]:
    """
    Get weather forecast data for a given location for the specified number of days.

    Args:
        location: The city and country (e.g., "Paris, France").
        unit: Temperature unit, either "celsius" or "fahrenheit" (default: "fahrenheit").
        num_days: Number of days weather is requested. Defaults to 7.
    Returns:
        dict: A dictionary containing the forecast data, or an error message.
        If 'success', includes a 'report' key with weather details.
        If 'error', includes an 'error_message' key.
    """
    # Validate temperature unit
    if unit.lower() not in ["celsius", "fahrenheit"]:
        return {"error": f"Invalid temperature unit: {unit}. Must be 'celsius' or 'fahrenheit'"}
    
    geolocator = Nominatim(user_agent="weather_app_geocoding")
    geo_location = geolocator.geocode(location)

    if not geo_location:
        return {"error": f"Could not find coordinates for location: {location}"}

    latitude = geo_location.latitude
    longitude = geo_location.longitude

    unit_param = unit.lower()
    
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
                "unit": unit.capitalize(),
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


weather_tool = {
    "name": "get_weather",
    "description": "Retrieves current weather conditions for any city worldwide. Provides real-time data including temperature, humidity, precipitation, and wind speed from reliable meteorological sources. The tool can return temperature in either Celsius or Fahrenheit (defaults to Fahrenheit). Use this when users ask about current weather conditions, temperature, or atmospheric conditions for a specific location. It will not provide weather forecasts or historical weather data.",
    "input_schema": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "The city and state, e.g. San Francisco, CA"
            },
            "unit": {
                "type": "string",
                "enum": ["celsius", "fahrenheit"],
                "description": "The unit of temperature, either \"celsius\" or \"fahrenheit\"",
                "default": "fahrenheit"
            }
        },
        "required": ["location"]
    }
}

stock_tool = {
    "name": "get_stock_price",
    "description": "Retrieves the current stock price for a given ticker symbol. The ticker symbol must be a valid symbol for a publicly traded company on a major US stock exchange like NYSE or NASDAQ. The tool will return the latest trade price in USD. It should be used when the user asks about the current or most recent price of a specific stock. It will not provide any other information about the stock or company.",
    "input_schema": {
        "type": "object",
        "properties": {
            "ticker": {
                "type": "string",
                "description": "The stock ticker symbol, e.g. AAPL, GOOGL, TSLA"
            }
        },
        "required": ["ticker"]
    }
}


stock_info_tool = {
    "name": "get_stock_info",
    "description": "Retrieves comprehensive company information for a given stock ticker symbol, including company name, business sector, and industry classification. The ticker symbol must be a valid symbol for a publicly traded company on major US stock exchanges like NYSE or NASDAQ. Use this when users want to know about a company's business details, what sector they operate in, or general corporate information. It will not provide financial metrics, stock prices, or trading data.",
    "input_schema": {
        "type": "object",
        "properties": {
            "ticker": {
                "type": "string",
                "description": "The stock ticker symbol, e.g. AAPL, GOOGL, TSLA"
            }
        },
        "required": ["ticker"]
    }
}

exchange_rate_tool = {
    "name": "get_exchange_rate",
    "description": "Retrieves accurate currency exchange rates between any two major world currencies for a specific date or current rates. Uses reliable financial data sources to provide real-time or historical exchange rate information. Supports all major currencies including USD, EUR, GBP, JPY, CAD, AUD, CHF, and many others. Use this when users need currency conversion rates, want to know exchange rates for travel or business, or need historical exchange rate data. The tool can provide rates for any past date or the most current available rates.",
    "input_schema": {
        "type": "object",
        "properties": {
            "currency_from": {
                "type": "string",
                "description": "The source currency code (e.g., USD, EUR, GBP, JPY)"
            },
            "currency_to": {
                "type": "string", 
                "description": "The target currency code (e.g., USD, EUR, GBP, JPY)"
            },
            "currency_date": {
                "type": "string",
                "description": "The date for exchange rate in YYYY-MM-DD format, or 'latest' for current rates"
            }
        },
        "required": ["currency_from", "currency_to", "currency_date"]
    }
}

current_time_tool = {
    "name": "get_current_time",
    "description": "Retrieves the current local time for any city or location worldwide, automatically accounting for time zones and daylight saving time adjustments. Uses geographic coordinates to determine the precise time zone and provides accurate local time information. Use this when users want to know what time it is in a specific city, need to coordinate across time zones, or want to check local time before making calls or scheduling meetings. The tool will return the time in standard YYYY-MM-DD HH:MM:SS format along with the time zone information.",
    "input_schema": {
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "The name of the city to get the current time for (e.g., 'New York', 'London', 'Tokyo')"
            }
        },
        "required": ["city"]
    }
}

weather_forecast_tool = {
    "name": "get_n_day_weather_forecast",
    "description": "Retrieves detailed weather forecast for any city worldwide for a specified number of days (1-16 days). Provides daily forecast data including maximum and minimum temperatures and precipitation amounts from reliable meteorological sources. The tool can return temperature in either Celsius or Fahrenheit (defaults to Fahrenheit). Use this when users ask about weather forecasts, future weather conditions, or want to plan activities based on upcoming weather. It will not provide current weather conditions or historical weather data.",
    "input_schema": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "The city and country, e.g. Paris, France or New York, USA"
            },
            "unit": {
                "type": "string",
                "enum": ["celsius", "fahrenheit"],
                "description": "The unit of temperature, either \"celsius\" or \"fahrenheit\"",
                "default": "fahrenheit"
            },
            "num_days": {
                "type": "integer",
                "description": "Number of forecast days (1-16), defaults to 7",
                "minimum": 1,
                "maximum": 16,
                "default": 7
            }
        },
        "required": ["location"]
    }
}

# List of all available tools
available_tools = [weather_tool, weather_forecast_tool, stock_tool, stock_info_tool, exchange_rate_tool, current_time_tool]

def process_user_request(user_input):
    """
    Process user request for weather or stock information using Claude and available tools
    """
    messages = [{"role": "user", "content": user_input}]

    response = client.messages.create(
        model="claude-opus-4-1-20250805",
        max_tokens=1024,
        tools=available_tools,
        messages=messages
    )

    print(f"\n=== Processing Request: {user_input} ===")
    
    # Check if Claude wants to use a tool
    if response.stop_reason == "tool_use":
        print("🔧 Processing tool calls...")
        
        # Add assistant's response to conversation
        messages.append({"role": "assistant", "content": response.content})
        
        # Process each tool use in the response
        tool_results = []
        for content_block in response.content:
            if content_block.type == "tool_use":
                tool_name = content_block.name
                tool_input = content_block.input
                tool_use_id = content_block.id
                
                print(f"🔍 Using tool: {tool_name}")
                print(f"📝 Tool input: {tool_input}")
                
                # Call the appropriate function
                if tool_name == "get_weather":
                    # Get unit parameter, default to "fahrenheit" if not provided
                    unit = tool_input.get("unit", "fahrenheit")
                    print(f"🌤️  Getting weather data for: {tool_input['location']} (unit: {unit})")
                    result = get_weather(tool_input["location"], unit)
                elif tool_name == "get_n_day_weather_forecast":
                    # Get unit and num_days parameters with defaults
                    unit = tool_input.get("unit", "fahrenheit")
                    num_days = tool_input.get("num_days", 7)
                    print(f"🌦️  Getting {num_days}-day weather forecast for: {tool_input['location']} (unit: {unit})")
                    result = get_n_day_weather_forecast(tool_input["location"], unit, num_days)
                elif tool_name == "get_stock_price":
                    print(f"📈 Getting stock price for: {tool_input['ticker']}")
                    result = get_stock_price(tool_input["ticker"])
                elif tool_name == "get_stock_info":
                    print(f"ℹ️  Getting stock info for: {tool_input['ticker']}")
                    result = get_stock_info(tool_input["ticker"])
                elif tool_name == "get_exchange_rate":
                    print(f"💱 Getting exchange rate from {tool_input['currency_from']} to {tool_input['currency_to']} for {tool_input['currency_date']}")
                    result = get_exchange_rate(tool_input["currency_from"], tool_input["currency_to"], tool_input["currency_date"])
                elif tool_name == "get_current_time":
                    print(f"🕐 Getting current time for: {tool_input['city']}")
                    result = get_current_time(tool_input["city"])
                else:
                    result = {"error": f"Unknown tool: {tool_name}"}
                
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use_id,
                    "content": json.dumps(result)
                })
        
        # Send tool results back to Claude
        if tool_results:
            messages.append({"role": "user", "content": tool_results})
            
            final_response = client.messages.create(
                model="claude-opus-4-1-20250805",
                max_tokens=1024,
                tools=available_tools,
                messages=messages
            )
            
            print("\n📊 Response:")
            for content_block in final_response.content:
                if content_block.type == "text":
                    print(content_block.text)
    else:
        print("\n💬 Claude responded without using tools:")
        # Just print the regular response
        for content_block in response.content:
            if content_block.type == "text":
                print(content_block.text)

def main():
    """
    Main function that runs the interactive assistant loop
    """
    print("🤖 Welcome to the AI Assistant!")
    print("Ask for weather information (e.g., 'What's the weather in New York?')")
    print("Ask for weather forecasts (e.g., 'What's the 5-day forecast for Paris?' or 'Weather forecast for Tokyo')")
    print("Ask for stock prices (e.g., 'What's the price of AAPL stock?')")
    print("Ask for stock company info (e.g., 'Tell me about Apple stock' or 'What company is TSLA?')")
    print("Ask for currency exchange rates (e.g., 'What's the USD to EUR exchange rate?' or 'Convert GBP to JPY for today')")
    print("Ask for current time in any city (e.g., 'What time is it in Tokyo?' or 'Current time in London')")
    print("Type 'exit' to quit.\n")
    
    while True:
        try:
            # Get user input
            user_input = input("Enter your question (or 'exit' to quit): ").strip()
            
            # Check for exit condition
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("\n👋 Thanks for using the AI Assistant! Goodbye!")
                break
            
            # Skip empty inputs
            if not user_input:
                print("⚠️  Please enter a valid question.")
                continue
            
            # Process the user request
            process_user_request(user_input)
            print("\n" + "="*50)
            
        except KeyboardInterrupt:
            print("\n\n👋 Thanks for using the AI Assistant! Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ An error occurred: {e}")
            print("Please try again.")

if __name__ == "__main__":
    main()

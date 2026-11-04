import asyncio
import aioboto3
import json
import requests
import yfinance as yf
from geopy.geocoders import Nominatim
from typing import Dict, Any
from datetime import datetime
from timezonefinder import TimezoneFinder
import pytz

# Define sample tools
def calculate_sum(a, b):
    """Calculates the sum of two numbers."""
    return a + b

def get_weather(location: str) -> dict:
    """
    Calls an external weather API with location information and returns the current weather data.
    """
    try:
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
            f"&temperature_unit=fahrenheit"
        )

        response = requests.get(url)
        response.raise_for_status() # Raise an exception for bad status codes
        data = response.json()

        if "current" in data:
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
        else:
            return {"error": "Weather data unavailable"}


    except requests.exceptions.RequestException as e:
        return {"error": f"API request failed: {e}"}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {e}"}

def get_stock_info(ticker: str) -> dict:
    """
    Fetches basic company information for a given stock ticker, like 'AAPL' or 'GOOGL'.
    """
    try:
        stock = yf.Ticker(ticker)
        stock_info = stock.info

        company_name = stock_info.get("shortName")
        if company_name is None:
            company_name = "Name not available"
        
        sector = stock_info.get("sector")
        if sector is None:
            sector = "Sector not available"
        
        return {
            "ticker": ticker,
            "company_name": company_name,
            "sector": sector,
            "error": None
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
    """
    try:
        stock = yf.Ticker(ticker)
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

def get_exchange_rate(currency_from: str, currency_to: str, currency_date: str) -> Dict[str, Any]:
    """
    Get the exchange rate for currencies between countries. Give the latest or current value if not date is given
    """
    try:
        # Build the API URL
        if currency_date and currency_date.lower() != 'latest':
            url = f"https://api.frankfurter.app/{currency_date}"
        else:
            url = "https://api.frankfurter.app/latest"
            
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

def get_current_time(city: str) -> dict:
    """
    Returns the current date and time at the city
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

async def invoke_claude_with_tools(user_prompt):
    """
    Invokes the Claude model with a user prompt, handles tool use,
    and returns the final response.
    """
    # Define the tool specifications for Claude
    tools = [
        {
            "toolSpec": {
                "name": "calculate_sum",
                "description": "Calculates the sum of two numbers.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "a": {"type": "number", "description": "The first number."},
                            "b": {"type": "number", "description": "The second number."},
                        },
                        "required": ["a", "b"],
                    }
                },
            }
        },
        {
            "toolSpec": {
                "name": "get_weather",
                "description": "Retrieves the current weather for a given location. Use a city name like 'New York'.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "location": {"type": "string", "description": "The name of the city."},
                        },
                        "required": ["location"],
                    }
                },
            }
        },
        {
            "toolSpec": {
                "name": "get_stock_info",
                "description": "Fetches basic company information for a given stock ticker, like 'AAPL' or 'GOOGL'.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "ticker": {"type": "string", "description": "The stock ticker symbol."},
                        },
                        "required": ["ticker"],
                    }
                },
            }
        },
        {
            "toolSpec": {
                "name": "get_stock_price",
                "description": "Fetches the current price of a given stock ticker. Use a stock ticker symbol like 'AAPL' or 'GOOGL'.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "ticker": {"type": "string", "description": "The stock ticker symbol."},
                        },
                        "required": ["ticker"],
                    }
                },
            }
        },
        {
            "toolSpec": {
                "name": "get_exchange_rate",
                "description": "Gets the exchange rate between two currencies. Requires a 'currency_from' (e.g., 'EUR') and 'currency_to' (e.g., 'USD'). You can also specify an optional 'currency_date' in YYYY-MM-DD format, or 'latest' for the most recent rate.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "currency_from": {"type": "string", "description": "The base currency code."},
                            "currency_to": {"type": "string", "description": "The target currency code."},
                            "currency_date": {"type": "string", "description": "The date for the rate in YYYY-MM-DD format, or 'latest'."}
                        },
                        "required": ["currency_from", "currency_to", "currency_date"],
                    }
                },
            }
        },
        {
            "toolSpec": {
                "name": "get_current_time",
                "description": "Returns the current date and time for a given city.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "city": {"type": "string", "description": "The name of the city."},
                        },
                        "required": ["city"],
                    }
                },
            }
        }
    ]

    # Prepare the messages for Claude
    messages = [
        {
            "role": "user",
            "content": [{"text": user_prompt}],
        }
    ]

    model_id = "us.anthropic.claude-opus-4-20250514-v1:0"

    try:
        # Use an async session context manager to create the client
        async with aioboto3.Session().client("bedrock-runtime", region_name="us-west-2") as bedrock_runtime_client:
            response = await bedrock_runtime_client.converse(
                modelId=model_id,
                messages=messages,
                toolConfig={"tools": tools},
            )

            assistant_message = response["output"]["message"]
            messages.append(assistant_message)

            tool_uses = [
                content_block["toolUse"]
                for content_block in assistant_message["content"]
                if "toolUse" in content_block
            ]

            if tool_uses:
                tool_results = []
                for tool_use in tool_uses:
                    tool_name = tool_use["name"]
                    tool_input = tool_use["input"]
                    tool_use_id = tool_use["toolUseId"]

                    print(f"\nClaude wants to use tool: {tool_name} with input: {json.dumps(tool_input, indent=2)}")

                    # Execute the tool based on its name
                    if tool_name == "calculate_sum":
                        result_data = calculate_sum(**tool_input)
                        result_content = str(result_data)
                    elif tool_name == "get_weather":
                        result_data = get_weather(**tool_input)
                        result_content = json.dumps(result_data)
                    elif tool_name == "get_stock_info":
                        result_data = get_stock_info(**tool_input)
                        result_content = json.dumps(result_data)
                    elif tool_name == "get_stock_price":
                        result_data = get_stock_price(**tool_input)
                        result_content = json.dumps(result_data)
                    elif tool_name == "get_exchange_rate":
                        if "currency_date" not in tool_input or not tool_input["currency_date"]:
                             tool_input["currency_date"] = "latest"
                        result_data = get_exchange_rate(**tool_input)
                        result_content = json.dumps(result_data)
                    elif tool_name == "get_current_time":
                        result_data = get_current_time(**tool_input)
                        result_content = json.dumps(result_data)
                    else:
                        result_content = "Tool not found or not supported."
                    
                    print(f"Tool execution result: {result_content}")

                    tool_results.append({
                        "toolResult": {
                            "toolUseId": tool_use_id,
                            "content": [{"text": result_content}],
                        }
                    })

                if tool_results:
                    user_tool_message = {
                        "role": "user",
                        "content": tool_results,
                    }
                    messages.append(user_tool_message)

                    response_with_tool_result = await bedrock_runtime_client.converse(
                        modelId=model_id,
                        messages=messages,
                        toolConfig={"tools": tools},
                    )

                    final_message_content = response_with_tool_result["output"]["message"]["content"]
                    final_text = "".join(
                        content_block["text"]
                        for content_block in final_message_content
                        if "text" in content_block
                    )
                    return final_text
            else:
                direct_text = "".join(
                    content_block["text"]
                    for content_block in assistant_message["content"]
                    if "text" in content_block
                )
                return direct_text

    except Exception as e:
        return f"Error invoking Claude: {e}"

async def main():
    """Main function to run the tool use example in a loop."""
    print("Welcome to the Claude Tool Assistant. Type 'exit' or 'quit' to end the session.")
    
    while True:
        user_prompt = input("\nEnter your prompt: ")
        
        if user_prompt.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break
            
        final_response = await invoke_claude_with_tools(user_prompt)
        print("\n" + "="*50)
        print(f"Response: {final_response}")
        print("="*50 + "\n")

if __name__ == "__main__":
    asyncio.run(main())

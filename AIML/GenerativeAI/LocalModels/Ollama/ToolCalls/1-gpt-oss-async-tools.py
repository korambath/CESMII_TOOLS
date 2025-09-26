import asyncio
import ollama
from ollama import ChatResponse
import random
from typing import Iterator, Optional, Dict, Any
import httpx
import os
from datetime import datetime
from dotenv import load_dotenv

from rich import print
from ollama import Client, AsyncClient
from ollama._types import ChatResponse
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
from ollama import web_fetch

# 1. Load environment variables from the .env file
load_dotenv()

# 2. Get the API key from the environment variable
api_key = os.getenv("OLLAMA_API_KEY")

# Check if the API key was loaded successfully
if not api_key:
    raise ValueError("OLLAMA_API_KEY not found in .env file.")

OLLAMA_API_KEY=api_key

# Constants
NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "weather-app/1.0"

async def make_nws_request(url: str) -> dict[str, Any] | None:
    """Make a request to the NWS API with proper error handling."""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/geo+json"
    }
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None

def format_alert(feature: dict) -> str:
    """Format an alert feature into a readable string."""
    props = feature["properties"]
    return f"""
Event: {props.get('event', 'Unknown')}
Area: {props.get('areaDesc', 'Unknown')}
Severity: {props.get('severity', 'Unknown')}
Description: {props.get('description', 'No description available')}
Instructions: {props.get('instruction', 'No specific instructions provided')}
"""

async def get_alerts(state: str) -> str:
    """Get weather alerts for a US state.

    Args:
        state: Two-letter US state code (e.g. CA, NY)
    """
    url = f"{NWS_API_BASE}/alerts/active/area/{state}"
    data = await make_nws_request(url)

    if not data or "features" not in data:
        return "Unable to fetch alerts or no alerts found."

    if not data["features"]:
        return "No active alerts for this state."

    alerts = [format_alert(feature) for feature in data["features"]]
    return "\n---\n".join(alerts)

async def get_coordinates(location: str) -> tuple[float, float] | None:
    """Get coordinates for a location using geocoding."""
    try:
        geolocator = Nominatim(user_agent="weather-app")
        location_data = geolocator.geocode(location)
        if location_data:
            return (location_data.latitude, location_data.longitude)
        return None
    except Exception:
        return None

async def get_forecast(location: str) -> str:
    """Get weather forecast for a location.

    Args:
        location: Name of the location (e.g., "Los Angeles, CA")
    """
    # Get coordinates for the location
    coords = await get_coordinates(location)
    if not coords:
        return f"Unable to find coordinates for {location}."
    
    latitude, longitude = coords
    
    # First get the forecast grid endpoint
    points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
    points_data = await make_nws_request(points_url)

    if not points_data:
        return "Unable to fetch forecast data for this location."

    # Get the forecast URL from the points response
    forecast_url = points_data["properties"]["forecast"]
    forecast_data = await make_nws_request(forecast_url)

    if not forecast_data:
        return "Unable to fetch detailed forecast."

    # Format the periods into a readable forecast
    periods = forecast_data["properties"]["periods"]
    forecasts = []
    for period in periods[:5]:  # Only show next 5 periods
        forecast = f"""
{period['name']}:
Temperature: {period['temperature']}°{period['temperatureUnit']}
Wind: {period['windSpeed']} {period['windDirection']}
Forecast: {period['detailedForecast']}
"""
        forecasts.append(forecast)

    return "\n---\n".join(forecasts)




available_tools = {'get_forecast': get_forecast, 'get_alerts': get_alerts}

model_name='gpt-oss:20b'
async def process_user_query(client, user_input: str):
    """Process a single user query and return the response."""
    messages = [{'role': 'user', 'content': user_input}]
    
    response: ChatResponse = await client.chat(
        model_name,
        messages=messages,
        tools=[get_forecast, get_alerts],
    )

    if response.message.tool_calls:
        # There may be multiple tool calls in the response
        tool_outputs = []
        for tool in response.message.tool_calls:
            # Ensure the function is available, and then call it
            if function_to_call := available_tools.get(tool.function.name):
                print(f'\nCalling tool: {tool.function.name}')
                print(f'Arguments: {tool.function.arguments}')
                output = await function_to_call(**tool.function.arguments)
                print(f'Function output: {output}')
                tool_outputs.append(output)
                
                # Add the tool call and response to messages
                messages.append(response.message)
                messages.append({
                    'role': 'tool', 
                    'content': str(output), 
                    'tool_name': tool.function.name
                })
            else:
                print(f'Function {tool.function.name} not found')

        # Get final response from model with function outputs
        if tool_outputs:
            final_response = await client.chat(model_name, messages=messages)
            print(f'\nAssistant: {final_response.message.content}')
        else:
            print('No tool functions were successfully executed')
    else:
        print(f'\nAssistant: {response.message.content}')

async def main():
    client = ollama.AsyncClient(
       host="https://ollama.com", headers={'Authorization': OLLAMA_API_KEY}
    )
    
    print("Weather Assistant - Ask me about weather forecasts or alerts!")
    print("Type 'exit' to quit.\n")
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if user_input.lower() == 'exit':
                print("Goodbye!")
                break
                
            if not user_input:
                print("Please enter a question or type 'exit' to quit.")
                continue
                
            await process_user_query(client, user_input)
            print()  # Add blank line for readability
            
        except EOFError:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"An error occurred: {e}")
            print("Please try again or type 'exit' to quit.\n")


if __name__ == '__main__':
  try:
    asyncio.run(main())
  except KeyboardInterrupt:
    print('\nGoodbye!')

from openai import OpenAI
from geopy.geocoders import Nominatim
import json
import requests
 
client = OpenAI(
    base_url="http://localhost:11434/v1",  # Local Ollama API
    api_key="ollama"                       # Dummy key
)
 
def get_weather(location: str) -> dict:
    """
    Calls an extenal weather API with location information and returns the current weather data
    """
    try:
        # Step 1: Get coordinates from city name
        print(f"[debug] getting weather for {location}")
        geolocator = Nominatim(user_agent="weather_finder")
        geo_data = geolocator.geocode(location)

        if not geo_data:
            return {"error": "City or location not found"}

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



tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather in a given city or location",
            "parameters": {
                "type": "object",
                "properties": {"location": {"type": "string"}},
                "required": ["location"]
            },
        },
    }
]
 
input_messages = [{"role": "user", "content": "What's the weather like in Los Angeles, CA right now?"}]
model_name="gpt-oss:latest"

response = client.chat.completions.create(
    model=model_name,
    messages=input_messages,
    tools=tools
)
 
print(response.choices[0].message)

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
            if name == "get_weather":
                function_result = get_weather(**args)
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


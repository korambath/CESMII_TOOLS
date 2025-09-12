# https://strandsagents.com/latest/documentation/docs/examples/python/weather_forecaster/
import os
import boto3
from strands import Agent
from strands.models.litellm import LiteLLMModel
from strands.models import BedrockModel
from strands.models.ollama import OllamaModel
from strands_tools import http_request
from dotenv import load_dotenv
import json

load_dotenv()

# Create an Ollama model instance
ollama_model = OllamaModel(
    host="http://localhost:11434",  # Ollama server address
    model_id="llama3.2"               # Specify which model to use
)

# Create an agent using the Ollama model
ollam_agent = Agent(model=ollama_model)

# Check if OpenAI API Key is set
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
print(f"OpenAI API Key set: {'Yes' if OPENAI_API_KEY else 'No (Please set your OPENAI_API_KEY in a .env file)'}")

openai_model = LiteLLMModel(
    client_args={
        "api_key": OPENAI_API_KEY,
    },
    # **model_config
    model_id="openai/gpt-4o-mini",
    params={
        "max_tokens": 1000,
        "temperature": 0.7,
    }
)



# Define a weather-focused system prompt
WEATHER_SYSTEM_PROMPT = """You are a weather assistant with HTTP capabilities. You can:

1. Make HTTP requests to the National Weather Service API
2. Process and display weather forecast data
3. Provide weather information for locations in the United States

When retrieving weather information:
1. First get the coordinates or grid information using https://api.weather.gov/points/{latitude},{longitude} or https://api.weather.gov/points/{zipcode}
2. Then use the returned forecast URL to get the actual forecast

When displaying responses:
- Format weather data in a human-readable way
- Highlight important information like temperature, precipitation, and alerts
- Handle errors appropriately
- Convert technical terms to user-friendly language

Always explain the weather conditions clearly and provide context for the forecast.
"""


bedrock_model = BedrockModel(
    model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",
    region_name="us-west-2",
    temperature=0.3,
)

weather_agent = Agent(
    system_prompt=WEATHER_SYSTEM_PROMPT,
    tools=[http_request],  # Explicitly enable http_request tool
    #model=bedrock_model,  
    model=ollama_model,  
    #model=openai_model,  # Use the LiteLLMModel instance
)
print(f"\nAgent Model Configuration: {weather_agent.model.config}\n")

# Let the agent handle the API details
#response = weather_agent("What's the weather like in Seattle?")
#response = weather_agent("Will it rain tomorrow in Miami?")
#response = weather_agent("Compare the temperature in New York and Chicago this weekend")

#response = weather_agent("Compare the temperature in New York and Chicago this weekend")
response = weather_agent("Will it rain tomorrow in Los Angeles, CA?")


print(f"\n\n\nModel Response: {response.message}\n\n")
print(json.dumps(response.message, indent = 4))


print("\nEND")
#print(json.dumps(response.metrics.get_summary(), indent=4))

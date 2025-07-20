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

from google import genai
from google.genai import types

from google import genai
from google.genai import types
import datetime # Import datetime for potential date/time validation (though not strictly required for this simple mock)

# Define the function declaration for the model
schedule_meeting_function = {
    "name": "schedule_meeting",
    "description": "Schedules a meeting with specified attendees at a given time and date.",
    "parameters": {
        "type": "object",
        "properties": {
            "attendees": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of people attending the meeting.",
            },
            "date": {
                "type": "string",
                "description": "Date of the meeting (e.g., '2024-07-29')",
            },
            "time": {
                "type": "string",
                "description": "Time of the meeting (e.g., '15:00')",
            },
            "topic": {
                "type": "string",
                "description": "The subject or topic of the meeting.",
            },
        },
        "required": ["attendees", "date", "time", "topic"],
    },
}

# --- Implement the schedule_meeting function ---
def schedule_meeting(attendees: list[str], date: str, time: str, topic: str) -> dict:
    """
    Simulates scheduling a meeting with the given details.
    In a real application, this would interact with a calendar API (e.g., Google Calendar, Outlook).
    """
    try:
        # Basic validation (optional, but good practice)
        if not attendees:
            return {"status": "error", "message": "Attendees list cannot be empty."}
        if not date or not time or not topic:
            return {"status": "error", "message": "Date, time, and topic are required."}

        # Simulate a date/time parse to ensure format (optional)
        try:
            # This is a very basic parse, real apps need robust date/time handling
            meeting_datetime_str = f"{date} {time}"
            meeting_datetime = datetime.datetime.strptime(meeting_datetime_str, "%Y-%m-%d %H:%M")
        except ValueError:
            return {"status": "error", "message": "Invalid date or time format. Expected YYYY-MM-DD HH:MM."}

        # Simulate scheduling action
        attendee_list = ", ".join(attendees)
        print(f"\n--- Scheduling Meeting ---")
        print(f"Topic: {topic}")
        print(f"Date: {date}")
        print(f"Time: {time}")
        print(f"Attendees: {attendee_list}")
        print(f"--------------------------\n")

        # In a real scenario, this would return confirmation from the calendar API
        return {
            "status": "success",
            "message": f"Meeting '{topic}' scheduled for {date} at {time} with {attendee_list}.",
            "meeting_details": {
                "topic": topic,
                "date": date,
                "time": time,
                "attendees": attendees
            }
        }
    except Exception as e:
        return {"status": "error", "message": f"An unexpected error occurred: {str(e)}"}

# --- Define a mapping of available functions ---
# This is your whitelist for functions the AI can call.
AVAILABLE_FUNCTIONS = {
    "schedule_meeting": schedule_meeting,
    # Add other functions here if you have them, e.g., "get_weather": get_weather
}

# Configure the client and tools
client = genai.Client()
tools = types.Tool(function_declarations=[schedule_meeting_function])
config = types.GenerateContentConfig(tools=[tools])

# Assuming 'client', 'config', and 'AVAILABLE_FUNCTIONS' are already defined
# (e.g., from your previous setup)

while True:
    print("\n--- Schedule a New Meeting ---")
    topic = input("Enter the meeting topic (or 'quit' to exit): ")
    if topic.lower() == 'quit' or topic.lower() == 'exit':
        break

    attendees = input("Enter attendees (comma-separated, e.g., Bob, Alice): ")
    date = input("Enter the date (YYYY-MM-DD, e.g., 2025-03-14): ")
    time = input("Enter the time (HH:MM AM/PM, e.g., 10:00 AM): ")

    # Construct the content string using f-strings for easy variable insertion
    content_string = f"Schedule a meeting with {attendees} for {date} at {time} about the {topic}."

    # Send request with function declarations
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=content_string,
        config=config,
    )

    # Check for a function call
    if response.candidates and response.candidates[0].content.parts[0].function_call:
        function_call = response.candidates[0].content.parts[0].function_call
        print(f"Function to call: {function_call.name}")
        print(f"Arguments: {function_call.args}")

        # --- Call your function here ---
        function_name = function_call.name
        function_args = function_call.args

        if function_name in AVAILABLE_FUNCTIONS:
            target_function = AVAILABLE_FUNCTIONS[function_name]
            try:
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

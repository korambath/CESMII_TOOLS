import os
from google import genai
from google.genai import types
import matplotlib.pyplot as plt
import json
from dotenv import load_dotenv

load_dotenv()

# The client gets the API key from the environment variable `GEMINI_API_KEY`.
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY environment variable not set.")
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
model_name = "gemini-2.5-flash" # Renamed to avoid conflict with `model` variable later

# --- Charting Function Definition ---
def create_chart(title: str, labels: list, values: list, chart_type: str = "bar"):
    """
    Creates various types of charts (bar, line, pie) given a title, labels, and corresponding values.

    Args:
        title (str): The title for the chart.
        labels (list): List of labels for the data points.
        values (list): List of numerical values corresponding to the labels.
        chart_type (str): The type of chart to create ('bar', 'line', 'pie'). Defaults to 'bar'.
    """
    plt.figure(figsize=(10, 6))

    if chart_type == "bar":
        plt.bar(labels, values, color='skyblue')
        plt.ylabel("Values")
    elif chart_type == "line":
        plt.plot(labels, values, marker='o', linestyle='-', color='green')
        plt.ylabel("Values")
    elif chart_type == "pie":
        plt.pie(values, labels=labels, autopct='%1.1f%%', startangle=90, colors=plt.cm.Paired.colors)
        plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    else:
        print(f"Unsupported chart type: {chart_type}. Please choose 'bar', 'line', or 'pie'.")
        return

    plt.title(title)
    plt.xlabel("Categories") # This might not always be applicable for pie charts, but generally good for bar/line.
    plt.grid(axis='y', linestyle='--', alpha=0.7) # Grid for bar/line charts
    plt.tight_layout()
    plt.show() # Display the chart
    print(f"Chart '{title}' of type '{chart_type}' displayed successfully.")
    return f"Chart '{title}' of type '{chart_type}' created."

# --- Function Declaration for the Gemini Model ---
create_chart_function = {
    "name": "create_chart",
    "description": "Creates various types of charts (bar, line, pie) given a title, labels, values, and chart type.",
    "parameters": {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "The title for the chart.",
            },
            "labels": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of labels for the data points (e.g., ['Q1', 'Q2', 'Q3']).",
            },
            "values": {
                "type": "array",
                "items": {"type": "number"},
                "description": "List of numerical values corresponding to the labels (e.g., [50000, 75000, 60000]).",
            },
            "chart_type": {
                "type": "string",
                "description": "The type of chart to create. Can be 'bar', 'line', or 'pie'. Defaults to 'bar'.",
                "enum": ["bar", "line", "pie"],
                "default": "bar",
            },
        },
        "required": ["title", "labels", "values"],
    },
}

# Configure the client and tools
client = genai.Client()
tools = types.Tool(function_declarations=[create_chart_function])
config = types.GenerateContentConfig(tools=[tools])

# Register the function that the model can call
AVAILABLE_FUNCTIONS = {
    "create_chart": create_chart,
}

# --- Example Usage with Gemini Model Call ---
print("--- Requesting Bar Chart ---")
response = client.models.generate_content(
    model=model_name,
    contents="Create a bar chart titled 'Quarterly Sales' with data: Q1: 50000, Q2: 75000, Q3: 60000.",
    config=config,
)

if response.candidates and response.candidates[0].content.parts[0].function_call:
    function_call = response.candidates[0].content.parts[0].function_call
    print(f"Function to call: {function_call.name}")
    print(f"Arguments: {function_call.args}")

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
else:
    print("No function call found in the response.")
    print(f"Model's text response: {response.text}")

print("\n--- Requesting Line Chart ---")
response = client.models.generate_content(
    model=model_name,
    contents="Show me a line graph of monthly website visits: Jan: 1000, Feb: 1200, Mar: 950, Apr: 1500. Title it 'Website Visits'.",
    config=config,
)

if response.candidates and response.candidates[0].content.parts[0].function_call:
    function_call = response.candidates[0].content.parts[0].function_call
    print(f"Function to call: {function_call.name}")
    print(f"Arguments: {function_call.args}")

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
else:
    print("No function call found in the response.")
    print(f"Model's text response: {response.text}")

print("\n--- Requesting Pie Chart ---")
response = client.models.generate_content(
    model=model_name,
    contents="Make a pie chart showing department headcounts: Sales: 40, Marketing: 25, Engineering: 35. Call it 'Department Headcount'.",
    config=config,
)

if response.candidates and response.candidates[0].content.parts[0].function_call:
    function_call = response.candidates[0].content.parts[0].function_call
    print(f"Function to call: {function_call.name}")
    print(f"Arguments: {function_call.args}")

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
else:
    print("No function call found in the response.")
    print(f"Model's text response: {response.text}")

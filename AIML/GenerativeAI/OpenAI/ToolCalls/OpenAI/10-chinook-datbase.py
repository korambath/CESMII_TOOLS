import sqlite3
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

client = OpenAI()

conn = sqlite3.connect("data/Chinook.db")
print("Opened database successfully")

def get_table_names(conn):
    """Return a list of table names."""
    #print(f"[Debug] get_table_names called")
    table_names = []
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
    for table in tables.fetchall():
        table_names.append(table[0])
    return table_names


def get_column_names(conn, table_name):
    """Return a list of column names."""
    #print(f"[Debug] get_column_names called")
    column_names = []
    columns = conn.execute(f"PRAGMA table_info('{table_name}');").fetchall()
    for col in columns:
        column_names.append(col[1])
    return column_names


def get_database_info(conn):
    """Return a list of dicts containing the table name and columns for each table in the database."""
    #print(f"[Debug] get_database_info called")
    table_dicts = []
    for table_name in get_table_names(conn):
        columns_names = get_column_names(conn, table_name)
        table_dicts.append({"table_name": table_name, "column_names": columns_names})
    return table_dicts


database_schema_dict = get_database_info(conn)
database_schema_string = "\n".join(
    [
        f"Table: {table['table_name']}\nColumns: {', '.join(table['column_names'])}"
        for table in database_schema_dict
    ]
)

tools = [
    {
        "type": "function",
        "function": {
            "name": "ask_database",
            "description": "Use this function to answer user questions about music. Input should be a fully formed SQL query.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": f"""
                                SQL query extracting info to answer the user's question.
                                SQL should be written using this database schema:
                                {database_schema_string}
                                The query should be returned in plain text, not in JSON.
                                """,
                    }
                },
                "required": ["query"],
            },
        }
    }
]

def ask_database(conn, query):
    """Function to query SQLite database with a provided SQL query."""
    try:
        results = str(conn.execute(query).fetchall())
    except Exception as e:
        results = f"query failed with error: {e}"
    return results


# Step #1: Prompt with content that may result in function call. In this case the model can identify the information requested by the user is potentially available in the database schema passed to the model in Tools description. 
messages = [{
    "role":"user", 
    "content": "What is the name of the album with the most tracks?"
}]

response = client.chat.completions.create(
    model='gpt-4o', 
    messages=messages, 
    tools= tools, 
    tool_choice="auto"
)

# Append the message to messages list
response_message = response.choices[0].message 
messages.append(response_message)

print(f"Initial Response: {response_message}")


# Step 2: determine if the response from the model includes a tool call.   
tool_calls = response_message.tool_calls
if tool_calls:
    # If true the model will return the name of the tool / function to call and the argument(s)  
    tool_call_id = tool_calls[0].id
    tool_function_name = tool_calls[0].function.name
    tool_query_string = json.loads(tool_calls[0].function.arguments)['query']

    # Step 3: Call the function and retrieve results. Append the results to the messages list.      
    if tool_function_name == 'ask_database':
        results = ask_database(conn, tool_query_string)
        
        messages.append({
            "role":"tool", 
            "tool_call_id":tool_call_id, 
            "name": tool_function_name, 
            "content":results
        })
        
        # Step 4: Invoke the chat completions API with the function response appended to the messages list
        # Note that messages with role 'tool' must be a response to a preceding message with 'tool_calls'
        model_response_with_function_call = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
        )  # get a new response from the model where it can see the function response
        print(f"Final Response: {model_response_with_function_call.choices[0].message.content}")
    else: 
        print(f"Error: function {tool_function_name} does not exist")
else: 
    # Model did not identify a function to call, result can be returned to the user 
    print(response_message.content) 




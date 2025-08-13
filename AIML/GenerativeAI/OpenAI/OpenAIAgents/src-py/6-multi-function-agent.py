import asyncio
from agents import Agent, Runner, function_tool
import wikipedia
from agents import Agent, ImageGenerationTool, Runner, trace
from agents import Agent, Runner, WebSearchTool, trace
from openai.types.responses import ResponseTextDeltaEvent
from agents import Agent, Runner, set_tracing_disabled
from dotenv import load_dotenv
from typing import Optional, Dict, Any
import os
import random
load_dotenv()

OPENAI_API_KEY=os.getenv("OPENAI_API_KEY")

print(f"OpenAI API Key set: {'Yes' if os.environ.get('OPENAI_API_KEY') and os.environ['OPENAI_API_KEY'] != 'YOUR_OPENAI_API_KEY' else 'No (REPLACE PLACEHOLDER!)'}")

@function_tool
async def calculate_total_with_tax(order_total: float, tax_rate : float = 0.0725) -> str:
    print(f"DEBUG: calculate_total_with_tax function called order:{order_total} tax:{tax_rate}")
    """Calculates the total due with tax for a given order total based on the input amount (float) and tax rate (float).
    Args:
        order_total: The total amount of the order before tax.
        tax_rate: defautl to 0.0725 if no data given.
    """
    tax_amount = order_total * tax_rate
    total_with_tax = order_total + tax_amount
    return f"The tax rate on your order is ${tax_amount:.2f}. Your total amount due with tax is ${total_with_tax:.2f}."


@function_tool
def random_number_tool(max: int) -> int:
    print(f"DEBUG:  random_number function called for max int :{max}")
    """Return a random integer between 0 and the given maximum."""
    return random.randint(0, max)



@function_tool
def temperature_converter(temperature: float, original_unit: str, target_unit: str) -> Dict[str, Any]:
    print(f"DEBUG: temperature_converter function called with temperature:{temperature} original unit :{original_unit} and target unit {target_unit}")
    """
    Converts a temperature from one unit to another.

    Args:
        temperature (float): The temperature value to convert.
        original_unit (str): The current unit of the temperature ('celsius' or 'fahrenheit').
        target_unit (str): The desired unit for conversion ('celsius' or 'fahrenheit').

    Returns:
        A dictionary containing:
            - celsius or fahrenheit : The converted temperature in Celsius or Fahrenheit
            - original_fahrenheit or original_celsius : The original Fahrenheit value or Celsius Value
            - str: An error message if the units are invalid.
    """
    #print("Agent called \n")
    original_unit = original_unit.lower()
    target_unit = target_unit.lower()

    if original_unit == target_unit:
        return {
           "temperature": temperature ,
           "original_temperature": temperature
        }

    if original_unit == 'celsius' and target_unit == 'fahrenheit':
        celsius_t =  (temperature * 9/5) + 32
        return {
            "celsius": round(celsius_t, 2),
            "original_fahrenheit": temperature
        }
    elif original_unit == 'fahrenheit' and target_unit == 'celsius':
        fahrenheit_t =  (temperature - 32) * 5/9
        return {
            "fahrenheit": round(fahrenheit_t, 2),
            "original_celsius": temperature
        }
    else:
        return {
             "Error" : "Invalid units specified. Please use 'celsius' or 'fahrenheit'."
        }

@function_tool
def word_count(text: str) -> int:
    print(f"DEBUG: word_count function called for for text :{text}")
    """Count words in text.

    This docstring is used by the LLM to understand the tool's purpose.
    """
    return len(text.split())

@function_tool
def wikipedia_lookup(q: str) -> str:
    print(f"DEBUG: wikepedia_lookup function called for for query :{q}")
    """Look up a query in Wikipedia and return the result"""
    return wikipedia.page(q).summary

research_agent = Agent(
    name="Research agent",
    instructions="""You research topics using Wikipedia and report on 
                    the results or return number of words in a sentence or return a random number using random_number_tool. 
                    If the user needs help in converting temperature from fahrenheit to celsius or vice versa
                    Use temperature_converter to convert temperatures between Fahrenheit and Celsius or vice versa """,
    model="o4-mini",
    tools=[wikipedia_lookup, word_count, temperature_converter, random_number_tool, calculate_total_with_tax],
)

async def run_agent(input_string):
    result = await Runner.run(research_agent, input_string)
    #return result.final_output
    return result

if __name__ == "__main__":
    print("\n Example query for  wikipedia search, word_count, temperature_converter, random_number, calculate total with tax")
    input_string = input("\nEnter your question: ").strip()
    try:
        result = asyncio.run(run_agent(input_string))
        print(f"\nEntire list of messages : {result.to_input_list()}\n")
        print(result.final_output)
    except Exception as e: 
        print(f"An error occurred during execution: {e}")

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
from pydantic import BaseModel

class Recipe(BaseModel):
    recipe_name: str
    ingredients: list[str]

client = genai.Client()
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="List a few popular cookie recipes, and include the amounts of ingredients.",
    config={
        "response_mime_type": "application/json",
        "response_schema": list[Recipe],
    },
)
# Use the response as a JSON string.
print(response.text)


# Use instantiated objects.
my_recipes: list[Recipe] = response.parsed

for index, recipe in enumerate(my_recipes):
    print(f"Recipe {index + 1}: {recipe.recipe_name}")
    print("Ingredients:")
    for ingredient in recipe.ingredients:
        print(f"- {ingredient}")
    print()  # Print a newline for better readability
# Example of accessing a specific recipe



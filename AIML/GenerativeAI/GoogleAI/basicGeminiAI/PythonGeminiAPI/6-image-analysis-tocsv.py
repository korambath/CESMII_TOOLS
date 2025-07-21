from google import genai
import os
import requests
import json
from dotenv import load_dotenv
import csv # Import the csv module
from PIL import Image

load_dotenv()

# The client gets the API key from the environment variable `GEMINI_API_KEY`.
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY environment variable not set.")

client = genai.Client(api_key=api_key) # Use the retrieved api_key here
model_name = "gemini-2.5-flash" # Renamed 'model' to 'model_name' to avoid conflict with client.models

# Open the image file
try:
    image = Image.open("proteindata.png")
    # image.show() # You might not want to show the image every time in an automated script
except FileNotFoundError:
    print("Error: proteindata.png not found. Please ensure the image file is in the correct directory.")
    exit()

prompt = '''
Look at the image shot which is a CSV file and has many rows and columns:
List all the rows and columns and data as if I am looking at the CSV file.
Ensure the output is directly parsable as a CSV, with each row on a new line and values separated by commas.
'''

print("Sending request to Gemini API...")
response = client.models.generate_content(
    model=model_name, # Use the renamed variable here
    contents=[image, prompt]
)

# Print the raw response text for debugging/verification
print("\n--- Raw Gemini Response ---")
print(response.text)
print("---------------------------\n")

# Define the output CSV file name
output_csv_file = "output_proteindata.csv"

try:
    # Open the CSV file in write mode
    with open(output_csv_file, 'w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile)

        # Split the response text into lines
        lines = response.text.strip().split('\n')

        for line in lines:
            # Attempt to parse each line as CSV.
            # This is a basic split; for more complex CSV structures (e.g., commas within fields, quoted fields),
            # you might need more sophisticated parsing or rely on Gemini to provide perfectly formed CSV.
            row_data = line.split(',')
            csv_writer.writerow(row_data)

    print(f"Successfully wrote data to {output_csv_file}")

except Exception as e:
    print(f"An error occurred while writing to the CSV file: {e}")

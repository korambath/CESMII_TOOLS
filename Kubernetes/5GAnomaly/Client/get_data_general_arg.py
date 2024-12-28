import argparse
import requests
import time

def print_data(data, indent=0):
    """ Recursively prints data (handles nested lists and dictionaries) """
    if isinstance(data, dict):
        for key, value in data.items():
            # Print the key-value pair with proper indentation
            print(' ' * indent + f"{key}:")
            print_data(value, indent + 2)  # Recurse into the value
    elif isinstance(data, list):
        for i, item in enumerate(data):
            print(' ' * indent + f"Item {i + 1}:")
            print_data(item, indent + 2)  # Recurse into the list item
    else:
        # Print the value if it's not a dictionary or list
        print(' ' * indent + f"{data}")

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Poll the server for data and print the received data.")
    
    # Add arguments for URL and port
    parser.add_argument('url', type=str, help="The base URL of the HTTP server (e.g., 'localhost').")
    parser.add_argument('port', type=int, help="The port number of the HTTP server (e.g., '8000').")
    
    # Parse arguments
    args = parser.parse_args()

    # Construct the full URL by combining the base URL and port
    full_url = f"http://{args.url}:{args.port}"

    # Infinite loop to continuously poll the server for new data
    while True:
        try:
            # Send GET request to retrieve the data that has been sent to the server
            response = requests.get(full_url)

            if response.status_code == 200:
                data = response.json()  # Get the response data (JSON)

                if data:
                    print("New data received from the server:")
                    print_data(data)  # Print the received data recursively
                else:
                    print("No new data received yet.")

            else:
                print(f"Error: {response.status_code}")
                print(response.text)

        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")

        # Sleep for a few seconds before checking again (adjust as needed)
        time.sleep(5)

if __name__ == "__main__":
    main()


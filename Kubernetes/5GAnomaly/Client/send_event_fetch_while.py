import argparse
import requests
import json
from datetime import datetime
from datetime import datetime, timedelta
import time

# Function to generate a formatted timestamp
def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Function to send the POST request
def send_post_request(url, payload):
    headers = {'Content-Type': 'application/json'}
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            print("POST request was successful")
            print(f"Response: {response.json()}")
        else:
            print(f"Failed POST request. Status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

# Function to fetch the event data from the provided URL
def fetch_event_data(event_url):
    try:
        response = requests.get(event_url)
        if response.status_code == 200:
            return response.json()  # Assuming the response is in JSON format
        else:
            print(f"Failed to fetch event data. Status code: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while fetching event data: {e}")
        return None

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Send security events as a POST request to a given URL and port.")
    
    # Add arguments for URL and port
    parser.add_argument('url', type=str, help="The base URL to connect to (e.g., 'localhost').")
    parser.add_argument('port', type=int, help="The port number to connect to.")
    parser.add_argument('event_url', type=str, help="The base URL to connect to (e.g., 'https://hostname').")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Create the full URL for the POST request
    full_url = f"http://{args.url}:{args.port}/security/event"


    # Initial start and end times
    start_time_str = "2025-03-21T16:14:00"
    end_time_str = "2025-03-21T16:15:00"

    # Convert to datetime objects
    start_time = datetime.strptime(start_time_str, "%Y-%m-%dT%H:%M:%S")
    end_time = datetime.strptime(end_time_str, "%Y-%m-%dT%H:%M:%S")

    # URL template
    url_template = "{}/security/event/{}/{}/"
    
    # URL from which to fetch the event data
    #print(event_url)

    # While loop to create URLs with updated start_time and end_time
    begin_time=start_time
    while end_time <= begin_time + timedelta(minutes=500):  # Loop for 5 minutes as an example
        print(f"Start Time: {start_time}, End Time: {end_time}")
        event_url = url_template.format(args.event_url,start_time.strftime("%Y-%m-%dT%H:%M:%S"), end_time.strftime("%Y-%m-%dT%H:%M:%S"))
        print(f"Generated URL: {event_url}")
    
        # Update start_time and end_time
        start_time = end_time + timedelta(minutes=1)
        end_time = start_time + timedelta(minutes=1)

    
        # Fetch the event data
        payload = fetch_event_data(event_url)

        print(payload)

        #if payload is not None:
        if payload:
            # Send the POST request with the fetched data
            send_post_request(full_url, payload)
            #print("Payload is empty.")
        else:
            print("No event data fetched. POST request not sent.")
        time.sleep (1)

if __name__ == "__main__":
    main()


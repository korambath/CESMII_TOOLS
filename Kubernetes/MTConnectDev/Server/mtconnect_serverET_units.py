import argparse
import http.server
import socketserver
import random
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from zoneinfo import ZoneInfo


# Port to run the server on
DEFAULT_PORT = 5000


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="CESMII Smart Manufacturing Platform Data Sender")
    parser.add_argument("-u", "--mt_url", type=str, default="localhost", help="MT Connect Server URL (default: localhost)")
    parser.add_argument("-p", "--mt_port", type=int, default=DEFAULT_PORT, help="MT Connect Port (default: 5000)")
    return parser.parse_args()


def generate_sensor_data():
    """Simulate sensor data."""
    temperature = round(random.uniform(20.0, 30.0), 2)  # Temperature in Celsius
    pressure = round(random.uniform(980, 1020), 2)      # Pressure in hPa
    humidity = round(random.uniform(40, 60), 2)         # Humidity in percentage
    return temperature, pressure, humidity


def create_mtconnect_xml():
    """Create MTConnect XML response with simulated sensor data."""
    temperature, pressure, humidity = generate_sensor_data()
    
    # Build the XML structure
    root = ET.Element("MTConnectDevices", version="1.7.1")
    device = ET.SubElement(root, "Device", name="SimulatedDevice", id="1")
    
    # Adding Temperature, Pressure, and Humidity data as "DataItems"
    data_items = ET.SubElement(device, "DataItems")
    
    # Add Temperature DataItem with units
    temperature_data_item = ET.SubElement(data_items, "DataItem", name="Temperature", type="TEMPERATURE", id="1", unit="Celsius")
    temperature_data_item.text = str(temperature)

    # Add Pressure DataItem with units
    pressure_data_item = ET.SubElement(data_items, "DataItem", name="Pressure", type="PRESSURE", id="2", unit="hPa")
    pressure_data_item.text = str(pressure)

    # Add Humidity DataItem with units
    humidity_data_item = ET.SubElement(data_items, "DataItem", name="Humidity", type="HUMIDITY", id="3", unit="Percent")
    humidity_data_item.text = str(humidity)

    # Get current time in UTC
    now_utc = datetime.now(timezone.utc)

    # Convert to Pacific Time
    pacific_timezone = ZoneInfo("America/Los_Angeles")
    now_pacific = now_utc.astimezone(pacific_timezone)
    timestamp = now_pacific.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    root.set("timestamp", timestamp)

    # Convert XML to string and return
    return ET.tostring(root, encoding='utf-8', method='xml').decode()


class MTConnectHandler(http.server.BaseHTTPRequestHandler):
    """Custom handler for responding with MTConnect data."""
    
    def do_GET(self):
        """Handle GET requests."""
        if self.path == '/current_data':
            # Serve the MTConnect XML response with simulated data
            self.send_response(200)
            self.send_header("Content-Type", "application/xml")
            self.end_headers()
            response_xml = create_mtconnect_xml()
            self.wfile.write(response_xml.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()


def run_server(url, port):
    """Run the HTTP server."""
    with socketserver.TCPServer((url, port), MTConnectHandler) as httpd:
        print(f"Server running at http://{url}:{port}")
        httpd.serve_forever()


if __name__ == "__main__":
    # Parse command-line arguments
    args = parse_arguments()

    # Display configured server information
    print(f"Starting server at {args.mt_url}:{args.mt_port}")
    
    # Start the server
    run_server(args.mt_url, args.mt_port)


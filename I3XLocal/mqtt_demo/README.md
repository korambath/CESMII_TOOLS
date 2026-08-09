# MQTT to i3X Demo

This repository demonstrates how to publish MQTT sensor data and make it visible through an i3X server and i3X Explorer.

It combines:
- the i3X quickstart flow for installing and running an i3X server,
- a local MQTT publisher that sends random values,
- an Arduino-based publisher that reads a BME280 sensor,
- a local MQTT subscriber for simple terminal-based monitoring,
- and CLI-based subscription examples for interacting with the i3X server.

## What this demo does

1. An MQTT publisher sends sensor data to the topic:
   - `cesmii/labLA/bme280sensor`
2. An i3X server subscribes to that MQTT stream and exposes the data through the i3X API.
3. You can visualize the data with:
   - i3X Explorer,
   - the local Python subscriber,
   - or the curl-based subscription commands in the runtime folder.

---

## Prerequisites

Make sure you have:
- Python 3
- pip
- Git
- A local MQTT broker (for example, Mosquitto)
- Optional but recommended: `jq` for formatted JSON output
- Optional: an Arduino board with a BME280 sensor if you want to use the hardware publisher

### Install Python dependencies

```bash
python3 -m pip install --user paho-mqtt pyserial
```

### Install jq (optional, recommended)

On macOS:

```bash
brew install jq
```

On Ubuntu/Debian:

```bash
sudo apt update && sudo apt install jq
```

---

## 1. Install and run the i3X server

The following steps follow the i3X quickstart flow.

### Step 1: Clone the i3X repository

```bash
git clone https://github.com/cesmii/i3X.git
cd i3X/demo/server
```

### Step 2: Configure the server for MQTT

```bash
cp config-mqtt.json config.json
```

If needed, edit `config.json` to point to your MQTT broker.

### Step 3: Start the server

On macOS/Linux/WSL:

```bash
./setup.sh
```

On Windows PowerShell:

```powershell
./setup.ps1
```

This creates a Python virtual environment and installs dependencies.

### Step 4: Start the server runtime

After setup, start the local i3X server service. The exact startup command may depend on the server package, but the default local endpoint is typically:

```bash
http://localhost:8080
```

---

## 2. Download and run i3X Explorer

The quickstart recommends downloading the i3X Explorer client to visualize the address space and data.

### Download Explorer

Visit:

- https://acetechnologies.net/i3X/

Choose the package for your platform (macOS, Windows, or Linux) and install it.

### Connect Explorer

1. Open i3X Explorer.
2. Disconnect from the public demo endpoint if it is connected.
3. Connect to your local server:
   - `http://localhost:8080`
4. Explore the namespaces and objects to see the MQTT-backed data.

---

## 3. Start an MQTT broker

This demo expects an MQTT broker running locally on port `1883`.

If you do not already have one, install and run Mosquitto.

On macOS:

```bash
brew install mosquitto
brew services start mosquitto
```

On Ubuntu:

```bash
sudo apt install mosquitto mosquitto-clients
sudo systemctl start mosquitto
```

The publisher scripts in this repo connect to:
- broker: `127.0.0.1`
- port: `1883`

---

## 4. Run the local MQTT publishers

### Option A: Publish random sensor values

Use the Python publisher that generates synthetic data:

```bash
python3 publisher.py
```

This script publishes random values for:
- temperature,
- humidity,
- pressure.

### Option B: Publish real data from an Arduino BME280 sensor

The Arduino sketch is located at Arudino folder inside publish folder:

#### Upload the Arduino sketch

1. Open the sketch in the Arduino IDE.
2. Install the required libraries if needed:
   - Adafruit BME280 library
   - Adafruit Sensor library
3. Upload the sketch to your board.

#### Update the serial port

The Python publisher expects the Arduino to appear on a serial device such as:

```python
SERIAL_PORT = "/dev/cu.usbmodem2101"
```

If your port is different, update it in publisher_arduino.py file.

#### Run the Arduino-based publisher

```bash
python3 publisher_arduino.py
```

This script reads live values from the BME280 sensor and publishes them to the same MQTT topic.

---

## 5. View data locally with the MQTT subscriber

To watch the MQTT messages directly in the terminal, run:

```bash
python3 subscriber.py
```

This subscribes to the same topic and prints the incoming payloads as JSON.

---

## 6. Use the i3X server to subscribe to the MQTT data

Once the i3X server is running, you can create and manage subscriptions using the provided curl examples.


### Example flow

1. Create a subscription:

```bash
curl -s -X POST http://localhost:8080/subscriptions \
  -H "Content-Type: application/json" \
  -d '{
    "clientId": "mqtt_test_client",
    "displayName": "BME280 MQTT Subscription"
  }' | jq
```

2. Register the object to monitor:

```bash
curl -s -X POST http://localhost:8080/subscriptions/register \
  -H "Content-Type: application/json" \
  -d '{
    "clientId": "mqtt_test_client",
    "subscriptionId": "PASTE_THE_GENERATED_ID_HERE",
    "elementIds": [
      "cesmii_labLA_bme280sensor"
    ]
  }' | jq
```

3. Start streaming updates:

```bash
curl -N -X POST http://localhost:8080/subscriptions/stream \
  -H "Content-Type: application/json" \
  -d '{
    "clientId": "mqtt_test_client",
    "subscriptionId": "PASTE_THE_GENERATED_ID_HERE"
  }'
```

### Helper script

You can also run the provided shell helper:

```bash
cd i3x-mqtt-runtime
chmod +x subscribe_bme280.sh
./subscribe_bme280.sh
```

---

## 7. Suggested run order

For a complete demo, use this order:

1. Start the MQTT broker.
2. Start the i3X server.
3. Open i3X Explorer and connect to `http://localhost:8080`.
4. Start one of the publishers:
   - `python3 publisher.py`, or
   - `python3 publisher_arduino.py`
5. Run `python3 subscriber.py` to see the MQTT stream locally.
6. Create and stream the i3X subscription using the commands in subscribe_bme280.sh file

---

## Notes

- The MQTT topic used by the demo is `cesmii/labLA/bme280sensor`.
- The object element ID used by the server-side examples is `cesmii_labLA_bme280sensor`.
- If your Arduino board uses a different serial port, update publisher_arduino.py before running it.
- If the i3X server is not listening on `localhost:8080`, adjust the curl commands and the local endpoint in Explorer accordingly.

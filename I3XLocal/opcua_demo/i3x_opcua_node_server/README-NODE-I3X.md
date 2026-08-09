# node-i3x Quick Start Guide

This guide shows how to install and run node-i3x from npm, connect it to an OPC UA server, and explore or subscribe to the resulting i3X data from either the command line or the I3XExplorer GUI.

The example OPC UA server used here is the additive manufacturing demo server from:

- $(HOME)/CESMII/cesmiipjcts/opcua_demo/opcua_server/opcua_additive_mfg_server.py

If needed, place that file in a separate folder such as opcua_server before starting it.

---

## 1. Prerequisites

Make sure the following are available:

- Node.js 20 or newer
- npm
- Python 3 with pip
- Optional: jq for nicer JSON output on the command line
- I3XExplorer GUI client

On macOS, you can install jq with:

```bash
brew install jq
```

---

## 2. Install node-i3x

Open a terminal and clone the node-i3x repository if it is not already present, then change into it:

```bash
# Clone the repository
git clone https://github.com/node-opcua/node-i3x.git
cd node-i3x
npm install
npm run build
```

Create a local environment file and set the OPC UA endpoint that node-i3x will use:

```bash
cp .env.example .env
```

Then edit the .env file or export the values in your shell:

```bash
export NODE_I3X_OPCUA_ENDPOINT=opc.tcp://127.0.0.1:4840/freeopcua/server/
export NODE_I3X_HOST=127.0.0.1
export NODE_I3X_PORT=8000
```

If you want to run without authentication requirements during testing, you can also set:

```bash
export NODE_I3X_REQUIRE_AUTH=false
```

---

## 3. Start the OPC UA server

The example server is a Python-based OPC UA server that publishes additive manufacturing telemetry such as chamber temperature, substrate temperature, laser power, powder level, machine state, job progress, and more.

Copy or place the server script into a folder such as opcua_server and run it from there:

```bash
mkdir -p opcua_server
cp $(HOME)/CESMII/cesmiipjcts/opcua_demo/opcua_server/opcua_additive_mfg_server.py opcua_server/
cd opcua_server
python3 -m venv .venv
source .venv/bin/activate
pip install asyncua
python opcua_additive_mfg_server.py --endpoint opc.tcp://0.0.0.0:4840/freeopcua/server/
```

Leave this terminal running. The server will expose an OPC UA endpoint on port 4840.

---

## 4. Start node-i3x

Open a second terminal and start the node-i3x application:

```bash
cd $(HOME)/CESMII/cesmiipjcts/i3xDev/node-i3x
NODE_I3X_OPCUA_ENDPOINT=opc.tcp://127.0.0.1:4840/freeopcua/server/ npm run dev
```

The server should begin listening on:

```text
http://127.0.0.1:8000
```

Verify that it is up:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/v1/info
```

You should see a healthy response and some basic server information.

---

## 5. Browse the data from the command line

### Health and metadata

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/v1/info
curl http://127.0.0.1:8000/v1/namespaces
```

### List objects and browse the model

```bash
curl -s "http://127.0.0.1:8000/v1/objects?includeMetadata=true" | jq
```

If you want to inspect a specific subset of the tree, you can also use:

```bash
curl -s -X POST http://127.0.0.1:8000/v1/objects/list \
  -H "Content-Type: application/json" \
  -d '{"elementIds":["<element-id-from-the-list>"]}' | jq
```

### Read current values

After you discover the relevant element IDs from the object list, you can fetch current values like this:

```bash
curl -s -X POST http://127.0.0.1:8000/v1/objects/value \
  -H "Content-Type: application/json" \
  -d '{"elementIds":["<element-id>"]}' | jq
```

For the additive manufacturing demo, the variables you will typically see are related to:

- ChamberTemperature
- SubstrateTemperature
- LaserPowerOutput
- RecoaterSpeed
- ShieldingGasPressure
- PowderLevelPercentage
- JobState
- ActiveLayerIndex

---

## 6. Subscribe to live updates from the command line

The i3X API supports subscriptions for streaming updates. The general workflow is:

1. Create a subscription
2. Register one or more element IDs to monitor
3. Open a stream to receive updates

### Step 1: Create a subscription

```bash
curl -s -X POST http://127.0.0.1:8000/v1/subscriptions \
  -H "Content-Type: application/json" \
  -d '{"clientId":"demo-client","displayName":"AM demo"}' | jq
```

The response will include a subscriptionId. Save it for the next steps.

### Step 2: Register monitored elements

```bash
curl -s -X POST http://127.0.0.1:8000/v1/subscriptions/register \
  -H "Content-Type: application/json" \
  -d '{
    "clientId":"demo-client",
    "subscriptionId":"<subscription-id>",
    "elementIds":["<element-id-1>","<element-id-2>"]
  }' | jq
```

### Step 3: Open the stream

```bash
curl -N -X POST http://127.0.0.1:8000/v1/subscriptions/stream \
  -H "Content-Type: application/json" \
  -d '{
    "clientId":"demo-client",
    "subscriptionId":"<subscription-id>",
    "lastSequenceNumber":0
  }'
```

This command stays open and prints live updates as values change.

### Optional: Poll for updates

```bash
curl -s -X POST http://127.0.0.1:8000/v1/subscriptions/sync \
  -H "Content-Type: application/json" \
  -d '{
    "clientId":"demo-client",
    "subscriptionId":"<subscription-id>",
    "lastSequenceNumber":0
  }' | jq
```

---

## 7. Use I3XExplorer GUI

The I3XExplorer GUI provides a visual way to browse the i3X address space and subscribe to values.

### Download and install

1. Go to the official I3X Explorer site:
   - https://www.acetechnologies.net/i3x
2. Download the desktop package for your operating system.
3. Install the application and launch it.

### Connect to node-i3x

In the explorer, connect to the local node-i3x server using:

```text
http://127.0.0.1:8000/v1
```

If the UI asks for a base URL, use the same address. If it asks for an API endpoint, use the root URL above.

### Browse and subscribe

Once connected:

1. Open the object tree or browse view.
2. Select the additive manufacturing machine or one of its variables.
3. Use the subscription or monitor action in the UI.
4. Register the selected element IDs and observe the live updates.

The exact button names can vary slightly depending on the I3XExplorer version, but the workflow is the same: connect, browse, select, subscribe, and monitor.

---

## 8. Runtime shell scripts

If you prefer to run the example through shell scripts instead of manually issuing curl commands, the repository also includes several runtime helpers in the runtime folder. These scripts are useful for browsing values, monitoring data continuously, and creating subscriptions from the shell.

Relevant files include:

- runtime/get_i3x_values.sh
- runtime/get_i3x_all_values.sh
- runtime/get_i3x_values_table.sh
- runtime/i3x_subscribe.sh
- runtime/i3x_auto_monitor.sh

Example usage:

```bash
cd $(HOME)/CESMII/cesmiipjcts/i3xDev/runtime
chmod +x get_i3x_values.sh i3x_subscribe.sh i3x_auto_monitor.sh
./get_i3x_values.sh
./i3x_subscribe.sh
./i3x_auto_monitor.sh
```

These scripts assume that node-i3x is already running and reachable at the local API endpoint.

---

## 9. Troubleshooting

### node-i3x cannot reach the OPC UA server

Confirm that:

- The Python OPC UA server is still running.
- The endpoint is set correctly:

```bash
export NODE_I3X_OPCUA_ENDPOINT=opc.tcp://127.0.0.1:4840/freeopcua/server/
```

### The server is running but the API is not responding

Check the health endpoint:

```bash
curl http://127.0.0.1:8000/health
```

If needed, restart node-i3x after updating the environment variables.

### Authentication errors

If your local environment requires it, start node-i3x with:

```bash
NODE_I3X_REQUIRE_AUTH=false npm run dev
```

---

## 9. Summary

Once everything is running, you should be able to:

- Start the OPC UA additive manufacturing server
- Start node-i3x from npm
- Browse the model over REST
- Read values through the API
- Subscribe to live updates from the command line or the I3XExplorer GUI

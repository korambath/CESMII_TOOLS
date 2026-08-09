# OPC UA Additive Manufacturing Demo

A Python-based OPC UA server and client pair that simulates a live metal additive manufacturing (AM) machine. The server exposes real-time telemetry following the OPC 40540 Additive Manufacturing companion specification. The client subscribes to all machine variables and prints structured JSON change events.

---

## Contents

| File | Purpose |
|---|---|
| `opcua_additive_mfg_server.py` | OPC UA server — simulates AM machine telemetry |
| `opcua_additive_mfg_client.py` | OPC UA client — subscribes and prints data changes |

---

## Requirements

```bash
pip install asyncua
```

Python 3.10+ is recommended.

---

## Server — `opcua_additive_mfg_server.py`

### What it does

- Starts an OPC UA server on `opc.tcp://0.0.0.0:4840/freeopcua/server/`
- Registers two namespaces:
  - `http://opcfoundation.org/UA/AdditiveManufacturing/`
  - `http://opcfoundation.org/UA/Machinery/`
- Builds an `AdditiveManufacturingMachine` object tree with:

| Section | Variables |
|---|---|
| **Identification** | Manufacturer, Model, SerialNumber, YearOfConstruction, HardwareRevision, SoftwareRevision, ActiveMaterialConsumable (BatchId, MaterialClass) |
| **OverallStatus** | AvailabilityState, ExecutionState, ActiveAlarmCount |
| **ProcessValues** | ChamberTemperature (°C), SubstrateTemperature (°C), AxisXPosition (mm), RecoaterSpeed (mm/s), LaserPowerOutput (W), ShieldingGasPressure (hPa), PowderLevelPercentage (%) |
| **JobManagement** | JobId, JobName, JobState, ActiveLayerIndex, TotalLayers, ElapsedTimeSec (s), EstimatedTimeRemainingSec (s) |

- Continuously updates process values at a configurable interval, simulating:
  - Temperature drift (chamber ±1.5 °C, substrate ±0.5 °C per cycle)
  - Laser power jitter (±4 W)
  - Powder level depletion (−0.03 % per cycle)
  - Layer progression toward completion (500 layers total)
  - Random 1 % chance of transitioning to `Paused` state
  - Random alarm count (0–2)

- Handles `SIGINT` / `SIGTERM` for graceful shutdown.

### Usage

```bash
# Default endpoint
python opcua_additive_mfg_server.py

# Custom endpoint and update interval
python opcua_additive_mfg_server.py \
    --endpoint opc.tcp://0.0.0.0:4840/freeopcua/server/ \
    --update-interval 2

# Via environment variable
OPCUA_SERVER_ENDPOINT=opc.tcp://0.0.0.0:4840/freeopcua/server/ python opcua_additive_mfg_server.py
```

| Argument | Default | Description |
|---|---|---|
| `--endpoint` | `opc.tcp://0.0.0.0:4840/freeopcua/server/` | Server endpoint URL |
| `--update-interval` | `5` | Seconds between telemetry updates |

---

## Client — `opcua_additive_mfg_client.py`

### What it does

- Connects to the server and discovers all namespaces.
- Locates the `AdditiveManufacturingMachine` object in the AM namespace.
- Recursively walks the address space and subscribes to every `Variable` node.
- On each data change, prints a JSON record to stdout:

```json
{
  "browse_name": "ChamberTemperature",
  "display_name": "ChamberTemperature",
  "namespace": "http://opcfoundation.org/UA/AdditiveManufacturing/",
  "node_id": "ns=1;i=1002",
  "value": 325.47,
  "unit": "°C",
  "source_timestamp": "2026-08-09T14:32:01.123456+00:00",
  "server_timestamp": "2026-08-09T14:32:01.124000+00:00",
  "status": "Good"
}
```

### Usage

```bash
# Default (connects to localhost)
python opcua_additive_mfg_client.py

# Custom server URL
python opcua_additive_mfg_client.py --server-url opc.tcp://192.168.1.100:4840/freeopcua/server/

# Via environment variable
OPCUA_SERVER_URL=opc.tcp://192.168.1.100:4840/freeopcua/server/ python opcua_additive_mfg_client.py
```

| Argument | Default | Description |
|---|---|---|
| `--server-url` | `opc.tcp://127.0.0.1:4840/freeopcua/server/` | OPC UA server endpoint to connect to |

---

## Quick Start (two terminals)

```bash
# Terminal 1 — start the server
python opcua_additive_mfg_server.py --update-interval 2

# Terminal 2 — start the client
python opcua_additive_mfg_client.py
```

---

## GUI Client with Live Plotting — `opcua-client-gui`

[`opcua-client-gui`](https://github.com/FreeOpcUa/opcua-client-gui) is a free, open-source desktop application that can browse any OPC UA server's address space, subscribe to nodes, and display live plots — no additional code required.

### Install

```bash
pip install opcua-client
```

> On macOS you may also need `PyQt5` if it is not pulled in automatically:
> ```bash
> pip install PyQt5 opcua-client
> ```

### Launch

```bash
opcua-client
```

### Connect to the demo server

1. In the **Endpoint** field at the top, enter:
   ```
   opc.tcp://127.0.0.1:4840/freeopcua/server/
   ```
2. Click **Connect**.
3. The left panel shows the address space tree. Expand:
   ```
   Objects → AdditiveManufacturingMachine → ProcessValues
   ```
4. **Subscribe to a node for live data:**
   - Right-click any variable (e.g. `ChamberTemperature`) → **Subscribe to data change**.
   - The **Data Change** tab at the bottom shows streaming values.

5. **Plot a variable:**
   - Right-click the variable → **Add to plot**.
   - Switch to the **Graph** tab to see a real-time scrolling chart.
   - Repeat for multiple variables to overlay them on the same plot.

### Suggested variables to plot

| Variable | Path |
|---|---|
| ChamberTemperature | ProcessValues → ChamberTemperature |
| SubstrateTemperature | ProcessValues → SubstrateTemperature |
| LaserPowerOutput | ProcessValues → LaserPowerOutput |
| PowderLevelPercentage | ProcessValues → PowderLevelPercentage |
| ActiveLayerIndex | JobManagement → ActiveLayerIndex |
| EstimatedTimeRemainingSec | JobManagement → EstimatedTimeRemainingSec |

---

## Alternative: Python live-plot client with `matplotlib`

[`opcua_live_plot.py`](opcua_live_plot.py) is a scriptable alternative that subscribes to the four main process sensors and displays a 2×2 grid of auto-scaling live charts, updating every 500 ms.

### Install

```bash
pip install asyncua matplotlib
```

### Run

```bash
python opcua_live_plot.py
```

Close the plot window to exit and unsubscribe cleanly.

---

## Address Space Summary

```
Objects/
└── AdditiveManufacturingMachine  (ns=AdditiveManufacturing)
    ├── Identification
    │   ├── Manufacturer
    │   ├── Model
    │   ├── SerialNumber
    │   ├── YearOfConstruction
    │   ├── HardwareRevision
    │   ├── SoftwareRevision
    │   └── ActiveMaterialConsumable
    │       ├── BatchId
    │       └── MaterialClass
    ├── OverallStatus
    │   ├── AvailabilityState
    │   ├── ExecutionState
    │   └── ActiveAlarmCount
    ├── ProcessValues
    │   ├── ChamberTemperature    [°C]
    │   ├── SubstrateTemperature  [°C]
    │   ├── AxisXPosition         [mm]
    │   ├── RecoaterSpeed         [mm/s]
    │   ├── LaserPowerOutput      [W]
    │   ├── ShieldingGasPressure  [hPa]
    │   └── PowderLevelPercentage [%]
    └── JobManagement
        ├── JobId
        ├── JobName
        ├── JobState
        ├── ActiveLayerIndex
        ├── TotalLayers
        ├── ElapsedTimeSec        [s]
        └── EstimatedTimeRemainingSec [s]
```

---

## License

MIT

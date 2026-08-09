import argparse
import asyncio
import os
from asyncua import Server, ua
from datetime import datetime, timezone
from random import Random

import logging
import random
import signal
from datetime import datetime
import socket


'''
| Variable                  | Unit      |
| --------------------------| --------- |
| ChamberTemperature        | °C        |
| SubstrateTemperature      | °C        |
| LaserPowerOutput          | W         |
| RecoaterSpeed             | mm/s      |
| AxisXPosition             | mm        |
| ShieldingGasPressure      | Pa or hPa |
| PowderLevelPercentage     | %         |
| LayerHeight               | µm        |
| ScanSpeed                 | mm/s      |
| BuildTime                 | s         |
| ElapsedTimeSec            | s         |
| EstimatedTimeRemainingSec | s         |


'''

rng = Random()

UNIT_ID_BY_SYMBOL = {
    "°C": 4408652,
    "W": 4408653,
    "mm": 4408654,
    "mm/s": 4408655,
    "hPa": 4408656,
    "%": 4408657,
    "s": 4408658,
}


async def add_sensor(
    parent,
    namespace,
    name,
    value,
    unit,
):

    node = await parent.add_variable(
        namespace,
        name,
        value,
    )

    unit_id = UNIT_ID_BY_SYMBOL.get(unit, 0)

    await node.add_property(
        0,
        "EngineeringUnits",
        ua.EUInformation(
            NamespaceUri="http://www.opcfoundation.org/UA/units/un/cefact",
            UnitId=unit_id,
            DisplayName=ua.LocalizedText(unit),
            Description=ua.LocalizedText(unit),
        )
    )

    return node


async def read_engineering_units(node):

    properties = await node.get_children()

    for prop in properties:

        browse_name = await prop.read_browse_name()

        if browse_name.Name == "EngineeringUnits":

            eu = await prop.read_value()
            return eu.DisplayName.Text

    return None


async def write_variable(
    variable,
    value,
    timestamp: datetime,
    logger: logging.Logger,
):
    dv = ua.DataValue(
        ua.Variant(value)
    )

    dv.SourceTimestamp = timestamp
    dv.ServerTimestamp = timestamp

    await variable.write_value(dv)

    browse_name = await variable.read_browse_name()

    logger.info(
        "%s = %s",
        browse_name.Name,
        value,
    )



async def main(args=None):
    parser = argparse.ArgumentParser(description="Run the OPC UA additive manufacturing demo server")
    parser.add_argument("--endpoint", default=os.getenv("OPCUA_SERVER_ENDPOINT", "opc.tcp://0.0.0.0:4840/freeopcua/server/"))
    parser.add_argument("--update-interval", type=int, default=5, help="Seconds between telemetry updates")
    parsed_args = parser.parse_args(args)

    # 1. Initialize the Server
    logger = logging.getLogger(__name__)
    server = Server()
    await server.init()
    
    endpoint = parsed_args.endpoint
    server.set_endpoint(endpoint)
    server.set_server_name("OPC 40540 Comprehensive AM Server")

    # 2. Register Namespaces
    uri_am = "http://opcfoundation.org/UA/AdditiveManufacturing/"
    uri_machinery = "http://opcfoundation.org/UA/Machinery/"
    
    idx_am = await server.register_namespace(uri_am)
    idx_machinery = await server.register_namespace(uri_machinery)

    # 3. Build Objects Tree under Objects Folder
    objects_node = server.nodes.objects
    am_machine = await objects_node.add_object(idx_am, "AdditiveManufacturingMachine")


    # ==========================================
    # A. IDENTIFICATION (Nameplate & Components)
    # ==========================================
    identification = await am_machine.add_object(idx_am, "Identification")
    
    manufacturer = await identification.add_variable(idx_am, "Manufacturer", "AM Technologies Inc.")
    model = await identification.add_variable(idx_am, "Model", "FusionPro-X1")
    serial_number = await identification.add_variable(idx_am, "SerialNumber", "FP-2026-9901")
    year_of_construction = await identification.add_variable(idx_am, "YearOfConstruction", 2026)
    hardware_revision = await identification.add_variable(idx_am, "HardwareRevision", "Rev 2.1")
    software_revision = await identification.add_variable(idx_am, "SoftwareRevision", "v4.5.0-build12")
    
    # Sub-component / Material Identification block
    material_info = await identification.add_object(idx_am, "ActiveMaterialConsumable")
    material_batch = await material_info.add_variable(idx_am, "BatchId", "BATCH-Ti6Al4V-883")
    material_type = await material_info.add_variable(idx_am, "MaterialClass", "Titanium Powder")


    chamber_temperature = 325.0
    substrate_temperature = 140.0
    laser_power_output = 275.0
    powder_level = 100.0
    layer = 0
    elapsed = 0
    remaining = 18000
    execution = "Running"
    total_layer_count = 500
    update_interval_seconds = parsed_args.update_interval

    # ==========================================
    # B. OVERALL STATUS & MONITORING
    # ==========================================
    overall_status = await am_machine.add_object(idx_am, "OverallStatus")
    
    availability_state = await overall_status.add_variable(idx_am, "AvailabilityState", "Available") # Available, OutOfService
    execution_state = await overall_status.add_variable(idx_am, "ExecutionState", execution)         # Idle, Running, Paused, Aborted, Completed
    active_alarm_count = await overall_status.add_variable(idx_am, "ActiveAlarmCount", 0)

    # ==========================================
    # C. PROCESS VALUES (Telemetry Categories)
    # ==========================================

    process_values = await am_machine.add_object(idx_am, "ProcessValues")
    
    # 1. Thermal Monitoring
    #chamber_temp = await process_values.add_variable(idx_am, "ChamberTemperature", chamber_temperature) # °C
    #substrate_temp = await process_values.add_variable(idx_am, "SubstrateTemperature", substrate_temperature) # °C

    chamber_temp = await add_sensor(
        process_values,
        idx_am,
        "ChamberTemperature",
        chamber_temperature,
        "°C",
    )

    range_property = await chamber_temp.add_property(
        0,
        "EURange",
        ua.Range()
    )

    range_property.Low = 0
    range_property.High = 500


    value = await chamber_temp.read_value()
    print(f"Value: {value}")

    properties = await chamber_temp.get_children()

    for p in properties:
        print("Property reads")
        print(await p.read_browse_name())

    unit = await read_engineering_units(chamber_temp)

    print(
        f"Unit = {unit}"
    )



    substrate_temp = await add_sensor(
        process_values,
        idx_am,
        "SubstrateTemperature",
        substrate_temperature,
        "°C",
    )


    
    # 2. Kinematic & Motion Monitoring
    axis_x_pos = await add_sensor(
        process_values,
        idx_am,
        "AxisXPosition",
        150.2,
        "mm",
    )
    recoater_speed = await add_sensor(
        process_values,
        idx_am,
        "RecoaterSpeed",
        120.0,
        "mm/s",
    )
    
    # 3. Laser / Energy Monitoring
    #laser_power = await process_values.add_variable(idx_am, "LaserPowerOutput", laser_power_output) # Watts
    laser_power = await add_sensor(
        process_values,
        idx_am,
        "LaserPowerOutput",
        250.0,
        "W",
    )
    shielding_gas_pressure = await add_sensor(
        process_values,
        idx_am,
        "ShieldingGasPressure",
        1013.25,
        "hPa",
    )
    
    # 4. Consumable / Material Levels
    powder_level_pct = await add_sensor(
        process_values,
        idx_am,
        "PowderLevelPercentage",
        powder_level,
        "%",
    )

    # ==========================================
    # D. JOB MANAGEMENT & PROGRESS
    # ==========================================
    job_management = await am_machine.add_object(idx_am, "JobManagement")
    
    current_job_id = await job_management.add_variable(idx_am, "JobId", "JOB-2026-07-001")
    current_job_name = await job_management.add_variable(idx_am, "JobName", "AerospaceBracket_A1")
    job_state = await job_management.add_variable(idx_am, "JobState", "Executing") # Idle, Executing, Paused, Completed, Aborted
    
    # Progress Metrics
    active_layer_index = await add_sensor(
        job_management,
        idx_am,
        "ActiveLayerIndex",
        42,
        "",
    )
    total_layers = await add_sensor(
        job_management,
        idx_am,
        "TotalLayers",
        total_layer_count,
        "",
    )
    elapsed_time_sec = await add_sensor(
        job_management,
        idx_am,
        "ElapsedTimeSec",
        elapsed,
        "s",
    )
    estimated_time_remaining_sec = await add_sensor(
        job_management,
        idx_am,
        "EstimatedTimeRemainingSec",
        remaining,
        "s",
    )

    # Make all necessary state and parameter variables writable for control simulation
    writable_nodes = [
        manufacturer, model, serial_number, year_of_construction,
        hardware_revision, software_revision, material_batch, material_type,
        availability_state, execution_state, current_job_id, current_job_name, job_state
    ]
    for node in writable_nodes:
        await node.set_writable()

    # 4. Start Server and Simulate Live Values
    stop_event = asyncio.Event()

    def handle_shutdown():
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in ("SIGINT", "SIGTERM"):
        try:
            loop.add_signal_handler(getattr(signal, sig), handle_shutdown)
        except (AttributeError, NotImplementedError):
            pass

    async with server:
        hostname = socket.gethostname()
        start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        print(
            f"\n[{start_time}] Starting Comprehensive OPC 40540 AM Server\n"
            f"on host '{hostname}' at {endpoint}"
        )
        

        while not stop_event.is_set():

            timestamp = datetime.now(timezone.utc)

            #
            # Simulate process
            #

            chamber_temperature += rng.uniform(-1.5, 1.5)
            substrate_temperature += rng.uniform(-0.5, 0.5)

            laser_power_output += rng.uniform(-4, 4)

            powder_level = max(
                0,
                powder_level - 0.03,
            )

            elapsed += update_interval_seconds
            remaining = max(
                0,
                remaining - update_interval_seconds,
            )

            if execution == "Running":

                layer += 1

                if layer >= total_layer_count:
                    execution = "Completed"

            #
            # Occasional pause
            #

            if rng.random() < 0.01:
                execution = "Paused"

            elif execution == "Paused":
                execution = "Running"

            alarms = rng.randint(0, 2)

            await asyncio.gather(

                write_variable(
                    chamber_temp,
                    round(chamber_temperature, 2),
                    timestamp,
                    logger,
                ),

                write_variable(
                    substrate_temp,
                    round(substrate_temperature, 2),
                    timestamp,
                    logger,
                ),

                write_variable(
                    laser_power,
                    round(laser_power_output, 1),
                    timestamp,
                    logger,
                ),

                write_variable(
                    powder_level_pct,
                    round(powder_level, 2),
                    timestamp,
                    logger,
                ),

                write_variable(
                    active_layer_index,
                    layer,
                    timestamp,
                    logger,
                ),

                write_variable(
                    elapsed_time_sec,
                    elapsed,
                    timestamp,
                    logger,
                ),

                write_variable(
                    estimated_time_remaining_sec,
                    remaining,
                    timestamp,
                    logger,
                ),

                write_variable(
                    execution_state,
                    execution,
                    timestamp,
                    logger,
                ),

                write_variable(
                    active_alarm_count,
                    alarms,
                    timestamp,
                    logger,
                ),
            )

            await asyncio.sleep(update_interval_seconds)

        print("Shutdown requested; stopping server.")



if __name__ == "__main__":
    logging.basicConfig(
           #level=logging.INFO,
           level=logging.WARN,
           format="%(asctime)s %(levelname)s %(message)s",
    )


    asyncio.run(main(), debug=True)
    #asyncio.run(main())

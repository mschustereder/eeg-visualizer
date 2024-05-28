#Code taken from https://github.com/abcsds/hrv/blob/main/src/05_multiple_lsl.py
# Author: Luis Alberto Barradas Chacón 

import asyncio
import contextlib
import logging
from typing import Iterable

from bleak import BleakScanner, BleakClient
from pylsl import StreamInfo, StreamOutlet


HR_UUID = "00002a37-0000-1000-8000-00805f9b34fb"


def interpret(data):
    """
    from fg1/BLEHeartRateLogger
    data is a list of integers corresponding to readings from the BLE HR monitor
    """
    byte0 = data[0]
    res = {}
    res["hrv_uint8"] = (byte0 & 1) == 0
    sensor_contact = (byte0 >> 1) & 3
    if sensor_contact == 2:
        res["sensor_contact"] = "No contact detected"
    elif sensor_contact == 3:
        res["sensor_contact"] = "Contact detected"
    else:
        res["sensor_contact"] = "Sensor contact not supported"

    res["ee_status"] = ((byte0 >> 3) & 1) == 1
    res["rr_interval"] = ((byte0 >> 4) & 1) == 1
    if res["hrv_uint8"]:
        res["hr"] = data[1]
        i = 2
    else:
        res["hr"] = (data[2] << 8) | data[1]
        i = 3
    if res["ee_status"]:
        res["ee"] = (data[i + 1] << 8) | data[i]
        i += 2
    if res["rr_interval"]:
        res["rr"] = []
        while i < len(data):
            # Note: Need to divide the value by 1024 to get in seconds
            res["rr"].append((data[i + 1] << 8) | data[i])
            i += 2
    return res

# Define the addresses, names, and UUIDs of devices
devices = [
    # {"address": "CD:4B:39:D5:62:36", "name": "HR-70ECAB5D", "uuid": "00002a37-0000-1000-8000-00805f9b34fb"},
    # {"address": "CB:1E:40:C8:F6:03", "name": "HR-70EC985D", "uuid": "00002a37-0000-1000-8000-00805f9b34fb"},
    # {"address": "DB:D1:1C:A1:57:3D", "name": "HR-70EC845D", "uuid": "00002a37-0000-1000-8000-00805f9b34fb"},
    # {"address": "FF:D2:0F:F3:FE:EC", "name": "HR-70ECE75D", "uuid": "00002a37-0000-1000-8000-00805f9b34fb"},
    # {"address": "E8:9B:59:E2:8C:71", "name": "HR-70ECD35D", "uuid": "00002a37-0000-1000-8000-00805f9b34fb"},
    # {"address": "F2:48:B2:FF:3E:CE", "name": "HR-70ECD05D", "uuid": "00002a37-0000-1000-8000-00805f9b34fb"},  
]

# async def connect_device(device, lock):
#     address = device["address"]
#     client = BleakClient(address)
#     device_name = device["name"]

#     try:
#         async with lock:
#             await client.connect()
#             print(f"Device Address: {client.address}")
#             hr_data = await client.start_notify(device["uuid"], lambda data: callback(data, device_name, outlet_hr, outlet_rr))
#             while True:
#                 await asyncio.sleep(0.1)
#     except KeyboardInterrupt:
#         print(f"Stopped by user")
#         await client.stop_notify(device["uuid"])
#     except Exception as e:
#         print(f"Exception: {e}")
#     finally:
#         await client.disconnect()

# def callback(data, device_name, outlet_hr, outlet_rr):
#     if data:
#         data = interpret(data, device_name)
#         print(f"{device_name} - HR: {data['hr']}")
#         outlet_hr.push_sample([data['hr']])
#         if "rr" in data.keys():
#             for data_rr in data["rr"]:
#                 print(f"{device_name} - RR: {data_rr}")
#                 outlet_rr.push_sample([data_rr])
#         return data
#     else:
#         return None

# async def main_multiple_devices(devices):
#     # Create a lock for device connection
#     connection_lock = asyncio.Lock()

#     # Create LSL outlets for all devices
#     for device in devices:
#         device_name = device["name"]
#         info_hr = StreamInfo(name=f'HR_{device_name}',
#             type='Markers',
#             channel_count=1,
#             channel_format='int32',
#             source_id=f'HR_{device_name}_markers'
#         )
#         info_rr = StreamInfo(name=f'RR_{device_name}',
#             type='Markers',
#             channel_count=1,
#             channel_format='int32',
#             source_id=f'RR_{device_name}_markers'
#         )
#         outlet_hr = StreamOutlet(info_hr)
#         outlet_rr = StreamOutlet(info_rr)

#         await connect_device(device, connection_lock)

async def connect_to_device(
    lock: asyncio.Lock,
    device: dict,
    address: str,
    outlet_hr: StreamOutlet,
    outlet_rr: StreamOutlet,
):
    logging.info("starting %s task", address)

    try:
        async with contextlib.AsyncExitStack() as stack:
            # Trying to establish a connection to two devices at the same time
            # can cause errors, so use a lock to avoid this.
            async with lock:
                logging.info("scanning for %s", address)

                found_device = await BleakScanner.find_device_by_address(address, timeout=30.0, scanning_mode="active")

                logging.info("stopped scanning for %s", address)

                if found_device is None:
                    logging.error("%s not found", address)
                    return

                client = BleakClient(found_device)

                logging.info("connecting to %s", address)

                await stack.enter_async_context(client)

                logging.info("connected to %s", address)

                # This will be called immediately before client.__aexit__ when
                # the stack context manager exits.
                stack.callback(logging.info, "disconnecting from %s", address)

            # The lock is released here. The device is still connected and the
            # Bluetooth adapter is now free to scan and connect another device
            # without disconnecting this one.

            # def callback(_, data):
            #     logging.info("%s received %r", address, data)

            def callback(sender: int, data: bytearray):
                if data:
                    data = interpret(data)
                    logging.info(f"{device['name']} HR: {data['hr']}")
                    outlet_hr.push_sample([data['hr']])
                    if "rr" in data.keys():
                        for data_rr in data["rr"]:
                            logging.info(f"    {device['name']} RR: {data_rr}")
                            outlet_rr.push_sample([data_rr])
                    return data
                else:
                    return None

            hr_data = await client.start_notify(HR_UUID, callback)
            while True:
                await asyncio.sleep(0.1)

        # The stack context manager exits here, triggering disconnection.
        # await client.stop_notify(HR_UUID)
        logging.info("disconnected from %s", address)

    except Exception:
        logging.exception("error with %s", address)


async def main(devices: dict, addresses: Iterable[str]):
    device_names = [d["name"] for d in devices]
    infos_hr = [
        StreamInfo(name=f'HR_{device_name}',
            type='Markers',
            channel_count=1,
            channel_format='int32',
            source_id=f'HR_{device_name}_markers')
        for device_name in device_names
    ]
    infos_rr = [
        StreamInfo(name=f'RR_{device_name}',
            type='Markers',
            channel_count=1,
            channel_format='int32',
            source_id=f'RR_{device_name}_markers')
        for device_name in device_names
    ]
    outlets_hr = [StreamOutlet(info_hr) for info_hr in infos_hr]
    outlets_rr = [StreamOutlet(info_rr) for info_rr in infos_rr]
    lock = asyncio.Lock()
    await asyncio.gather(
        *(
            connect_to_device(lock, device, address, outlet_hr, outlet_rr)
            for device, address, outlet_hr, outlet_rr in zip(devices, addresses, outlets_hr, outlets_rr)
        )
    )


if __name__ == "__main__":
    devices = [
        # {"address": "DB:6E:5B:87:4E:50", "name": "Polar H10", "uuid": "00002a37-0000-1000-8000-00805f9b34fb"},
        # {"address": "C8:28:E6:77:9D:0D", "name": "Polar H10 D6B5C724", "uuid": "00002a37-0000-1000-8000-00805f9b34fb"},
        # {"address": "A0:9E:1A:C5:36:32", "name": "Polar Sense C5363229", "uuid": "00002a37-0000-1000-8000-00805f9b34fb"},
        {"address": "D6:E7:A7:D1:29:AE", "name": "Polar H10 CA549123", "uuid": "00002a37-0000-1000-8000-00805f9b34fb"},
        # {"address": "DE:C5:AC:14:25:28", "name": "HR6 0039090", "uuid": "00002a37-0000-1000-8000-00805f9b34fb"},
        # {"address": "CD:4B:39:D5:62:36", "name": "HR-70ECAB5D", "uuid": "00002a37-0000-1000-8000-00805f9b34fb"},
        # {"address": "CB:1E:40:C8:F6:03", "name": "HR-70EC985D", "uuid": "00002a37-0000-1000-8000-00805f9b34fb"},
        # {"address": "DB:D1:1C:A1:57:3D", "name": "HR-70EC845D", "uuid": "00002a37-0000-1000-8000-00805f9b34fb"},
        # {"address": "FF:D2:0F:F3:FE:EC", "name": "HR-70ECE75D", "uuid": "00002a37-0000-1000-8000-00805f9b34fb"},
        # {"address": "E8:9B:59:E2:8C:71", "name": "HR-70ECD35D", "uuid": "00002a37-0000-1000-8000-00805f9b34fb"},
        # {"address": "F2:48:B2:FF:3E:CE", "name": "HR-70ECD05D", "uuid": "00002a37-0000-1000-8000-00805f9b34fb"},
    ]
    addresses = [d["address"] for d in devices]
    debug = False
    log_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)-15s %(name)-8s %(levelname)s: %(message)s",
    )

    asyncio.run(main(devices, addresses))
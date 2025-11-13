import OpenOPC
import time
from datetime import datetime
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

import os
from dotenv import load_dotenv

# load .env
load_dotenv()

# konfigurasi OPC
OPC_SERVER = os.getenv("OPC_SERVER")
TAGS = []  
# konfigurasi InfluxDB
INFLUX_URL = os.getenv("INFLUX_URL")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN")
INFLUX_ORG = os.getenv("INFLUX_ORG")
INFLUX_BUCKET = os.getenv("INFLUX_BUCKET")
# koneksi OPC DA
opc = OpenOPC.client()
opc.connect(OPC_SERVER)
print("Connected to OPC DA:", OPC_SERVER)


client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
write_api = client.write_api(write_options=SYNCHRONOUS)


while True:
    try:
        for tag in TAGS:
            value, quality, timestamp = opc.read(tag)
            print(f"{tag}: {value} (Q={quality}) at {timestamp}")

   
            point = (
                Point("OPC_Sim")
                .tag("source", "Simulation")
                .tag("tagname", tag)
                .field("value", float(value) if value is not None else 0)
                .time(datetime.utcnow(), WritePrecision.NS)
            )
            write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)

        time.sleep(1) 

    except Exception as e:
        print("Error:", e)
        time.sleep(5)

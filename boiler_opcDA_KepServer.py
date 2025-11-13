import os
import time
import logging
from datetime import datetime, timezone

import OpenOPC
from dotenv import load_dotenv
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

OPC_SERVER   = os.getenv("OPC_SERVER", "Kepware.KEPServerEX.V6")
OPC_HOST     = os.getenv("OPC_HOST", "").strip() or None
KEP_CHANNEL  = os.getenv("KEP_CHANNEL", "BOILER").strip()
WHITELIST    = [s.strip() for s in os.getenv("KEP_ITEMS","").split(",") if s.strip()]
POLL_SEC     = float(os.getenv("POLL_SEC", "1"))
TOL          = float(os.getenv("CHANGE_TOLERANCE", "0.0"))  

INFLUX_URL   = os.getenv("INFLUX_URL")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN")
INFLUX_ORG   = os.getenv("INFLUX_ORG")
INFLUX_BUCKET= os.getenv("INFLUX_BUCKET")
MEAS         = os.getenv("INFLUX_MEASUREMENT", "boiler_kepopc")

def norm_value(v):
    if isinstance(v, bool): return 1.0 if v else 0.0
    try: return float(v)
    except: return None

def list_strings(items):
    out = []
    for it in items:
        out.append(it[0] if isinstance(it, (list, tuple)) else it)
    return out

def opc_connect():
    opc = OpenOPC.client()
    if OPC_HOST: opc.connect(OPC_SERVER, OPC_HOST)
    else:        opc.connect(OPC_SERVER)
    return opc

def discover_items_under_channel(opc, channel: str):
    devs = list_strings(opc.list(f"{channel}.*"))
    found = []
    for dev in devs:
        tags = list_strings(opc.list(f"{dev}.*"))
        if not tags:
            tags = list_strings(opc.list(f"{dev}.*.*"))
        for t in tags:
            children = list_strings(opc.list(f"{t}.*"))
            found.extend(children if children else [t])
    found = sorted(set([f for f in found if f.startswith(channel + ".")]))
    logging.info(f"Discovered {len(found)} items under {channel}.")
    return found

def main():
    # Influx
    influx = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
    write_api = influx.write_api(write_options=SYNCHRONOUS)
    logging.info("Connected to InfluxDB.")

    # OPC
    opc = opc_connect()
    logging.info(f"Connected to OPC DA: {OPC_SERVER}")

    # Items 
    if WHITELIST:
        items = WHITELIST
        logging.info(f"Using whitelist ({len(items)} items).")
    else:
        items = discover_items_under_channel(opc, KEP_CHANNEL)
        if not items:
            raise RuntimeError("No items found. check.env")

    # Batch group
    group = "kep_boiler_batch"
    try: opc.remove(group)
    except: pass
    opc.read(items, group=group, update=0)
    
    # Last values
    last_val = {}      
    last_qual = {}  

    #Queue of points to write
    pending_points = []
    try:
        while True:
            rows = opc.read(items, group=group, update=0)
            points = []
            now = datetime.now(timezone.utc)

            for (item, raw_val, qual, ts) in rows:
                val = norm_value(raw_val)
                q = str(qual)

                if val is None:
                    if item not in last_qual or last_qual[item] != q:
                        last_qual[item] = q
                    continue

                changed = False
                if item not in last_val:
                    changed = True
                else:
                    prev = last_val[item]
                    if abs(val - prev) >= TOL:
                        changed = True

                if item not in last_qual or last_qual[item] != q:
                    changed = True

                if changed:
                    points.append(
                        Point(MEAS)
                        .tag("source", "KepwareDA")
                        .tag("channel", KEP_CHANNEL)
                        .tag("item", item)
                        .field("value", val)
                        .field("quality", 1 if q.lower().startswith("good") else 0)
                        .time(now, WritePrecision.NS)
                    )
                    last_val[item] = val
                    last_qual[item] = q
            

            

            if points:
                pending_points.extend(points)


            if pending_points:
                try:
                    write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=pending_points)
                    

                    logging.info(f"Successfully wrote {len(pending_points)} points to InfluxDB.")
                    pending_points = [] 
                
                except Exception as e:

                    logging.warning(f"Failed to write to InfluxDB: {e}. {len(pending_points)} points go in queue.")
            time.sleep(POLL_SEC)

    except KeyboardInterrupt:
        logging.info("Stopping.")
    finally:
        try: opc.close()
        except: pass
        try: influx.close()
        except: pass
        logging.info("Shutdown.")

if __name__ == "__main__":
    main()
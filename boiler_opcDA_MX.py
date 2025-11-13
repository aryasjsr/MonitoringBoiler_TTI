import os
import time
import logging
from datetime import datetime, timezone

import OpenOPC
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from dotenv import load_dotenv

# =========================
# Setup & Config
# =========================
load_dotenv()

OPC_SERVER       = os.getenv("OPC_SERVER", "MELSOFT.MXOPC.4")   
OPC_HOST         = os.getenv("OPC_HOST")                        
OPC_BROWSE_ROOT  = os.getenv("OPC_BROWSE_ROOT", "Dev01.Dynamic Tags.*")
OPC_WHITELIST    = [s.strip() for s in os.getenv("OPC_WHITELIST", "").split(",") if s.strip()]
OPC_POLL_MS      = int(os.getenv("OPC_POLL_MS", "1000"))
OPC_TIMEOUT_S    = int(os.getenv("OPC_TIMEOUT_S", "5"))

INFLUX_URL       = os.getenv("INFLUX_URL")
INFLUX_TOKEN     = os.getenv("INFLUX_TOKEN")
INFLUX_ORG       = os.getenv("INFLUX_ORG")
INFLUX_BUCKET    = os.getenv("INFLUX_BUCKET")

MEASUREMENT      = os.getenv("INFLUX_MEASUREMENT", "plc_mxopc")
SOURCE_TAG       = os.getenv("SOURCE_TAG", "MXOPC")
MACHINE_TAG      = os.getenv("MACHINE_TAG", "Dev01")  #

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

# =========================
# Helpers
# =========================
def normalize_value(v):
    """
    Konversi nilai OPC ke numeric:
    - True/False -> 1/0
    - int/float -> apa adanya
    - string -> coba cast ke float, kalau gagal -> None
    """
    try:
        if isinstance(v, bool):
            return 1 if v else 0
        if isinstance(v, (int, float)):
            return v
        # WORD dari beberapa OPC bisa datang sebagai int; kalau string, coba cast
        if isinstance(v, str):
            v = v.strip()
            if v.isdigit() or (v.startswith("-") and v[1:].isdigit()):
                return int(v)
            return float(v)
    except Exception:
        return None
    return None

def connect_opc():
    opc = OpenOPC.client()
    opc.timeout = OPC_TIMEOUT_S
    if OPC_HOST:
        opc.connect(OPC_SERVER, OPC_HOST)
    else:
        opc.connect(OPC_SERVER)
    return opc

def browse_tags(opc):
    """
    Kembalikan daftar item-id yang akan dibaca.
    - Jika ada OPC_WHITELIST, pakai itu.
    - Jika tidak, auto-discover dengan pattern OPC_BROWSE_ROOT.
    """
    if OPC_WHITELIST:
        logging.info(f"Using whitelist tags ({len(OPC_WHITELIST)} items).")
        return OPC_WHITELIST

    logging.info(f"Browsing MX OPC with pattern: {OPC_BROWSE_ROOT}")
    items = opc.list(OPC_BROWSE_ROOT)
    # Hasil list bisa berupa list item-id langsung atau tuples,
    # tergantung server. Pastikan berupa string item-id.
    flat_items = []
    for it in items:
        if isinstance(it, (list, tuple)) and len(it) > 0:
            flat_items.append(it[0])
        elif isinstance(it, str):
            flat_items.append(it)
    flat_items = sorted(set(flat_items))
    logging.info(f"Discovered {len(flat_items)} tags.")
    return flat_items

def connect_influx():
    client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
    write_api = client.write_api(write_options=SYNCHRONOUS)
    return client, write_api

# =========================
# Main loop
# =========================
def main():
    # Connect Influx
    client, write_api = connect_influx()
    logging.info("Connected to InfluxDB.")

    # Connect OPC
    opc = connect_opc()
    logging.info(f"Connected to OPC DA server: {OPC_SERVER}")

    # Tag list
    tags = browse_tags(opc)
    if not tags:
        raise RuntimeError("No OPC tags found. Check OPC_WHITELIST or OPC_BROWSE_ROOT.")

    # Optional: Create a group for efficient reads
    group_name = "mxopc_batch"
    try:
        opc.remove(group_name)   # cleanup if exists
    except Exception:
        pass
    opc.read(tags, group=group_name, update=0)  # initialize group

    poll_sec = max(0.05, OPC_POLL_MS / 1000.0)

    try:
        while True:
            try:
                # Batch read: returns list of tuples (item, value, quality, time)
                results = opc.read(tags, group=group_name, update=0)

                points = []
                now_ns = datetime.now(timezone.utc)

                for (item, value, quality, ts) in results:
                    val = normalize_value(value)
                    if val is None:
                        # Skip jika tidak bisa dinormalisasi
                        continue

                    p = (
                        Point(MEASUREMENT)
                        .tag("source", SOURCE_TAG)
                        .tag("machine", MACHINE_TAG)
                        .tag("tagname", item)
                        .field("value", val)
                        .field("quality", 1 if str(quality).lower().startswith("good") else 0)
                        .time(now_ns, WritePrecision.NS)
                    )
                    points.append(p)

                if points:
                    write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=points)

                time.sleep(poll_sec)

            except KeyboardInterrupt:
                logging.info("Stopping...")
                break

            except Exception as e:
                logging.error(f"Read/Write error: {e}. Retrying in 3s...")
                time.sleep(3)

                # Coba reconnect jika perlu
                try:
                    opc.close()
                except Exception:
                    pass
                try:
                    opc = connect_opc()
                    logging.info("Reconnected to OPC.")
                except Exception as e2:
                    logging.error(f"OPC reconnect failed: {e2}")
                    time.sleep(5)

    finally:
        try:
            opc.close()
        except Exception:
            pass
        try:
            client.close()
        except Exception:
            pass
        logging.info("Shutdown complete.")

if __name__ == "__main__":
    main()

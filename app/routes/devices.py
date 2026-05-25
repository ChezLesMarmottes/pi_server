from datetime import datetime, timezone
from fastapi import FastAPI, APIRouter
import sqlite3

from app.models import DeviceIn, DeviceOut
from app.main import app
from app.database import get_connection

devices_router = APIRouter()

@devices_router.post("/devices")
def post_devices(device_in: DeviceIn):
    connection, cursor = get_connection()

    #Log 1
    print(f"IN: {device_in}")

    record = {}

    record.update(device_in.model_dump())
    record["timestamp"] = datetime.now(timezone.utc).isoformat()

    columns = ", ".join(record.keys())
    placeholders = ", ".join(["?"] * len(record))
    values = tuple(record.values())

    query = f"INSERT INTO devices ({columns}) VALUES ({placeholders});"

    cursor.execute(query, values)
    connection.commit()

    #Log 2
    print(f"OUT: {record}")

    cursor.execute("SELECT * FROM devices WHERE id=?", (cursor.lastrowid,))

    result = {"status": "ok", "message": "device created", "id": cursor.lastrowid}

    connection.close()

    return result

@devices_router.get("/devices")
def get_devices(name: str | None = None, limit: int = 20):
    connection, cursor = get_connection()

    conditions = []
    values = []

    if name:
        conditions.append("name=?")
        values.append(name)
    
    query = "SELECT * FROM devices " 
    if conditions:
        query += "WHERE " + " AND ".join(conditions)
    query += " ORDER BY id DESC LIMIT ?"
    values.append(limit)

    cursor.execute(query, values)
    result = [DeviceOut(**row) for row in cursor.fetchall()]

    connection.close()

    return result

@devices_router.get("/devices/{name}")
def get_devices_name(name: str):
    connection, cursor = get_connection()

    cursor.execute("SELECT * FROM devices WHERE name=? ORDER BY id DESC LIMIT 1", (name,))

    result = {"status": "ok", "device": [DeviceOut(**row) for row in cursor.fetchall()]}

    connection.close()

    return result

@devices_router.post("/devices/{name}/state")
def post_devices_name_state(name: str, state: str):
    connection, cursor = get_connection()

    cursor.execute("SELECT * FROM devices WHERE name=? ORDER BY id DESC LIMIT 1", (name,))

    result = {"status": "ok", "message": "state updated", "device": [DeviceOut(**row) for row in cursor.fetchall()]}

    connection.close()

    return result
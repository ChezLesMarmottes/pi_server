from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException

from app.models import DeviceIn, DeviceOut
from app.database import connection_dependency

devices_router = APIRouter()

@devices_router.post("")
def post_devices(db: connection_dependency, device_in: DeviceIn):
    connection, cursor = db

    #Log 1
    print(f"IN: {device_in}")

    record: dict[str, str | int | float] = {}

    record.update(device_in.model_dump())
    record["timestamp"] = datetime.now(timezone.utc).isoformat()

    columns = ", ".join(record.keys())
    placeholders = ", ".join(["?"] * len(record))
    values = tuple(record.values())

    query = f"INSERT INTO devices ({columns}) VALUES ({placeholders});"

    cursor.execute(query, values)
    if cursor.rowcount == 0:
        raise HTTPException(404, detail="Device not found")
    
    connection.commit()

    #Log 2
    print(f"OUT: {record}")

    cursor.execute("SELECT * FROM devices WHERE id=?", (cursor.lastrowid,))
    if cursor.rowcount != -1:
        raise HTTPException(404, detail="Device not found")
    
    connection.commit()

    result: dict[str, str | int | None] = {"status": "ok", "message": "device created", "id": cursor.lastrowid}

    return result

@devices_router.get("")
def get_devices(db: connection_dependency, name: str | None = None, limit: int = 20):
    connection, cursor = db

    if limit >= 100:
        raise HTTPException(400, detail="Limit must be under 100")

    conditions: list[str] = []
    values: list[str | int] = []

    if name:
        conditions.append("name=?")
        values.append(name)
    
    query = "SELECT * FROM devices " 
    if conditions:
        query += "WHERE " + " AND ".join(conditions)
    query += " ORDER BY id DESC LIMIT ?"
    values.append(limit)

    cursor.execute(query, values)
    if cursor.rowcount != -1:
        raise HTTPException(404, detail="Device not found")
    
    connection.commit()
    
    result: dict[str, str | list[DeviceOut]] = {"status": "ok", "data": [DeviceOut(**row) for row in cursor.fetchall()]}

    return result

@devices_router.get("/{name}")
def get_devices_name(db: connection_dependency, name: str):
    connection, cursor = db

    cursor.execute("SELECT * FROM devices WHERE name=? ORDER BY id DESC LIMIT 1", (name,))
    if cursor.rowcount != -1:
        raise HTTPException(404, detail="Device not found")
    
    connection.commit()

    result: dict[str, str | DeviceOut] = {"status": "ok", "device": DeviceOut(**cursor.fetchone())}

    return result

@devices_router.post("/{name}/state")
def post_devices_name_state(db: connection_dependency, name: str, state: str):
    connection, cursor = db

    state = state.upper()

    if state not in ("ON", "OFF", "ARMED", "READING", "READY"):
        raise HTTPException(400, detail="State not in allowed states")

    cursor.execute("UPDATE devices SET state=? WHERE name=?", (state, name))
    if cursor.rowcount == 0:
        raise HTTPException(404, detail="Device not found")
    
    connection.commit()
    
    cursor.execute("SELECT * FROM devices WHERE name=?", (name,))
    if cursor.rowcount != -1:
        raise HTTPException(404, detail="Device not found")
    
    connection.commit()

    result: dict[str, str | DeviceOut] = {"status": "ok", "message": "state updated", "device": DeviceOut(**cursor.fetchone())}

    return result
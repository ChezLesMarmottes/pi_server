from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException

from app.models import ApiResponse, DeviceIn, DeviceOut, DeviceState, CreateData
from app.database import connection_dependency

devices_router = APIRouter()

@devices_router.post("", response_model=ApiResponse[CreateData])
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
    if cursor.lastrowid is None:
        raise HTTPException(500, detail="Insert failed")
    
    connection.commit()

    #Log 2
    print(f"OUT: {record}")

    result = {"message": "device created", "data": {"id": cursor.lastrowid}}

    return result

@devices_router.get("", response_model=ApiResponse[list[DeviceOut]])
def get_devices(db: connection_dependency, name: str | None = None, limit: int = 20):
    _, cursor = db

    if not (1 <= limit < 100):
        raise HTTPException(400, detail="Limit must be between 1 and 99")

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

    result = {"data": [DeviceOut(**row) for row in cursor.fetchall()]}

    return result

@devices_router.get("/{name}", response_model=ApiResponse[DeviceOut])
def get_devices_name(db: connection_dependency, name: str):
    _, cursor = db

    cursor.execute("SELECT * FROM devices WHERE name=? ORDER BY id DESC LIMIT 1", (name,))

    row = cursor.fetchone()
    if not row:
        raise HTTPException(404, detail="Device not found")

    result = {"data": DeviceOut(**row)}

    return result

@devices_router.post("/{name}/state", response_model=ApiResponse[DeviceOut])
def post_devices_name_state(db: connection_dependency, name: str, state: str):
    connection, cursor = db

    try:
        state = DeviceState(state.upper())
    except ValueError:
        raise HTTPException(400, detail="Invalid state")

    cursor.execute("UPDATE devices SET state=? WHERE name=? RETURNING *", (state, name))

    row = cursor.fetchone()
    if not row:
        raise HTTPException(404, detail="Device not found")
    
    connection.commit()

    result = {"message": "state updated", "data": DeviceOut(**row)}

    return result
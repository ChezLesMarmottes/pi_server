from fastapi import APIRouter, HTTPException

from app.models import ApiResponse, DeviceIn, DeviceOut, DeviceState, CreateData
from app.database import connection_dependency
from app.crud import build_filters, build_record, fetch_all, insert_record

devices_router = APIRouter()

@devices_router.post("", response_model=ApiResponse[CreateData])
def post_devices(db: connection_dependency, device_in: DeviceIn):
    connection, cursor = db

    record = build_record(device_in)

    device_id = insert_record(cursor, "devices", record)
    connection.commit()

    result = {"message": "device created", "data": {"id": device_id}}

    return result

@devices_router.get("", response_model=ApiResponse[list[DeviceOut]])
def get_devices(db: connection_dependency, name: str | None = None, limit: int = 20):
    _, cursor = db

    if not (1 <= limit < 100):
        raise HTTPException(400, detail="Limit must be between 1 and 99")

    conditions_sql, values = build_filters(name=name)
    
    query = "SELECT * FROM devices " 
    if conditions_sql:
        query += conditions_sql
    query += " ORDER BY id DESC LIMIT ?"
    values.append(limit)

    device_list = fetch_all(cursor, query, tuple(values), DeviceOut)

    result = {"data": device_list}

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
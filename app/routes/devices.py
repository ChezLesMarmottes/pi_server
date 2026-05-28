from datetime import datetime, timezone
import logging
from fastapi import APIRouter, HTTPException

from app.models import ApiResponse, DeviceIn, DeviceOut, DeviceState, CreateData, Database
from app.database import connection_dependency

devices_router = APIRouter()

logger = logging.getLogger(__name__)

@devices_router.post("", response_model=ApiResponse[CreateData])
def post_devices(db: connection_dependency, device_in: DeviceIn):

    record: dict[str, str | int | float] = {}

    record.update(device_in.model_dump())
    record["timestamp"] = datetime.now(timezone.utc).isoformat()

    columns = ", ".join(record.keys())
    placeholders = ", ".join(["?"] * len(record))
    values = tuple(record.values())

    query = f"INSERT INTO devices ({columns}) VALUES ({placeholders});"

    try:
        cursor = db.execute(query, tuple(values))
    except Exception:
        logger.exception("Failed query: Couldn't insert record into table")
        raise
    row_id = cursor.lastrowid

    if row_id is None:
        raise RuntimeError("Insert failed")
    
    db.commit()

    result = {"message": "device created", "data": {"id": row_id}}

    return result

@devices_router.get("", response_model=ApiResponse[list[DeviceOut]])
def get_devices(db: connection_dependency, name: str | None = None, limit: int = 20):

    if not (1 <= limit < 100):
        raise HTTPException(400, detail="Limit must be between 1 and 99")

    conditions: list[str] = []
    values: list[str | int] = []

    if name is not None:
        conditions.append("name=?")
        values.append(name)
    
    if conditions:
        conditions_sql = "WHERE " + " AND ".join(conditions)
    else:
        conditions_sql = ""
    
    query = "SELECT * FROM devices " 
    if conditions_sql:
        query += conditions_sql
    query += " ORDER BY id DESC LIMIT ?"
    values.append(limit)

    try:
        rows = db.fetch_all(query, tuple(values))
    except Exception:
        logger.exception("Failed query: Couldn't fetch all values from table")
        raise
    
    result = {"data": [DeviceOut(**row) for row in rows]}

    return result

@devices_router.get("/{name}", response_model=ApiResponse[DeviceOut])
def get_devices_name(db: connection_dependency, name: str):

    try:
        row = db.fetch_one("SELECT * FROM devices WHERE name=? ORDER BY id DESC LIMIT 1", (name,))
    except Exception:
        logger.exception("Failed query: Couldn't select %s from table devices", name)
        raise

    if not row:
        raise HTTPException(404, detail="Device not found")

    result = {"data": DeviceOut(**row)}

    return result

@devices_router.post("/{name}/state", response_model=ApiResponse[DeviceOut])
def post_devices_name_state(db: connection_dependency, name: str, state: str):

    try:
        state = DeviceState(state.upper())
    except ValueError:
        raise HTTPException(400, detail="Invalid state")

    try:
        row = db.fetch_one("UPDATE devices SET state=? WHERE name=? RETURNING *", (state, name))
    except Exception:
        logger.exception("Failed query: Couldn't update state of %s", name)
        raise

    if not row:
        raise HTTPException(404, detail="Device not found")
    
    db.commit()

    result = {"message": "state updated", "data": DeviceOut(**row)}

    return result
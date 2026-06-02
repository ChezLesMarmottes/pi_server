from datetime import datetime, timezone
import logging
import sqlite3
from typing import Any

from fastapi import APIRouter, HTTPException

from app.get_db import connection_dependency
from app.schemas import ApiResponse, CreateData, DeviceIn, DeviceOut, DeviceStateIn

devices_router: APIRouter = APIRouter()

logger: logging.Logger = logging.getLogger(__name__)

@devices_router.post("", response_model=ApiResponse[CreateData])
def post_devices(db: connection_dependency, device_in: DeviceIn) -> dict[str, str | dict[str, int]]:

    record: dict[str, str | int | float] = {}

    record.update(device_in.model_dump(mode="json"))
    record["timestamp"] = datetime.now(timezone.utc).isoformat()

    columns: str = ", ".join(record.keys())
    placeholders: str = ", ".join(["?"] * len(record))
    values: tuple[str | int | float, ...] = tuple(record.values())

    query: str = f"INSERT INTO devices ({columns}) VALUES ({placeholders});"

    try:
        cursor: sqlite3.Cursor = db.execute(query, values)
    except sqlite3.IntegrityError:
        logger.info("Device with this name already exists")
        raise HTTPException(400, detail="Device already exists")
    except Exception:
        logger.exception("Failed query: Couldn't insert record into table")
        raise
    row_id: int | None = cursor.lastrowid

    if row_id is None:
        raise RuntimeError("Insert failed")
    
    db.commit()

    result: dict[str, str | dict[str, int]] = {"status": "ok", "message": "device created", "data": {"id": row_id}}

    return result

@devices_router.get("", response_model=ApiResponse[list[DeviceOut]])
def get_devices(db: connection_dependency, name: str | None = None, limit: int = 20) -> dict[str, str | list[DeviceOut]]:

    conditions: list[str] = []
    values: list[str | int] = []

    if not (1 <= limit < 100):
        raise HTTPException(400, detail="Limit must be between 1 and 99")

    if name is not None:
        conditions.append("name=?")
        values.append(name)
    
    conditions_sql: str = "WHERE " + " AND ".join(conditions) if conditions else ""
    
    query: str = "SELECT * FROM devices "
    if conditions_sql:
        query += conditions_sql
    query += " ORDER BY id DESC LIMIT ?"
    values.append(limit)

    try:
        rows: list[dict[str, Any]] = db.fetch_all(query, tuple(values))
    except Exception:
        logger.exception("Failed query: Couldn't fetch all values from table")
        raise
    
    result: dict[str, str | list[DeviceOut]] = {"status": "ok", "message": "got devices", "data": [DeviceOut(**row) for row in rows]}

    return result

@devices_router.get("/{name}", response_model=ApiResponse[DeviceOut])
def get_devices_name(db: connection_dependency, name: str) -> dict[str, str | DeviceOut]:

    try:
        row: dict[str, Any] | None = db.fetch_one(
            "SELECT * FROM devices WHERE name=?",
            (name,)
        )
    except Exception:
        logger.exception("Failed query: Couldn't select %s from table devices", name)
        raise

    if not row:
        raise HTTPException(404, detail="Device not found")

    result: dict[str, str | DeviceOut] = {"status": "ok", "message": f"got device {name}", "data": DeviceOut(**row)}

    return result

@devices_router.post("/{name}/state", response_model=ApiResponse[DeviceOut])
def post_devices_name_state(db: connection_dependency, name: str, state_in: DeviceStateIn) -> dict[str, str | DeviceOut]:

    try:
        row: dict[str, Any] | None = db.fetch_one(
            "UPDATE devices SET state=? WHERE name=? RETURNING *",
            (state_in.state.value, name)
        )
    except Exception:
        logger.exception("Failed query: Couldn't update state of %s", name)
        raise

    if not row:
        raise HTTPException(404, detail="Device not found")
    
    db.commit()

    result: dict[str, str | DeviceOut] = {"status": "ok", "message": "state updated", "data": DeviceOut(**row)}

    return result
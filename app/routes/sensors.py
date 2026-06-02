import logging
import sqlite3
from typing import Any

from fastapi import APIRouter, HTTPException

from app.crud_helpers import get_record_by_name, get_records, insert_record, prepare_record_for_insert
from app.get_db import connection_dependency
from app.schemas import ApiResponse, CreateData, SensorIn, SensorOut, SensorStateIn

sensors_router: APIRouter = APIRouter()

logger: logging.Logger = logging.getLogger(__name__)

@sensors_router.post("", response_model=ApiResponse[CreateData])
def post_sensors(db: connection_dependency, sensor_in: SensorIn) -> dict[str, str | dict[str, int]]:

    record: dict[str, str | int | float] = prepare_record_for_insert(sensor_in.model_dump(mode="json"))

    try:
        row_id: int = insert_record(db, "sensors", record)
    except sqlite3.IntegrityError:
        logger.info("Sensor with this name already exists")
        raise HTTPException(400, detail="Sensor already exists")
    except Exception:
        logger.exception("Failed query: Couldn't insert record into table")
        raise

    result: dict[str, str | dict[str, int]] = {"status": "ok", "message": "sensor created", "data": {"id": row_id}}

    return result

@sensors_router.get("", response_model=ApiResponse[list[SensorOut]])
def get_sensors(db: connection_dependency, name: str | None = None, limit: int = 20) -> dict[str, str | list[SensorOut]]:

    if not (1 <= limit < 100):
        raise HTTPException(400, detail="Limit must be between 1 and 99")

    try:
        rows: list[dict[str, Any]] = get_records(db, "sensors", name_filter=name, limit=limit)
    except Exception:
        logger.exception("Failed query: Couldn't fetch all values from table")
        raise
    
    result: dict[str, str | list[SensorOut]] = {"status": "ok", "message": "got sensors", "data": [SensorOut(**row) for row in rows]}

    return result

@sensors_router.get("/{name}", response_model=ApiResponse[SensorOut])
def get_sensors_name(db: connection_dependency, name: str) -> dict[str, str | SensorOut]:

    try:
        row: dict[str, Any] | None = get_record_by_name(db, "sensors", name)
    except Exception:
        logger.exception("Failed query: Couldn't select %s from table sensors", name)
        raise

    if not row:
        raise HTTPException(404, detail="Sensor not found")

    result: dict[str, str | SensorOut] = {"status": "ok", "message": f"got sensor {name}", "data": SensorOut(**row)}

    return result

@sensors_router.post("/{name}/state", response_model=ApiResponse[SensorOut])
def post_sensors_name_state(db: connection_dependency, name: str, state_in: SensorStateIn) -> dict[str, str | SensorOut]:

    try:
        row: dict[str, Any] | None = db.fetch_one(
            "UPDATE sensors SET state=? WHERE name=? RETURNING *",
            (state_in.state.value, name)
        )
    except Exception:
        logger.exception("Failed query: Couldn't update state of %s", name)
        raise

    if not row:
        raise HTTPException(404, detail="Sensor not found")
    
    db.commit()

    result: dict[str, str | SensorOut] = {"status": "ok", "message": "state updated", "data": SensorOut(**row)}

    return result
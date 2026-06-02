import logging
import sqlite3
from typing import Any

from fastapi import APIRouter, HTTPException

from app.crud_helpers import get_records, insert_record, prepare_record_for_insert
from app.get_db import connection_dependency
from app.schemas import ApiResponse, CreateData, HardwareConfigIn, HardwareConfigOut

hardware_router: APIRouter = APIRouter()

logger: logging.Logger = logging.getLogger(__name__)


@hardware_router.post("", response_model=ApiResponse[CreateData])
def post_hardware_config(db: connection_dependency, config_in: HardwareConfigIn) -> dict[str, str | dict[str, int]]:

    record: dict[str, Any] = prepare_record_for_insert(config_in.model_dump(mode="json"))

    try:
        row_id: int = insert_record(db, "hardware_config", record)
    except sqlite3.IntegrityError:
        logger.info("Hardware config for this sensor already exists")
        raise HTTPException(400, detail="Hardware config for this sensor already exists")
    except Exception:
        logger.exception("Failed query: Couldn't insert hardware config")
        raise

    result: dict[str, str | dict[str, int]] = {"status": "ok", "message": "hardware config created", "data": {"id": row_id}}

    return result


@hardware_router.get("", response_model=ApiResponse[list[HardwareConfigOut]])
def get_hardware_config(db: connection_dependency, limit: int = 50) -> dict[str, str | list[HardwareConfigOut]]:

    if not (1 <= limit < 200):
        raise HTTPException(400, detail="Limit must be between 1 and 199")

    try:
        rows: list[dict[str, Any]] = db.fetch_all("SELECT * FROM hardware_config ORDER BY id DESC LIMIT ?", (limit,))
    except Exception:
        logger.exception("Failed query: Couldn't fetch hardware configs")
        raise

    result: dict[str, str | list[HardwareConfigOut]] = {
        "status": "ok",
        "message": "got hardware configs",
        "data": [HardwareConfigOut(**row) for row in rows]
    }

    return result


@hardware_router.get("/{sensor_id}", response_model=ApiResponse[HardwareConfigOut])
def get_hardware_config_by_sensor(db: connection_dependency, sensor_id: int) -> dict[str, str | HardwareConfigOut]:

    try:
        row: dict[str, Any] | None = db.fetch_one(
            "SELECT * FROM hardware_config WHERE sensor_id=?",
            (sensor_id,)
        )
    except Exception:
        logger.exception("Failed query: Couldn't fetch hardware config")
        raise

    if row is None:
        raise HTTPException(404, detail="Hardware config not found")

    result: dict[str, str | HardwareConfigOut] = {
        "status": "ok",
        "message": "got hardware config",
        "data": HardwareConfigOut(**row)
    }

    return result

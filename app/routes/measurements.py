from datetime import datetime, timezone
import logging
import sqlite3
from typing import Any

from fastapi import APIRouter, HTTPException

from app.database import connection_dependency
from app.models import ApiResponse, CreateData, MeasurementIn, MeasurementOut

measurements_router: APIRouter = APIRouter()

logger: logging.Logger = logging.getLogger(__name__)

@measurements_router.post("", response_model=ApiResponse[CreateData])
def post_measurements(db: connection_dependency, measurement_in: MeasurementIn) -> dict[str, str | dict[str, int]]:

    record: dict[str, str | int | float] = {}

    record.update(measurement_in.model_dump())
    record["timestamp"] = datetime.now(timezone.utc).isoformat()

    columns: str = ", ".join(record.keys())
    placeholders: str = ", ".join(["?"] * len(record))
    values: tuple[str | int | float, ...] = tuple(record.values())

    query: str = f"INSERT INTO measurements ({columns}) VALUES ({placeholders});"

    try:
        cursor: sqlite3.Cursor = db.execute(query, values)
    except Exception:
        logger.exception("Failed query: Couldn't insert record into table")
        raise
    row_id: int | None = cursor.lastrowid

    if row_id is None:
        raise RuntimeError("Insert failed")
    
    db.commit()

    result: dict[str, str | dict[str, int]] = {"message": "measurement stored", "data": {"id": row_id}}

    return result

@measurements_router.get("", response_model=ApiResponse[list[MeasurementOut]])
def get_measurements(db: connection_dependency, name: str | None = None, limit: int = 20) -> dict[str, list[MeasurementOut]]:

    conditions: list[str] = []
    values: list[str | int] = []

    if not (1 <= limit < 100):
        raise HTTPException(400, detail="Limit must be between 1 and 99")

    if name is not None:
        conditions.append("name=?")
        values.append(name)
    
    conditions_sql: str = "WHERE " + " AND ".join(conditions) if conditions else ""

    query: str = "SELECT * FROM measurements "
    if conditions_sql:
        query += conditions_sql
    query += " ORDER BY id DESC LIMIT ?"
    values.append(limit)

    try:
        rows: list[dict[str, Any]] = db.fetch_all(query, tuple(values))
    except Exception:
        logger.exception("Failed query: Couldn't fetch all values from table")
        raise
    
    result: dict[str, list[MeasurementOut]] = {"data": [MeasurementOut(**row) for row in rows]}

    return result

@measurements_router.get("/latest", response_model=ApiResponse[list[MeasurementOut]])
def get_measurements_latest(db: connection_dependency) -> dict[str, list[MeasurementOut]]:

    try:
        rows: list[dict[str, Any]] = db.fetch_all("SELECT * FROM measurements WHERE id IN (SELECT MAX(id) FROM measurements GROUP BY name) ORDER BY id DESC")
    except Exception:
        logger.exception("Failed query: Couldn't select latest from table measurements")
        raise

    result: dict[str, list[MeasurementOut]] = {"data": [MeasurementOut(**row) for row in rows]}

    return result

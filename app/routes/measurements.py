from datetime import datetime, timezone
import logging
from fastapi import APIRouter, HTTPException

from app.models import ApiResponse, MeasurementIn, MeasurementOut, CreateData
from app.database import connection_dependency

measurements_router = APIRouter()

logger = logging.getLogger(__name__)

@measurements_router.post("", response_model=ApiResponse[CreateData])
def post_measurements(db: connection_dependency, measurement_in: MeasurementIn):

    record: dict[str, str | int | float] = {}

    record.update(measurement_in.model_dump())
    record["timestamp"] = datetime.now(timezone.utc).isoformat()

    columns = ", ".join(record.keys())
    placeholders = ", ".join(["?"] * len(record))
    values = tuple(record.values())

    query = f"INSERT INTO measurements ({columns}) VALUES ({placeholders});"

    try:
        cursor = db.execute(query, tuple(values))
    except Exception:
        logger.exception("Failed query: Couldn't insert record into table")
        raise
    row_id = cursor.lastrowid

    if row_id is None:
        raise RuntimeError("Insert failed")
    
    db.commit()

    result = {"message": "measurement stored", "data": {"id": row_id}}

    return result

@measurements_router.get("", response_model=ApiResponse[list[MeasurementOut]])
def get_measurements(db: connection_dependency, name: str | None = None, limit: int = 20):

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

    
    query = "SELECT * FROM measurements " 
    if conditions_sql:
        query += conditions_sql
    query += " ORDER BY id DESC LIMIT ?"
    values.append(limit)

    try:
        rows = db.fetch_all(query, tuple(values))
    except Exception:
        logger.exception("Failed query: Couldn't fetch all values from table")
        raise
    
    result = {"data": [MeasurementOut(**row) for row in rows]}

    return result

@measurements_router.get("/latest", response_model=ApiResponse[list[MeasurementOut]])
def get_measurements_latest(db: connection_dependency):

    try:
        rows = db.fetch_all("SELECT * FROM measurements WHERE id IN (SELECT MAX(id) FROM measurements GROUP BY name) ORDER BY id DESC")
    except Exception:
        logger.exception("Failed query: Couldn't select latest from table measurements")
        raise

    result = {"data": [MeasurementOut(**row) for row in rows]}

    return result
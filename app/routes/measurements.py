import logging
from fastapi import APIRouter, HTTPException

from app.models import ApiResponse, MeasurementIn, MeasurementOut, CreateData
from app.database import connection_dependency
from app.crud import build_record, insert_record, fetch_all, build_filters

measurements_router = APIRouter()

logger = logging.getLogger(__name__)

@measurements_router.post("", response_model=ApiResponse[CreateData])
def post_measurements(db: connection_dependency, measurement_in: MeasurementIn):
    connection, cursor = db

    record = build_record(measurement_in)

    measurement_id = insert_record(cursor, "measurements", record)
    connection.commit()

    result = {"message": "measurement stored", "data": {"id": measurement_id}}

    return result

@measurements_router.get("", response_model=ApiResponse[list[MeasurementOut]])
def get_measurements(db: connection_dependency, name: str | None = None, limit: int = 20):
    _, cursor = db

    if not (1 <= limit < 100):
        raise HTTPException(400, detail="Limit must be between 1 and 99")

    conditions_sql, values = build_filters(name=name)
    
    query = "SELECT * FROM measurements " 
    if conditions_sql:
        query += conditions_sql
    query += " ORDER BY id DESC LIMIT ?"
    values.append(limit)

    measurement_list = fetch_all(cursor, query, tuple(values), MeasurementOut)
    
    result = {"data": measurement_list}

    return result

@measurements_router.get("/latest", response_model=ApiResponse[list[MeasurementOut]])
def get_measurements_latest(db: connection_dependency):
    _, cursor = db

    try:
        cursor.execute("SELECT * FROM measurements WHERE id IN (SELECT MAX(id) FROM measurements GROUP BY name) ORDER BY id DESC")
    except Exception:
        logger.exception("Failed query: Couldn't select latest from table measurements")
        raise

    result = {"data": [MeasurementOut(**row) for row in cursor.fetchall()]}

    return result
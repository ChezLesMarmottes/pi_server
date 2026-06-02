import logging
from typing import Any

from fastapi import APIRouter, HTTPException

from app.crud_helpers import get_record_by_name, get_records, insert_record, prepare_record_for_insert
from app.get_db import connection_dependency
from app.rule_engine import evaluate_rule, execute_rule_action
from app.schemas import ApiResponse, CreateData, MeasurementIn, MeasurementOut

measurements_router: APIRouter = APIRouter()

logger: logging.Logger = logging.getLogger(__name__)

@measurements_router.post("", response_model=ApiResponse[CreateData])
def post_measurements(db: connection_dependency, measurement_in: MeasurementIn) -> dict[str, str | dict[str, int]]:

    record: dict[str, str | int | float] = prepare_record_for_insert(measurement_in.model_dump(mode="json"))

    try:
        row_id: int = insert_record(db, "measurements", record)
    except Exception:
        logger.exception("Failed query: Couldn't insert record into table")
        raise

    # Real-time: evaluate against all enabled rules
    rules: list[dict[str, str | int | float]] = db.fetch_all("SELECT * FROM rules WHERE enabled=?", (True,))
    for rule in rules:
        if evaluate_rule(rule, record):
            execute_rule_action(db, rule)
            logger.info(f"Rule '{rule['name']}' triggered by current measurement")
    
    result: dict[str, str | dict[str, int]] = {"status": "ok", "message": "measurement stored", "data": {"id": row_id}}

    return result

@measurements_router.get("", response_model=ApiResponse[list[MeasurementOut]])
def get_measurements(db: connection_dependency, name: str | None = None, limit: int = 20) -> dict[str, str | list[MeasurementOut]]:

    if not (1 <= limit < 100):
        raise HTTPException(400, detail="Limit must be between 1 and 99")

    try:
        rows: list[dict[str, Any]] = get_records(db, "measurements", name_filter=name, limit=limit)
    except Exception:
        logger.exception("Failed query: Couldn't fetch all values from table")
        raise
    
    result: dict[str, str | list[MeasurementOut]] = {"status": "ok", "message": "got measurements", "data": [MeasurementOut(**row) for row in rows]}

    return result

@measurements_router.get("/latest", response_model=ApiResponse[list[MeasurementOut]])
def get_measurements_latest(db: connection_dependency) -> dict[str, str | list[MeasurementOut]]:

    try:
        rows: list[dict[str, Any]] = db.fetch_all("SELECT * FROM measurements WHERE id IN (SELECT MAX(id) FROM measurements GROUP BY name) ORDER BY id DESC")
    except Exception:
        logger.exception("Failed query: Couldn't select latest from table measurements")
        raise

    result: dict[str, str | list[MeasurementOut]] = {"status": "ok", "message": "got latest measurements", "data": [MeasurementOut(**row) for row in rows]}

    return result

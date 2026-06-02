import logging
import sqlite3
from typing import Any

from fastapi import APIRouter, HTTPException

from app.crud_helpers import get_record_by_name, get_records, insert_record, prepare_record_for_insert
from app.get_db import connection_dependency
from app.rule_engine import evaluate_rule_retroactively
from app.schemas import ApiResponse, CreateData, RuleIn, RuleOut, RuleEnabledIn

rules_router: APIRouter = APIRouter()

logger: logging.Logger = logging.getLogger(__name__)

@rules_router.post("", response_model=ApiResponse[CreateData])
def post_rules(db: connection_dependency, rule_in: RuleIn) -> dict[str, str | dict[str, int]]:

    record: dict[str, str | int | float] = prepare_record_for_insert(rule_in.model_dump(mode="json"))

    try:
        row_id: int = insert_record(db, "rules", record)
    except sqlite3.IntegrityError:
        logger.info("Rule with this name already exists")
        raise HTTPException(400, detail="Rule already exists")
    except Exception:
        logger.exception("Failed query: Couldn't insert record into table")
        raise

    # Retroactive: evaluate against all existing measurements
    if rule_in.enabled:
        fetched_rule = db.fetch_one("SELECT * FROM rules WHERE id=?", (row_id,))
        if not fetched_rule:
            logger.exception("Rule does not exist after creation")
            raise HTTPException(500, detail="Failed to create rule")
        count = evaluate_rule_retroactively(db, fetched_rule)
        logger.info(f"Rule '{rule_in.name}' would have triggered {count} times retroactively")

    result: dict[str, str | dict[str, int]] = {"status": "ok", "message": "rule created", "data": {"id": row_id}}

    return result

@rules_router.get("", response_model=ApiResponse[list[RuleOut]])
def get_rules(db: connection_dependency, name: str | None = None, limit: int = 20) -> dict[str, str | list[RuleOut]]:

    if not (1 <= limit < 100):
        raise HTTPException(400, detail="Limit must be between 1 and 99")

    try:
        rows: list[dict[str, Any]] = get_records(db, "rules", name_filter=name, limit=limit)
    except Exception:
        logger.exception("Failed query: Couldn't fetch all values from table")
        raise
    
    result: dict[str, str | list[RuleOut]] = {"status": "ok", "message": "got rules", "data": [RuleOut(**row) for row in rows]}

    return result

@rules_router.get("/{name}", response_model=ApiResponse[RuleOut])
def get_rules_name(db: connection_dependency, name: str) -> dict[str, str | RuleOut]:

    try:
        row: dict[str, Any] | None = get_record_by_name(db, "rules", name)
    except Exception:
        logger.exception("Failed query: Couldn't select %s from table rules", name)
        raise

    if not row:
        raise HTTPException(404, detail="Rule not found")

    result: dict[str, str | RuleOut] = {"status": "ok", "message": f"got rule {name}", "data": RuleOut(**row)}

    return result

@rules_router.post("/{name}/toggle", response_model=ApiResponse[RuleOut])
def post_name_toggle(db: connection_dependency, name: str, enabled: RuleEnabledIn) -> dict[str, str | RuleOut]:

    try:
        row: dict[str, Any] | None = db.fetch_one(
            "UPDATE rules SET enabled=? WHERE name=? RETURNING *",
            (enabled.enabled, name)
        )
    except Exception:
        logger.exception("Failed query: Couldn't update toggle for %s", name)
        raise

    if not row:
        raise HTTPException(404, detail="Rule not found")
    
    db.commit()

    # Retroactive: If toggling to enabled, evaluate against all existing measurements
    if enabled.enabled:
        count = evaluate_rule_retroactively(db, row)
        logger.info(f"Rule '{name}' retroactively fired {count} times after re-enabling")

    result: dict[str, str | RuleOut] = {"status": "ok", "message": "toggle updated", "data": RuleOut(**row)}

    return result

@rules_router.delete("/{name}", response_model=ApiResponse[None])
def delete_name(db: connection_dependency, name: str) -> dict[str, str | None]:

    try:
        cursor = db.execute("DELETE FROM rules WHERE name=?", (name,))
    except Exception:
        logger.exception("Failed query: Couldn't delete %s from table rules", name)
        raise

    if cursor.rowcount == 0:
        raise HTTPException(404, "Rule not found")
    
    db.commit()

    result: dict[str, str | None] = {"status": "ok", "message": f"rule {name} deleted", "data": None}

    return result
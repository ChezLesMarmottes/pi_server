from datetime import datetime, timezone
import logging
import sqlite3
from typing import Any

from fastapi import APIRouter, HTTPException

from app.get_db import connection_dependency
from app.schemas import ApiResponse, CreateData, RuleIn, RuleOut, RuleEnabledIn

rules_router: APIRouter = APIRouter()

logger: logging.Logger = logging.getLogger(__name__)

@rules_router.post("", response_model=ApiResponse[CreateData])
def post_rules(db: connection_dependency, rule_in: RuleIn) -> dict[str, str | dict[str, int]]:

    record: dict[str, str | int | float | datetime] = {}

    record.update(rule_in.model_dump(mode="json"))
    record["timestamp"] = datetime.now(timezone.utc).isoformat()

    columns: str = ", ".join(record.keys())
    placeholders: str = ", ".join(["?"] * len(record))
    values: tuple[str | int | float | datetime, ...] = tuple(record.values())

    query: str = f"INSERT INTO rules ({columns}) VALUES ({placeholders});"

    try:
        cursor: sqlite3.Cursor = db.execute(query, values)
    except sqlite3.IntegrityError:
        logger.info("Rule with this name already exists")
        raise HTTPException(400, detail="Rule already exists")
    except Exception:
        logger.exception("Failed query: Couldn't insert record into table")
        raise
    row_id: int | None = cursor.lastrowid

    if row_id is None:
        raise RuntimeError("Insert failed")
    
    db.commit()

    result: dict[str, str | dict[str, int]] = {"message": "rule created", "data": {"id": row_id}}

    return result

@rules_router.get("", response_model=ApiResponse[list[RuleOut]])
def get_rules(db: connection_dependency, name: str | None = None, limit: int = 20) -> dict[str, list[RuleOut]]:

    conditions: list[str] = []
    values: list[str | int] = []

    if not (1 <= limit < 100):
        raise HTTPException(400, detail="Limit must be between 1 and 99")

    if name is not None:
        conditions.append("name=?")
        values.append(name)
    
    conditions_sql: str = "WHERE " + " AND ".join(conditions) if conditions else ""
    
    query: str = "SELECT * FROM rules "
    if conditions_sql:
        query += conditions_sql
    query += " ORDER BY id DESC LIMIT ?"
    values.append(limit)

    try:
        rows: list[dict[str, Any]] = db.fetch_all(query, tuple(values))
    except Exception:
        logger.exception("Failed query: Couldn't fetch all values from table")
        raise
    
    result: dict[str, list[RuleOut]] = {"data": [RuleOut(**row) for row in rows]}

    return result

@rules_router.get("/{name}", response_model=ApiResponse[RuleOut])
def get_rules_name(db: connection_dependency, name: str) -> dict[str, RuleOut]:

    try:
        row: dict[str, Any] | None = db.fetch_one(
            "SELECT * FROM rules WHERE name=? ORDER BY id DESC LIMIT 1",
            (name,)
        )
    except Exception:
        logger.exception("Failed query: Couldn't select %s from table rules", name)
        raise

    if not row:
        raise HTTPException(404, detail="Rule not found")

    result = {"data": RuleOut(**row)}

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

    result: dict[str, str | RuleOut] = {"message": "toggle updated", "data": RuleOut(**row)}

    return result

@rules_router.delete("/{name}", response_model=ApiResponse[None])
def delete_name(db: connection_dependency, name: str) -> dict[str, str]:

    try:
        cursor = db.execute("DELETE FROM rules WHERE name=?", (name,))
    except Exception:
        logger.exception("Failed query: Couldn't select %s from table rules", name)
        raise

    if cursor.rowcount == 0:
        raise HTTPException(404, "Rule not found")
    
    db.commit()

    result = {"message": f"rule {name} deleted"}

    return result
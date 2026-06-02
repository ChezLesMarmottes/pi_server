from datetime import datetime, timezone
from typing import Any

from app.class_database import Database


def prepare_record_for_insert(model_data: dict[str, Any]) -> dict[str, Any]:

    record: dict[str, Any] = dict(model_data)
    record["timestamp"] = datetime.now(timezone.utc).isoformat()
    return record


def insert_record(db: Database, table: str, record: dict[str, Any]) -> int:

    columns: str = ", ".join(record.keys())
    placeholders: str = ", ".join(["?"] * len(record))
    values: tuple[Any, ...] = tuple(record.values())

    query: str = f"INSERT INTO {table} ({columns}) VALUES ({placeholders});"

    cursor = db.execute(query, values)
    row_id: int | None = cursor.lastrowid

    if row_id is None:
        raise RuntimeError("Insert failed")

    db.commit()
    return row_id


def get_records(db: Database, table: str, name_filter: str | None = None, limit: int = 20) -> list[dict[str, Any]]:

    conditions: list[str] = []
    values: list[str | int] = []

    if name_filter is not None:
        conditions.append("name=?")
        values.append(name_filter)

    conditions_sql: str = "WHERE " + " AND ".join(conditions) if conditions else ""

    query: str = f"SELECT * FROM {table} {conditions_sql} ORDER BY id DESC LIMIT ?"
    values.append(limit)

    rows: list[dict[str, Any]] = db.fetch_all(query, tuple(values))
    return rows


def get_record_by_name(db: Database, table: str, name: str) -> dict[str, Any] | None:

    row: dict[str, Any] | None = db.fetch_one(
        f"SELECT * FROM {table} WHERE name=?",
        (name,),
    )
    return row

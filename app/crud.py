from datetime import datetime, timezone
from typing import Type, TypeVar
from pydantic import BaseModel

def build_record(model: BaseModel) -> dict[str, str | int | float]:
    record: dict[str, str | int | float] = {}

    record.update(model.model_dump())
    record["timestamp"] = datetime.now(timezone.utc).isoformat()
    return record

def insert_record(cursor, table: str, record: dict[str, str | int | float]) -> int:
    columns = ", ".join(record.keys())
    placeholders = ", ".join(["?"] * len(record))
    values = tuple(record.values())

    query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders});"

    cursor.execute(query, values)
    row_id = cursor.lastrowid

    if row_id is None:
        raise RuntimeError("Insert failed")

    return row_id

T = TypeVar("T")
def fetch_all(cursor, query: str, values: tuple, model: Type[T]) -> list[T]:

    cursor.execute(query, values)
    
    return [model(**row) for row in cursor.fetchall()]

def build_filters(**kwargs):
    conditions: list[str] = []
    values: list[str | int] = []

    for key, value in kwargs.items():
        if value is not None:
            conditions.append(f"{key}=?")
            values.append(value)
    
    if conditions:
        conditions_sql = "WHERE " + " AND ".join(conditions)
    else:
        conditions_sql = ""

    return conditions_sql, values
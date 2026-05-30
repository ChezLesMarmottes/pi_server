import math
import os
import sqlite3
from enum import Enum

from pydantic import BaseModel, Field, field_validator
from typing import Any, Generic, Optional, TypeVar

class Database:
    connection: sqlite3.Connection

    def __init__(self, db_path: str = "data/platform.db") -> None:
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        self.connection = sqlite3.connect(db_path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.init_db()

    def init_db(self) -> None:
        cursor: sqlite3.Cursor = self.connection.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS measurements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT,
            name TEXT, 
            value REAL,
            unit TEXT,
            timestamp TEXT
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            state TEXT,
            timestamp TEXT
        );
        """)

        self.connection.commit()

    def execute(self, query: str, values: tuple[str | int | float, ...] | None = None) -> sqlite3.Cursor:
        cursor: sqlite3.Cursor = self.connection.cursor()
        if values is not None:
            cursor.execute(query, values)
        else:
            cursor.execute(query)
        return cursor

    def fetch_all(self, query: str, values: tuple[str | int | float, ...] | None = None) -> list[dict[Any, Any]]:
        cursor: sqlite3.Cursor = self.execute(query, values)
        return [dict(row) for row in cursor.fetchall()]

    def fetch_one(self, query: str, values: tuple[str | int | float, ...] | None = None) -> dict[Any, Any] | None:
        cursor: sqlite3.Cursor = self.execute(query, values)
        result: sqlite3.Row | None = cursor.fetchone()
        return dict(result) if result is not None else None
    
    def commit(self) -> None:
        self.connection.commit()

T = TypeVar("T")
class ApiResponse(BaseModel, Generic[T]):
    status: str = "ok"
    message: str | None = None
    data: T

class MeasurementIn(BaseModel):
    source: str = Field(min_length=1)
    name: str = Field(min_length=1)
    value: float
    unit: Optional[str] = None

    @field_validator("value")
    def check_finite(cls, v: int | float) -> int | float:
        if not math.isfinite(v):
            raise ValueError("value must be finite")
        return v
    
class MeasurementOut(BaseModel):
    id: int
    source: str
    name: str
    value: float
    unit: Optional[str] = None
    timestamp: str

class DeviceIn(BaseModel):
    name: str = Field(min_length=1)
    state: str = Field(min_length=1)

class DeviceOut(BaseModel):
    id: int
    name: str
    state: str
    timestamp: str

class DeviceStateIn(BaseModel):
    state: str = Field(min_length=1)

class CreateData(BaseModel):
    id: int

class DeviceState(str, Enum):
    ON = "ON"
    OFF = "OFF"
    ARMED = "ARMED"
    READING = "READING"
    READY = "READY"
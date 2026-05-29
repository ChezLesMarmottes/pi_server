import math
import sqlite3
from enum import Enum

from pydantic import BaseModel, Field, field_validator
from typing import Any, Generic, Optional, TypeVar

class Database:
    def __init__(self, db_path = "data/platform.db") -> None:
        self.connection = sqlite3.connect(db_path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row

    def execute(self, query: str, values: tuple | None = None) -> sqlite3.Cursor:
        cursor = self.connection.cursor()
        if values is not None:
            cursor.execute(query, values)
        else:
            cursor.execute(query)
        return cursor

    def fetch_all(self, query: str, values: tuple | None = None) -> list[dict[Any, Any]]:
        cursor = self.execute(query, values)
        return [dict(row) for row in cursor.fetchall()]

    def fetch_one(self, query: str, values: tuple | None = None) -> dict[Any, Any] | None:
        cursor = self.execute(query, values)
        result = cursor.fetchone()
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

class DeviceState(str, Enum):
    ON = "ON"
    OFF = "OFF"
    ARMED = "ARMED"
    READING = "READING"
    READY = "READY"

class CreateData(BaseModel):
    id: int
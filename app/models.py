from enum import Enum
from pydantic import BaseModel, Field, field_validator
from typing import Generic, Optional, TypeVar
import math

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
    def check_finite(cls, v):
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

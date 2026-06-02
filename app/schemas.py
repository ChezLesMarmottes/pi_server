from datetime import datetime
import math
from enum import Enum
from typing import Generic, TypeVar

from pydantic import BaseModel, Field, field_validator


T = TypeVar("T")
class ApiResponse(BaseModel, Generic[T]):
    status: str = "ok"
    message: str | None = None
    data: T | None = None


class CaseInsensitiveStrEnum(str, Enum):
    @classmethod
    def _missing_(cls, value: object) -> "CaseInsensitiveStrEnum | None":
        if isinstance(value, str):
            normalized = value.strip().lower()
            for member in cls:
                if member.value.lower() == normalized or member.name.lower() == normalized:
                    return member
        return None

    def __eq__(self, other: object) -> bool:
        if isinstance(other, str):
            return self.value.lower() == other.lower()
        if isinstance(other, Enum):
            return self.value.lower() == other.value.lower()
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.value.lower())


class DeviceState(CaseInsensitiveStrEnum):
    OFF = "OFF"
    ON = "ON"

class ConditionType(CaseInsensitiveStrEnum):
    MEASUREMENT_THRESHOLD = "measurement_threshold"

class ActionType(CaseInsensitiveStrEnum):
    SET_DEVICE_STATE = "set_device_state"

class ComparisonOperator(CaseInsensitiveStrEnum):
    GREATER = ">"
    LESS = "<"
    GREATER_EQUAL = ">="
    LESS_EQUAL = "<="
    EQUAL = "=="

class SensorState(str, Enum):
    INACTIVE = "INACTIVE"
    ACTIVE = "ACTIVE"

class SystemMode(str, Enum):
    DISARMED = "DISARMED"
    ARMED_AWAY = "ARMED_AWAY"
    ARMED_HOME = "ARMED_HOME"


class MeasurementIn(BaseModel):
    source: str = Field(min_length=1)
    name: str = Field(min_length=1)
    value: float
    unit: str | None = None

    @field_validator("value")
    def check_finite(cls, v: float) -> float:
        if not math.isfinite(v):
            raise ValueError("value must be finite")
        return v
    
class MeasurementOut(BaseModel):
    id: int
    source: str
    name: str
    value: float
    unit: str | None = None
    timestamp: datetime


class DeviceIn(BaseModel):
    name: str = Field(min_length=1)
    state: DeviceState

class DeviceOut(BaseModel):
    id: int
    name: str
    state: DeviceState
    timestamp: datetime

class DeviceStateIn(BaseModel):
    state: DeviceState


class RuleIn(BaseModel):
    name: str = Field(min_length=1)
    enabled: bool
    condition_type: ConditionType
    condition_measurement: str = Field(min_length=1)
    condition_operator: ComparisonOperator
    condition_value: float
    action_type: ActionType
    action_device: str = Field(min_length=1)
    action_state: DeviceState

class RuleOut(BaseModel):
    id: int
    name: str = Field(min_length=1)
    enabled: bool
    condition_type: ConditionType
    condition_measurement: str = Field(min_length=1)
    condition_operator: ComparisonOperator
    condition_value: float
    action_type: ActionType
    action_device: str = Field(min_length=1)
    action_state: DeviceState
    timestamp: datetime

class RuleEnabledIn(BaseModel):
    enabled: bool


class CreateData(BaseModel):
    id: int
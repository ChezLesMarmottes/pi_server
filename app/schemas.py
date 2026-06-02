from datetime import datetime
import math
from enum import Enum
from typing import Any, Generic, TypeVar

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

    def __eq__(self, other: object) -> Any:
        if isinstance(other, str):
            return self.value.lower() == other.lower()
        if isinstance(other, Enum):
            return self.value.lower() == other.value.lower()
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.value.lower())


class SensorState(CaseInsensitiveStrEnum):
    OFF = "OFF"
    ON = "ON"

class ConditionType(CaseInsensitiveStrEnum):
    MEASUREMENT_THRESHOLD = "measurement_threshold"

class ActionType(CaseInsensitiveStrEnum):
    SET_SENSOR_STATE = "set_sensor_state"

class CommandStatus(CaseInsensitiveStrEnum):
    PENDING = "pending"
    SENT = "sent"
    ACKNOWLEDGED = "acknowledged"
    FAILED = "failed"

class PinType(CaseInsensitiveStrEnum):
    DIGITAL = "digital"
    ANALOG = "analog"

class ComparisonOperator(CaseInsensitiveStrEnum):
    GREATER = ">"
    LESS = "<"
    GREATER_EQUAL = ">="
    LESS_EQUAL = "<="
    EQUAL = "=="

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


class SensorIn(BaseModel):
    name: str = Field(min_length=1)
    state: SensorState

class SensorOut(BaseModel):
    id: int
    name: str
    state: SensorState
    timestamp: datetime

class SensorStateIn(BaseModel):
    state: SensorState


class RuleIn(BaseModel):
    name: str = Field(min_length=1)
    enabled: bool
    condition_type: ConditionType
    condition_measurement: str = Field(min_length=1)
    condition_operator: ComparisonOperator
    condition_value: float
    action_type: ActionType
    action_sensor: str = Field(min_length=1)
    action_state: SensorState

class RuleOut(BaseModel):
    id: int
    name: str = Field(min_length=1)
    enabled: bool
    condition_type: ConditionType
    condition_measurement: str = Field(min_length=1)
    condition_operator: ComparisonOperator
    condition_value: float
    action_type: ActionType
    action_sensor: str = Field(min_length=1)
    action_state: SensorState
    timestamp: datetime

class RuleEnabledIn(BaseModel):
    enabled: bool


class CreateData(BaseModel):
    id: int


class HardwareConfigIn(BaseModel):
    sensor_id: int
    arduino_pin: str = Field(min_length=1)
    pin_type: PinType
    read_interval_ms: int = Field(gt=0)


class HardwareConfigOut(BaseModel):
    id: int
    sensor_id: int
    arduino_pin: str
    pin_type: PinType
    read_interval_ms: int
    timestamp: datetime


class CommandIn(BaseModel):
    sensor_id: int
    action: str = Field(min_length=1)


class CommandOut(BaseModel):
    id: int
    sensor_id: int
    action: str
    status: CommandStatus
    timestamp: datetime
    acknowledged_at: datetime | None = None
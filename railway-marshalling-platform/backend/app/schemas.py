"""Pydantic 请求/响应模式。"""
from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .models import LocoStatus, TrainType

T = TypeVar("T")


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------------- 货列 ----------------

class TrainBase(BaseModel):
    code: str = Field(..., max_length=32)
    train_type: TrainType = TrainType.freight_normal
    arrival_time: datetime
    departure_time: datetime

    length_m: float = Field(0, ge=0)
    weight_t: float = Field(0, ge=0)
    max_width_m: float = Field(3.2, ge=0)
    max_height_m: float = Field(4.5, ge=0)

    track_id: int | None = None
    locomotive_id: int | None = None
    sequence_no: int | None = None

    destination: str = ""
    note: str = ""

    @field_validator("departure_time")
    @classmethod
    def departure_after_arrival(cls, v, info):
        arrival = info.data.get("arrival_time")
        if arrival and v < arrival:
            raise ValueError("发车时间不能早于到达时间")
        return v


class TrainCreate(TrainBase):
    pass


class TrainUpdate(TrainBase):
    pass


class TrainOut(ORMModel):
    id: int
    code: str
    train_type: TrainType
    arrival_time: datetime
    departure_time: datetime
    length_m: float
    weight_t: float
    max_width_m: float
    max_height_m: float
    track_id: int | None
    locomotive_id: int | None
    sequence_no: int | None
    destination: str
    note: str


# ---------------- 股道 ----------------

class TrackBase(BaseModel):
    name: str = Field(..., max_length=32)
    track_kind: str = "classification"
    length_m: float = Field(0, ge=0)
    occupied_length_m: float = Field(0, ge=0)
    max_load_t: float = Field(0, ge=0)
    allow_dangerous: bool = False
    allow_overload: bool = False
    note: str = ""


class TrackCreate(TrackBase):
    pass


class TrackUpdate(TrackBase):
    pass


class TrackOut(ORMModel):
    id: int
    name: str
    track_kind: str
    length_m: float
    occupied_length_m: float
    max_load_t: float
    allow_dangerous: bool
    allow_overload: bool
    note: str


# ---------------- 机车 ----------------

class LocomotiveBase(BaseModel):
    name: str = Field(..., max_length=32)
    model: str = ""
    power_kw: float = Field(0, ge=0)
    status: LocoStatus = LocoStatus.available
    available_from: datetime | None = None
    available_to: datetime | None = None
    note: str = ""


class LocomotiveCreate(LocomotiveBase):
    pass


class LocomotiveUpdate(LocomotiveBase):
    pass


class LocomotiveOut(ORMModel):
    id: int
    name: str
    model: str
    power_kw: float
    status: LocoStatus
    available_from: datetime | None
    available_to: datetime | None
    note: str


# ---------------- 规则 ----------------

class RuleBase(BaseModel):
    key: str = Field(..., max_length=64)
    value: Any
    label: str = ""
    category: str = "general"
    description: str = ""


class RuleCreate(RuleBase):
    pass


class RuleUpdate(BaseModel):
    value: Any
    label: str | None = None
    category: str | None = None
    description: str | None = None


class RuleOut(ORMModel):
    id: int
    key: str
    value: Any
    value_type: str
    label: str
    category: str
    description: str


# ---------------- 冲突分析 ----------------

class Suggestion(BaseModel):
    action: str            # reassign_track / reassign_loco / reschedule / fix_sequence / manual_review
    description: str
    target_track_id: int | None = None
    target_locomotive_id: int | None = None
    new_arrival_time: datetime | None = None
    new_departure_time: datetime | None = None
    new_sequence_no: int | None = None


class Conflict(BaseModel):
    code: str
    severity: str          # high / medium / low
    title: str
    detail: str
    train_code: str | None = None
    track_name: str | None = None
    locomotive_name: str | None = None
    related_train_code: str | None = None
    suggestions: list[Suggestion] = Field(default_factory=list)


class TrackStat(BaseModel):
    track_id: int | None
    track_name: str
    trains: int
    used_length_m: float
    capacity_m: float
    utilization: float


class LocoStat(BaseModel):
    locomotive_id: int | None
    locomotive_name: str
    trains: int


class AnalysisResponse(BaseModel):
    generated_at: datetime
    train_count: int
    track_count: int
    locomotive_count: int
    conflicts: list[Conflict]
    summary: dict[str, int]
    timeline_start: datetime | None
    timeline_end: datetime | None
    track_stats: list[TrackStat]
    loco_stats: list[LocoStat]


class ListResponse(BaseModel, Generic[T]):
    total: int
    items: list[T]

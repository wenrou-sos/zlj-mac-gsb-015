"""Pydantic 请求/响应模型。"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ---------- 股道 ----------
class TrackBase(BaseModel):
    name: str = Field(..., examples=["3道"])
    length_m: float = Field(..., gt=0, examples=[900.0])
    track_type: str = "arrival_departure"
    status: str = "active"


class TrackCreate(TrackBase):
    pass


class TrackUpdate(BaseModel):
    name: str | None = None
    length_m: float | None = Field(default=None, gt=0)
    track_type: str | None = None
    status: str | None = None


class TrackOut(TrackBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


# ---------- 机车 ----------
class LocomotiveBase(BaseModel):
    loco_number: str = Field(..., examples=["HXD3-0001"])
    loco_type: str = "electric"
    max_traction_weight_t: float = Field(..., gt=0, examples=[6000.0])
    status: str = "available"
    available_from: datetime | None = None
    available_until: datetime | None = None


class LocomotiveCreate(LocomotiveBase):
    pass


class LocomotiveUpdate(BaseModel):
    loco_number: str | None = None
    loco_type: str | None = None
    max_traction_weight_t: float | None = Field(default=None, gt=0)
    status: str | None = None
    available_from: datetime | None = None
    available_until: datetime | None = None


class LocomotiveOut(LocomotiveBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


# ---------- 编组规则 ----------
class RuleBase(BaseModel):
    name: str = Field(..., examples=["标准编组规则"])
    max_wagons: int = Field(default=60, gt=0)
    max_length_m: float = Field(default=850.0, gt=0)
    max_weight_t: float = Field(default=5000.0, gt=0)
    min_departure_interval_min: int = Field(default=15, ge=0)
    max_dwell_time_min: int = Field(default=720, gt=0)
    is_active: bool = True


class RuleCreate(RuleBase):
    pass


class RuleUpdate(BaseModel):
    name: str | None = None
    max_wagons: int | None = Field(default=None, gt=0)
    max_length_m: float | None = Field(default=None, gt=0)
    max_weight_t: float | None = Field(default=None, gt=0)
    min_departure_interval_min: int | None = Field(default=None, ge=0)
    max_dwell_time_min: int | None = Field(default=None, gt=0)
    is_active: bool | None = None


class RuleOut(RuleBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


# ---------- 货列 ----------
class TrainBase(BaseModel):
    train_number: str = Field(..., examples=["X801"])
    arrival_time: datetime
    departure_time: datetime | None = None
    wagon_count: int = Field(default=0, ge=0)
    total_length_m: float = Field(default=0.0, ge=0)
    total_weight_t: float = Field(default=0.0, ge=0)
    cargo_type: str = "general"
    priority: int = Field(default=3, ge=1, le=5)
    status: str = "scheduled"
    track_id: int | None = None
    locomotive_id: int | None = None


class TrainCreate(TrainBase):
    pass


class TrainUpdate(BaseModel):
    train_number: str | None = None
    arrival_time: datetime | None = None
    departure_time: datetime | None = None
    wagon_count: int | None = Field(default=None, ge=0)
    total_length_m: float | None = Field(default=None, ge=0)
    total_weight_t: float | None = Field(default=None, ge=0)
    cargo_type: str | None = None
    priority: int | None = Field(default=None, ge=1, le=5)
    status: str | None = None
    track_id: int | None = None
    locomotive_id: int | None = None


class TrainOut(TrainBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


# ---------- 冲突分析 ----------
class ConflictOut(BaseModel):
    type: str            # track_occupation / sequence / over_limit / locomotive
    severity: str        # high / medium / low
    message: str
    train_ids: list[int]
    track_id: int | None = None
    suggestion: str


class AnalysisRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    train_count: int
    conflict_count: int
    results: list[ConflictOut]

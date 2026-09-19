"""SQLAlchemy 数据模型：股道、机车、编组规则、货列、分析记录。"""
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Track(Base):
    """股道（到发线 / 调车线 / 编组线）。"""

    __tablename__ = "tracks"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    length_m: Mapped[float] = mapped_column(Float, nullable=False)  # 有效长度（米）
    track_type: Mapped[str] = mapped_column(String(20), default="arrival_departure")
    status: Mapped[str] = mapped_column(String(20), default="active")  # active / maintenance

    trains: Mapped[list["Train"]] = relationship(back_populates="track")


class Locomotive(Base):
    """机车资源。"""

    __tablename__ = "locomotives"

    id: Mapped[int] = mapped_column(primary_key=True)
    loco_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    loco_type: Mapped[str] = mapped_column(String(20), default="electric")  # electric / diesel
    max_traction_weight_t: Mapped[float] = mapped_column(Float, nullable=False)  # 最大牵引重量（吨）
    status: Mapped[str] = mapped_column(String(20), default="available")  # available / maintenance
    available_from: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    available_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    trains: Mapped[list["Train"]] = relationship(back_populates="locomotive")


class MarshallingRule(Base):
    """编组规则。"""

    __tablename__ = "marshalling_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    max_wagons: Mapped[int] = mapped_column(Integer, default=60)          # 最大编组辆数
    max_length_m: Mapped[float] = mapped_column(Float, default=850.0)     # 最大列车长度（米）
    max_weight_t: Mapped[float] = mapped_column(Float, default=5000.0)    # 最大牵引总重（吨）
    min_departure_interval_min: Mapped[int] = mapped_column(Integer, default=15)  # 同股道最小出发间隔（分钟）
    max_dwell_time_min: Mapped[int] = mapped_column(Integer, default=720)         # 最大停留时间（分钟）
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Train(Base):
    """货运列车。"""

    __tablename__ = "trains"

    id: Mapped[int] = mapped_column(primary_key=True)
    train_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)  # 车次
    arrival_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    departure_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    wagon_count: Mapped[int] = mapped_column(Integer, default=0)       # 编组辆数
    total_length_m: Mapped[float] = mapped_column(Float, default=0.0)  # 列车总长度（米）
    total_weight_t: Mapped[float] = mapped_column(Float, default=0.0)  # 总重（吨）
    cargo_type: Mapped[str] = mapped_column(String(50), default="general")
    priority: Mapped[int] = mapped_column(Integer, default=3)  # 1 最高 - 5 最低
    status: Mapped[str] = mapped_column(String(20), default="scheduled")  # scheduled / arrived / departed

    track_id: Mapped[int | None] = mapped_column(ForeignKey("tracks.id"), nullable=True)
    locomotive_id: Mapped[int | None] = mapped_column(ForeignKey("locomotives.id"), nullable=True)

    track: Mapped[Track | None] = relationship(back_populates="trains")
    locomotive: Mapped[Locomotive | None] = relationship(back_populates="trains")


class AnalysisRun(Base):
    """一次冲突分析的运行记录与结果快照。"""

    __tablename__ = "analysis_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    train_count: Mapped[int] = mapped_column(Integer, default=0)
    conflict_count: Mapped[int] = mapped_column(Integer, default=0)
    results: Mapped[list] = mapped_column(JSON, default=list)

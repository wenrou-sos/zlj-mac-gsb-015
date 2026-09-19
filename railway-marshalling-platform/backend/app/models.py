"""SQLAlchemy 数据模型：货列、股道、机车、编组规则。"""
import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class TrainType(str, enum.Enum):
    freight_normal = "normal"        # 普通货物
    freight_dangerous = "dangerous"  # 危险品
    freight_overload = "overload"    # 超限/重载


class LocoStatus(str, enum.Enum):
    available = "available"
    maintenance = "maintenance"


class Train(Base):
    __tablename__ = "trains"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    train_type: Mapped[TrainType] = mapped_column(
        Enum(TrainType, values_callable=lambda x: [e.value for e in x]),
        default=TrainType.freight_normal,
    )
    arrival_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    departure_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # 车辆参数
    length_m: Mapped[float] = mapped_column(Float, default=0.0)
    weight_t: Mapped[float] = mapped_column(Float, default=0.0)
    max_width_m: Mapped[float] = mapped_column(Float, default=3.2)
    max_height_m: Mapped[float] = mapped_column(Float, default=4.5)

    # 编组安排
    track_id: Mapped[int | None] = mapped_column(
        ForeignKey("tracks.id", ondelete="SET NULL"), nullable=True
    )
    locomotive_id: Mapped[int | None] = mapped_column(
        ForeignKey("locomotives.id", ondelete="SET NULL"), nullable=True
    )
    sequence_no: Mapped[int | None] = mapped_column(Integer, nullable=True)

    destination: Mapped[str] = mapped_column(String(64), default="")
    note: Mapped[str] = mapped_column(Text, default="")

    track: Mapped["Track | None"] = relationship(back_populates="trains", lazy="joined")
    locomotive: Mapped["Locomotive | None"] = relationship(
        back_populates="trains", lazy="joined"
    )


class Track(Base):
    __tablename__ = "tracks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    track_kind: Mapped[str] = mapped_column(String(16), default="classification")
    length_m: Mapped[float] = mapped_column(Float, default=0.0)
    occupied_length_m: Mapped[float] = mapped_column(Float, default=0.0)  # 现存车辆占用
    max_load_t: Mapped[float] = mapped_column(Float, default=0.0)
    allow_dangerous: Mapped[bool] = mapped_column(Boolean, default=False)
    allow_overload: Mapped[bool] = mapped_column(Boolean, default=False)
    note: Mapped[str] = mapped_column(Text, default="")

    trains: Mapped[list["Train"]] = relationship(back_populates="track")


class Locomotive(Base):
    __tablename__ = "locomotives"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    model: Mapped[str] = mapped_column(String(32), default="")
    power_kw: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[LocoStatus] = mapped_column(
        Enum(LocoStatus, values_callable=lambda x: [e.value for e in x]),
        default=LocoStatus.available,
    )
    # 当班可用时间窗（空表示全天可用）
    available_from: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    available_to: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    note: Mapped[str] = mapped_column(Text, default="")

    trains: Mapped[list["Train"]] = relationship(back_populates="locomotive")


class Rule(Base):
    """可配置编组规则，value 以 JSON 文本存储，支持 number/boolean/string。"""

    __tablename__ = "rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    value: Mapped[str] = mapped_column(Text, default="")  # JSON 编码
    value_type: Mapped[str] = mapped_column(String(16), default="number")
    label: Mapped[str] = mapped_column(String(128), default="")
    category: Mapped[str] = mapped_column(String(32), default="general")
    description: Mapped[str] = mapped_column(Text, default="")

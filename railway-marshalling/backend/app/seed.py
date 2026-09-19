"""示例数据：首次启动时写入，便于演示冲突检测效果。"""
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from . import models


def seed_if_empty(db: Session) -> None:
    if db.query(models.Track).count() > 0:
        return

    base = datetime.now().replace(hour=6, minute=0, second=0, microsecond=0)

    tracks = [
        models.Track(name="1道", length_m=1050.0, track_type="arrival_departure"),
        models.Track(name="2道", length_m=900.0, track_type="arrival_departure"),
        models.Track(name="3道", length_m=750.0, track_type="arrival_departure"),
        models.Track(name="调车线A", length_m=600.0, track_type="classification"),
    ]
    locos = [
        models.Locomotive(loco_number="HXD3-0001", loco_type="electric", max_traction_weight_t=6000.0),
        models.Locomotive(loco_number="HXD3-0002", loco_type="electric", max_traction_weight_t=6000.0),
        models.Locomotive(loco_number="DF8B-0112", loco_type="diesel", max_traction_weight_t=4000.0),
    ]
    rules = [
        models.MarshallingRule(
            name="标准编组规则",
            max_wagons=60,
            max_length_m=850.0,
            max_weight_t=5000.0,
            min_departure_interval_min=15,
            max_dwell_time_min=720,
        )
    ]
    db.add_all(tracks + locos + rules)
    db.flush()

    h = timedelta(hours=1)
    trains = [
        # 正常列车
        models.Train(
            train_number="X801", arrival_time=base, departure_time=base + 3 * h,
            wagon_count=45, total_length_m=620.0, total_weight_t=3600.0,
            cargo_type="集装箱", track_id=tracks[0].id, locomotive_id=locos[0].id,
        ),
        # 与 X801 在 1 道时间重叠 -> 股道占用冲突
        models.Train(
            train_number="X803", arrival_time=base + 2 * h, departure_time=base + 5 * h,
            wagon_count=40, total_length_m=560.0, total_weight_t=3200.0,
            cargo_type="煤炭", track_id=tracks[0].id, locomotive_id=locos[1].id,
        ),
        # 超长列车放在 3 道 -> 超限风险
        models.Train(
            train_number="X805", arrival_time=base + 1 * h, departure_time=base + 4 * h,
            wagon_count=58, total_length_m=820.0, total_weight_t=4500.0,
            cargo_type="钢材", track_id=tracks[2].id, locomotive_id=locos[2].id,
        ),
        # 超重列车配小马力机车 -> 机车冲突；且与 X807 顺序颠倒 -> 顺序冲突
        models.Train(
            train_number="X809", arrival_time=base + 2 * h, departure_time=base + 6 * h,
            wagon_count=50, total_length_m=700.0, total_weight_t=5200.0,
            cargo_type="矿石", track_id=tracks[1].id, locomotive_id=locos[2].id,
        ),
        models.Train(
            train_number="X807", arrival_time=base + 3 * h, departure_time=base + 5 * h + timedelta(minutes=30),
            wagon_count=42, total_length_m=580.0, total_weight_t=3400.0,
            cargo_type="粮食", track_id=tracks[1].id, locomotive_id=locos[0].id,
        ),
    ]
    db.add_all(trains)
    db.commit()

"""初始化演示数据：股道、机车、货列（含若干预置冲突）。"""
from datetime import datetime

from sqlalchemy.orm import Session

from .models import LocoStatus, Locomotive, Track, Train, TrainType


def seed_data(db: Session) -> bool:
    """库为空时写入演示数据，返回是否执行了初始化。"""
    if db.query(Train).count() > 0 or db.query(Track).count() > 0:
        return False

    tracks = [
        Track(name="G1", track_kind="classification", length_m=850,
              occupied_length_m=120, max_load_t=4000,
              allow_dangerous=False, allow_overload=False,
              note="主编组线，普通货物"),
        Track(name="G2", track_kind="classification", length_m=1050,
              occupied_length_m=0, max_load_t=5000,
              allow_dangerous=False, allow_overload=True,
              note="重载/超限列车指定线"),
        Track(name="G3", track_kind="storage", length_m=700,
              occupied_length_m=200, max_load_t=3000,
              allow_dangerous=True, allow_overload=False,
              note="危险品停留线，端头式"),
        Track(name="G4", track_kind="departure", length_m=600,
              occupied_length_m=0, max_load_t=3500,
              allow_dangerous=False, allow_overload=False,
              note="出发线"),
    ]
    db.add_all(tracks)
    db.flush()
    g1, g2, g3, g4 = tracks

    locos = [
        Locomotive(name="DF7-001", model="DF7C 调车机", power_kw=1470,
                   status=LocoStatus.available,
                   note="一班，主担当 G1/G2 编组"),
        Locomotive(name="DF7-002", model="DF7C 调车机", power_kw=1470,
                   status=LocoStatus.available,
                   available_from=datetime(2026, 9, 18, 8, 0),
                   available_to=datetime(2026, 9, 18, 20, 0),
                   note="二班，8:00–20:00"),
        Locomotive(name="HXN5-003", model="HXN5 内燃机车", power_kw=4660,
                   status=LocoStatus.maintenance,
                   note="计划检修中，暂不可用"),
    ]
    db.add_all(locos)
    db.flush()
    l1, l2, l3 = locos

    def dt(h, m=0):
        return datetime(2026, 9, 18, h, m)

    trains = [
        # 正常：G1，08:00-09:30
        Train(code="X85001", train_type=TrainType.freight_normal,
              arrival_time=dt(8, 0), departure_time=dt(9, 30),
              length_m=620, weight_t=2800, max_width_m=3.2, max_height_m=4.4,
              track_id=g1.id, locomotive_id=l1.id, sequence_no=1,
              destination="郑州北", note="集装箱班列"),
        # 与 X85001 同股道时间重叠 -> C01 股道占用冲突
        Train(code="X85002", train_type=TrainType.freight_normal,
              arrival_time=dt(9, 0), departure_time=dt(10, 30),
              length_m=580, weight_t=2600, max_width_m=3.1, max_height_m=4.3,
              track_id=g1.id, locomotive_id=l2.id, sequence_no=2,
              destination="徐州北"),
        # 同机车 DF7-001 时间重叠 -> C08 机车时间冲突
        Train(code="X85003", train_type=TrainType.freight_normal,
              arrival_time=dt(8, 30), departure_time=dt(10, 0),
              length_m=540, weight_t=2400, max_width_m=3.2, max_height_m=4.4,
              track_id=g4.id, locomotive_id=l1.id, sequence_no=1,
              destination="丰台西"),
        # 超长：G4 有效 600m，本列 680m -> C02；且顺序倒置（序号3先到达）-> C07
        Train(code="X85004", train_type=TrainType.freight_normal,
              arrival_time=dt(11, 0), departure_time=dt(12, 30),
              length_m=680, weight_t=3100, max_width_m=3.3, max_height_m=4.5,
              track_id=g4.id, locomotive_id=l2.id, sequence_no=3,
              destination="南仓"),
        # G4 上后到但序号小 -> 与 X85004 构成 C07 顺序冲突；间隔也较紧
        Train(code="X85005", train_type=TrainType.freight_normal,
              arrival_time=dt(13, 0), departure_time=dt(14, 0),
              length_m=400, weight_t=1800, max_width_m=3.0, max_height_m=4.2,
              track_id=g4.id, locomotive_id=l2.id, sequence_no=1,
              destination="石家庄"),
        # 危险品进 G3 -> 合规；但被派给检修机车 -> C11
        Train(code="X85006", train_type=TrainType.freight_dangerous,
              arrival_time=dt(10, 0), departure_time=dt(11, 30),
              length_m=460, weight_t=2100, max_width_m=3.1, max_height_m=4.2,
              track_id=g3.id, locomotive_id=l3.id, sequence_no=1,
              destination="颖上", note="液化石油气罐车"),
        # 重载+超限，进 G1（不允许重载、尺寸超限）-> C04 + C05
        Train(code="X85007", train_type=TrainType.freight_overload,
              arrival_time=dt(15, 0), departure_time=dt(17, 0),
              length_m=720, weight_t=5200, max_width_m=3.8, max_height_m=5.1,
              track_id=g1.id, locomotive_id=l2.id, sequence_no=1,
              destination="宝鸡东", note="大型变压器，超限等级二级"),
        # 未分配股道与机车 -> C10
        Train(code="X85008", train_type=TrainType.freight_normal,
              arrival_time=dt(16, 30), departure_time=dt(18, 0),
              length_m=500, weight_t=2200, max_width_m=3.2, max_height_m=4.4,
              destination="武汉北", note="计划待调度"),
    ]
    db.add_all(trains)
    db.commit()
    return True

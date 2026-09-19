"""冲突检测引擎测试：验证预置数据与规则调整后的检测结果。"""
from datetime import datetime

from app.database import SessionLocal
from app.detector import analyze
from app.models import LocoStatus, Locomotive, Track, Train, TrainType


def _codes(result):
    return [c["code"] for c in result["conflicts"]]


def _find(result, code, train_code=None):
    for c in result["conflicts"]:
        if c["code"] == code and (train_code is None or c["train_code"] == train_code):
            return c
    return None


def test_seed_conflicts_detected(db):
    session = SessionLocal()
    result = analyze(session)
    codes = _codes(result)

    # X85001 vs X85002 同股道时间重叠
    assert _find(result, "C01", "X85001") is not None
    # X85004 长度 680 > G4 有效 600
    assert _find(result, "C02", "X85004") is not None
    # X85004 重量 3100t > G4 载重 3500? 3100<3500 不触发；X85007 5200t 触发 C03
    assert _find(result, "C03", "X85007") is not None
    # X85007 重载进 G1
    assert _find(result, "C04", "X85007") is not None
    # X85007 超限尺寸
    assert _find(result, "C05", "X85007") is not None
    # X85004/X85005 编组顺序与到达顺序矛盾
    assert _find(result, "C07", "X85004") is not None
    # DF7-001 同时给 X85001、X85003
    assert _find(result, "C08", "X85001") is not None
    # X85006 被派给检修机车
    assert _find(result, "C11", "X85006") is not None
    # X85008 未分配
    assert _find(result, "C10", "X85008") is not None

    assert result["summary"]["total"] == len(result["conflicts"])
    assert result["summary"]["high"] >= 4
    session.close()


def test_suggestions_present(db):
    session = SessionLocal()
    result = analyze(session)
    for c in result["conflicts"]:
        # 每条冲突都至少给出一条建议
        assert c["suggestions"], f"{c['code']}/{c['train_code']} 缺少建议"
    # C01 提供改时间建议；C02 提供改派股道建议
    c01 = _find(result, "C01", "X85001")
    assert any(s["action"] == "reschedule" for s in c01["suggestions"])
    c02 = _find(result, "C02", "X85004")
    assert any(s["action"] == "reassign_track"
               and s["target_track_id"] is not None for s in c02["suggestions"])
    session.close()


def test_rule_change_removes_gauge_conflict(db):
    """关闭超限检查后 C05 应消失；放宽限界后也应消失。"""
    from app import models
    import json
    session = SessionLocal()

    session.add(models.Rule(key="gauge_max_width_m",
                            value=json.dumps(4.0), value_type="number"))
    session.add(models.Rule(key="gauge_max_height_m",
                            value=json.dumps(5.5), value_type="number"))
    session.commit()

    result = analyze(session)
    assert _find(result, "C05", "X85007") is None
    session.close()


def test_clean_schedule_has_no_high_conflicts(db):
    """构造一份完全合规的安排，不应有高风险冲突。"""
    session = SessionLocal()
    session.query(Train).delete()
    track = Track(name="T1", length_m=1000, occupied_length_m=0,
                  max_load_t=5000, allow_dangerous=True, allow_overload=True)
    session.add(track)
    session.flush()
    loco = Locomotive(name="L1", status=LocoStatus.available)
    session.add(loco)
    session.flush()

    def dt(h):
        return datetime(2026, 9, 20, h, 0)

    session.add_all([
        Train(code="A1", arrival_time=dt(8), departure_time=dt(9),
              length_m=500, weight_t=2000, max_width_m=3.0, max_height_m=4.0,
              track_id=track.id, locomotive_id=loco.id, sequence_no=1),
        Train(code="A2", arrival_time=dt(10), departure_time=dt(11),
              length_m=500, weight_t=2000, max_width_m=3.0, max_height_m=4.0,
              track_id=track.id, locomotive_id=loco.id, sequence_no=2),
    ])
    session.commit()

    result = analyze(session)
    high = [c for c in result["conflicts"] if c["severity"] == "high"]
    assert high == []
    # 顺序与到达一致，无 C07
    assert _find(result, "C07") is None
    session.close()


def test_dangerous_on_normal_track(db):
    session = SessionLocal()
    track = session.query(Track).filter_by(name="G1").first()
    train = Train(
        code="DG1", train_type=TrainType.freight_dangerous,
        arrival_time=datetime(2026, 9, 19, 8), departure_time=datetime(2026, 9, 19, 9),
        length_m=300, weight_t=1000,
        track_id=track.id,
        locomotive_id=session.query(Locomotive).first().id,
    )
    session.add(train)
    session.commit()
    result = analyze(session)
    assert _find(result, "C04", "DG1") is not None
    session.close()

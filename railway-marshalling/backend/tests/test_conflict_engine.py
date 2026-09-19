"""冲突检测引擎单元测试。"""
from datetime import datetime, timedelta

from app.conflict_engine import (
    TrainView,
    detect_locomotive,
    detect_over_limit,
    detect_sequence,
    detect_track_occupation,
    run_analysis,
)

BASE = datetime(2026, 9, 19, 6, 0, 0)
H = timedelta(hours=1)
M = timedelta(minutes=1)

TRACKS = {
    1: {"id": 1, "name": "1道", "length_m": 900.0, "status": "active"},
    2: {"id": 2, "name": "2道", "length_m": 700.0, "status": "active"},
}
RULES = [{
    "is_active": True,
    "max_wagons": 60,
    "max_length_m": 850.0,
    "max_weight_t": 5000.0,
    "min_departure_interval_min": 15,
    "max_dwell_time_min": 720,
}]
LOCOS = {
    1: {"id": 1, "loco_number": "HXD3-0001", "status": "available",
        "max_traction_weight_t": 6000.0, "available_from": None},
    2: {"id": 2, "loco_number": "DF8B-0112", "status": "maintenance",
        "max_traction_weight_t": 4000.0, "available_from": None},
}


def make_train(tid, track_id=1, arr_offset=0, dep_offset=2, **kw):
    defaults = dict(
        id=tid, train_number=f"X{tid:03d}",
        arrival_time=BASE + arr_offset * H,
        departure_time=BASE + dep_offset * H,
        wagon_count=40, total_length_m=500.0, total_weight_t=3000.0,
        track_id=track_id, locomotive_id=None,
    )
    defaults.update(kw)
    return TrainView(**defaults)


# ---------- 股道占用 ----------

def test_track_occupation_detected():
    trains = [make_train(1, arr_offset=0, dep_offset=3),
              make_train(2, arr_offset=1, dep_offset=4)]
    conflicts = detect_track_occupation(trains, TRACKS)
    assert len(conflicts) == 1
    assert conflicts[0].type == "track_occupation"
    assert conflicts[0].severity == "high"
    assert conflicts[0].suggestion  # 附带调整建议


def test_track_occupation_no_overlap():
    trains = [make_train(1, arr_offset=0, dep_offset=2),
              make_train(2, arr_offset=2, dep_offset=4)]
    assert detect_track_occupation(trains, TRACKS) == []


def test_track_occupation_different_tracks():
    trains = [make_train(1, track_id=1), make_train(2, track_id=2)]
    assert detect_track_occupation(trains, TRACKS) == []


# ---------- 顺序冲突 ----------

def test_sequence_inverted_departure():
    # 2 号车晚到却先走 -> 堵门
    trains = [make_train(1, arr_offset=0, dep_offset=5),
              make_train(2, arr_offset=1, dep_offset=3)]
    conflicts = detect_sequence(trains, TRACKS, RULES)
    assert any(c.type == "sequence" and "堵门" in c.message for c in conflicts)


def test_sequence_min_interval():
    trains = [make_train(1, arr_offset=0, dep_offset=3),
              make_train(2, arr_offset=1, dep_offset=3)]
    # 出发时刻相同，间隔 0 < 15 分钟
    conflicts = detect_sequence(trains, TRACKS, RULES)
    assert any("最小间隔" in c.message for c in conflicts)


def test_sequence_ok_when_order_and_gap_fine():
    trains = [make_train(1, arr_offset=0, dep_offset=2),
              make_train(2, arr_offset=1, dep_offset=4)]
    assert detect_sequence(trains, TRACKS, RULES) == []


# ---------- 超限风险 ----------

def test_over_limit_train_longer_than_track():
    trains = [make_train(1, track_id=2, total_length_m=800.0)]  # 2道仅 700m
    conflicts = detect_over_limit(trains, TRACKS, RULES)
    assert any("有效长" in c.message for c in conflicts)


def test_over_limit_rule_violations():
    trains = [make_train(1, track_id=1, wagon_count=70, total_weight_t=5500.0)]
    conflicts = detect_over_limit(trains, TRACKS, RULES)
    messages = " ".join(c.message for c in conflicts)
    assert "辆" in messages and "总重" in messages


def test_over_limit_dwell_time():
    trains = [make_train(1, arr_offset=0, dep_offset=20)]  # 停留 20h > 12h
    conflicts = detect_over_limit(trains, TRACKS, RULES)
    assert any("停留" in c.message for c in conflicts)


def test_over_limit_none_when_compliant():
    trains = [make_train(1)]
    assert detect_over_limit(trains, TRACKS, RULES) == []


# ---------- 机车冲突 ----------

def test_locomotive_overweight():
    trains = [make_train(1, locomotive_id=2, total_weight_t=5000.0)]  # DF8B 仅 4000t
    conflicts = detect_locomotive(trains, LOCOS)
    assert any("无法牵引" in c.message for c in conflicts)


def test_locomotive_unavailable_status():
    trains = [make_train(1, locomotive_id=2, total_weight_t=3000.0)]
    conflicts = detect_locomotive(trains, LOCOS)
    assert any("maintenance" in c.message for c in conflicts)


def test_locomotive_double_booking():
    trains = [make_train(1, locomotive_id=1, arr_offset=0, dep_offset=3),
              make_train(2, locomotive_id=1, arr_offset=1, dep_offset=3)]
    conflicts = detect_locomotive(trains, LOCOS)
    assert any("整备时间不足" in c.message for c in conflicts)


# ---------- 汇总 ----------

def test_run_analysis_sorted_by_severity():
    trains = [
        make_train(1, arr_offset=0, dep_offset=3),
        make_train(2, arr_offset=1, dep_offset=4),          # 占用冲突 (high)
        make_train(3, track_id=2, total_length_m=800.0,    # 超限 (high)
                   arr_offset=10, dep_offset=12),
    ]
    results = run_analysis(trains, TRACKS, LOCOS, RULES)
    assert len(results) >= 2
    assert results[0]["severity"] == "high"
    assert all("suggestion" in r for r in results)

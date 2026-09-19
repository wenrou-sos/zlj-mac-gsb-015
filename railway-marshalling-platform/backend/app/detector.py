"""编组冲突检测引擎。

纯函数式分析：读取当前货列 / 股道 / 机车 / 规则配置，
输出冲突清单、严重程度统计与调整建议，不写数据库。
"""
import json
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from .models import LocoStatus, Locomotive, Rule, Track, Train, TrainType

# ---------------- 默认规则 ----------------
# key: (默认值, 类型, 名称, 分类, 说明)
DEFAULT_RULES: dict[str, tuple] = {
    "track_safety_buffer_min": (
        15, "number", "股道作业安全间隔（分钟）", "track",
        "同一股道相邻两列车作业时间窗之间至少保留的安全间隔。",
    ),
    "track_safety_margin_ratio": (
        0.10, "number", "股道长度预警余量比例", "track",
        "剩余可用长度低于该比例时给出接近满载预警。",
    ),
    "gauge_max_width_m": (
        3.4, "number", "机车车辆限界最大宽度（米）", "gauge",
        "货物最大宽度超过该值判定为超限货物。",
    ),
    "gauge_max_height_m": (
        4.8, "number", "机车车辆限界最大高度（米）", "gauge",
        "货物最大高度超过该值判定为超限货物。",
    ),
    "loco_reserve_ratio": (
        0.2, "number", "机车备用比例", "locomotive",
        "在用机车占可用机车比例高于 1-备用比例 时预警。",
    ),
    "check_track_overlap": (True, "boolean", "检查股道占用冲突", "switch", ""),
    "check_track_buffer": (True, "boolean", "检查安全间隔不足", "switch", ""),
    "check_gauge": (True, "boolean", "检查超限货物风险", "switch", ""),
    "check_sequence": (True, "boolean", "检查编组顺序冲突", "switch", ""),
    "check_loco_double_booking": (True, "boolean", "检查机车时间冲突", "switch", ""),
    "check_loco_capacity": (True, "boolean", "检查机车资源缺口", "switch", ""),
}

CONFLICT_TITLES = {
    "C01": "股道占用冲突",
    "C02": "股道长度超限",
    "C03": "股道载重超限",
    "C04": "股道品类限制",
    "C05": "超限货物风险",
    "C06": "股道安全间隔不足",
    "C07": "编组顺序冲突",
    "C08": "机车时间冲突",
    "C09": "机车资源缺口",
    "C10": "股道未分配",
    "C11": "机车可用窗口不匹配",
    "C12": "股道接近满载",
}

_SEVERITY_ORDER = {"high": 3, "medium": 2, "low": 1}


def load_rules(db: Session) -> dict:
    """默认规则与数据库配置合并，数据库优先。"""
    merged: dict[str, object] = {k: v[0] for k, v in DEFAULT_RULES.items()}
    for row in db.query(Rule).all():
        try:
            merged[row.key] = _cast_rule_value(row.value, row.value_type)
        except (ValueError, TypeError):
            continue
    return merged


def _cast_rule_value(raw: str, value_type: str):
    if value_type == "boolean":
        if isinstance(raw, bool):
            return raw
        return str(raw).strip().lower() in ("1", "true", "yes", "on")
    if value_type == "number":
        return float(raw)
    return json.loads(raw) if raw and raw not in ("null",) else raw


def _type_value(train: Train) -> str:
    t = train.train_type
    return t.value if isinstance(t, TrainType) else str(t)


def _loco_status(loco: Locomotive) -> str:
    s = loco.status
    return s.value if isinstance(s, LocoStatus) else str(s)


def _hard_overlap(a_start, a_end, b_start, b_end) -> bool:
    """作业时间窗是否重叠（首尾相接不算冲突）。"""
    return a_start < b_end and b_start < a_end


def _buffered_overlap(a_start, a_end, b_start, b_end, buf_min) -> tuple[bool, float]:
    """两端各加安全间隔后是否重叠，返回(是否重叠, 间隔缺口分钟数)。

    gap<0 表示硬重叠，0<=gap<2*buf 表示安全间隔不足。
    """
    if a_start <= b_start:
        gap = (b_start - a_end).total_seconds() / 60.0
    else:
        gap = (a_start - b_end).total_seconds() / 60.0
    return gap < 2 * buf_min, gap


def _candidate_tracks(train: Train, tracks: list[Track], trains: list[Train], buf_min):
    """找出能容纳该货列且时间窗不硬冲突的股道。"""
    result = []
    ttype = _type_value(train)
    for tk in tracks:
        if train.track_id == tk.id:
            continue
        if tk.length_m and train.length_m + tk.occupied_length_m > tk.length_m:
            continue
        if tk.max_load_t and train.weight_t > tk.max_load_t:
            continue
        if ttype == "dangerous" and not tk.allow_dangerous:
            continue
        if ttype == "overload" and not tk.allow_overload:
            continue
        clash = any(
            o.track_id == tk.id
            and _hard_overlap(
                train.arrival_time, train.departure_time,
                o.arrival_time, o.departure_time,
            )
            for o in trains if o.id != train.id
        )
        if clash:
            continue
        result.append(tk)
    return result


def _loco_fits_window(loco: Locomotive, start, end) -> bool:
    if loco.available_from and start < loco.available_from:
        return False
    if loco.available_to and end > loco.available_to:
        return False
    return True


def _candidate_locos(train: Train, locos: list[Locomotive], trains: list[Train]):
    result = []
    for loco in locos:
        if train.locomotive_id == loco.id:
            continue
        if _loco_status(loco) != LocoStatus.available.value:
            continue
        if not _loco_fits_window(loco, train.arrival_time, train.departure_time):
            continue
        clash = any(
            o.locomotive_id == loco.id
            and _hard_overlap(
                train.arrival_time, train.departure_time,
                o.arrival_time, o.departure_time,
            )
            for o in trains if o.id != train.id
        )
        if clash:
            continue
        result.append(loco)
    return result


def _track_suggestions(train, tracks, trains, buf_min) -> list[dict]:
    sugs = []
    for tk in _candidate_tracks(train, tracks, trains, buf_min)[:3]:
        sugs.append({
            "action": "reassign_track",
            "description": f"改派至股道「{tk.name}」（有效长度 {tk.length_m:.0f}m，"
                           f"现存 {tk.occupied_length_m:.0f}m，可容纳本列）",
            "target_track_id": tk.id,
        })
    if not sugs:
        sugs.append({
            "action": "manual_review",
            "description": "当前没有同时满足长度/载重/品类/时间窗的空闲股道，"
                           "请人工协调股道或调整作业时间。",
        })
    return sugs


def _loco_suggestions(train, locos, trains) -> list[dict]:
    return [
        {
            "action": "reassign_loco",
            "description": f"改用机车「{l.name}」（{l.model or '通用型'}，状态可用且时间窗匹配）",
            "target_locomotive_id": l.id,
        }
        for l in _candidate_locos(train, locos, trains)[:3]
    ]


def _conflict(code, severity, detail, *, train=None, track=None, loco=None,
              related=None, suggestions=None):
    return {
        "code": code,
        "severity": severity,
        "title": CONFLICT_TITLES[code],
        "detail": detail,
        "train_code": train.code if train else None,
        "track_name": track.name if track else None,
        "locomotive_name": loco.name if loco else None,
        "related_train_code": related.code if related else None,
        "suggestions": suggestions or [],
    }


# ---------------- 单车检查 ----------------

def _check_single_train(train, tracks, locos, trains, rules, conflicts):
    buf_min = rules["track_safety_buffer_min"]
    ttype = _type_value(train)
    track = next((t for t in tracks if t.id == train.track_id), None)

    # 股道未分配
    if track is None:
        sugs = _track_suggestions(train, tracks, trains, buf_min)
        conflicts.append(_conflict(
            "C10", "low",
            f"货列 {train.code} 尚未分配股道，到达后将无法安排编组作业。",
            train=train, suggestions=sugs or None,
        ))
        if not sugs:
            conflicts[-1]["suggestions"].append({
                "action": "manual_review",
                "description": "暂无空闲股道候选，请人工调整班计划或延长在站时间。",
            })
    else:
        # 长度超限
        used = track.occupied_length_m + train.length_m
        if track.length_m > 0:
            ratio = used / track.length_m
            if ratio > 1.0:
                conflicts.append(_conflict(
                    "C02", "high",
                    f"货列 {train.code}（车列长 {train.length_m:.0f}m）接入股道 "
                    f"{track.name} 后总占用 {used:.0f}m，超过有效长度 "
                    f"{track.length_m:.0f}m，超出 {used - track.length_m:.0f}m。",
                    train=train, track=track,
                    suggestions=_track_suggestions(train, tracks, trains, buf_min),
                ))
            elif ratio > 1 - rules["track_safety_margin_ratio"]:
                conflicts.append(_conflict(
                    "C12", "low",
                    f"股道 {track.name} 接入 {train.code} 后占用率达 {ratio * 100:.0f}%，"
                    f"剩余余量低于安全预警比例，请关注调车空间。",
                    train=train, track=track,
                    suggestions=_track_suggestions(train, tracks, trains, buf_min),
                ))

        # 载重超限
        if track.max_load_t and train.weight_t > track.max_load_t:
            conflicts.append(_conflict(
                "C03", "high",
                f"货列 {train.code} 总重 {train.weight_t:.0f}t 超过股道 "
                f"{track.name} 允许载重 {track.max_load_t:.0f}t。",
                train=train, track=track,
                suggestions=_track_suggestions(train, tracks, trains, buf_min),
            ))

        # 品类限制
        if ttype == "dangerous" and not track.allow_dangerous:
            conflicts.append(_conflict(
                "C04", "high",
                f"货列 {train.code} 为危险品列车，股道 {track.name} 未开放危险品作业，"
                f"违反危货股道停放规定。",
                train=train, track=track,
                suggestions=_track_suggestions(train, tracks, trains, buf_min),
            ))
        if ttype == "overload" and not track.allow_overload:
            conflicts.append(_conflict(
                "C04", "high",
                f"货列 {train.code} 为超限/重载列车，股道 {track.name} 不具备超限接车条件。",
                train=train, track=track,
                suggestions=_track_suggestions(train, tracks, trains, buf_min),
            ))

        # 超限货物风险（限界）
        if rules["check_gauge"] and not track.allow_overload:
            over_w = train.max_width_m > rules["gauge_max_width_m"]
            over_h = train.max_height_m > rules["gauge_max_height_m"]
            if over_w or over_h:
                dims = []
                if over_w:
                    dims.append(f"宽度 {train.max_width_m:.2f}m > 限界 "
                                f"{rules['gauge_max_width_m']:.2f}m")
                if over_h:
                    dims.append(f"高度 {train.max_height_m:.2f}m > 限界 "
                                f"{rules['gauge_max_height_m']:.2f}m")
                conflicts.append(_conflict(
                    "C05", "medium",
                    f"货列 {train.code} 存在超限尺寸（{'，'.join(dims)}），接入 "
                    f"{track.name} 前须确认沿线限界与邻线间距。",
                    train=train, track=track,
                    suggestions=([{
                        "action": "manual_review",
                        "description": "安排超限货物专项检查，必要时改走超限指定线路/股道。",
                    }] + _track_suggestions(train, tracks, trains, buf_min)),
                ))

    # 机车未分配
    loco = next((l for l in locos if l.id == train.locomotive_id), None)
    if loco is None:
        conflicts.append(_conflict(
            "C10", "low",
            f"货列 {train.code} 尚未指派调车机车。",
            train=train,
            suggestions=_loco_suggestions(train, locos, trains),
        ))
    else:
        if _loco_status(loco) != LocoStatus.available.value:
            conflicts.append(_conflict(
                "C11", "high",
                f"指派给 {train.code} 的机车 {loco.name} 当前处于检修/不可用状态。",
                train=train, loco=loco,
                suggestions=_loco_suggestions(train, locos, trains),
            ))
        elif not _loco_fits_window(loco, train.arrival_time, train.departure_time):
            win = (
                f"{loco.available_from:%H:%M}–{loco.available_to:%H:%M}"
                if loco.available_from and loco.available_to else "当班窗口"
            )
            conflicts.append(_conflict(
                "C11", "medium",
                f"机车 {loco.name} 的可用时间窗（{win}）无法覆盖货列 {train.code} 的"
                f" {train.arrival_time:%H:%M}–{train.departure_time:%H:%M} 作业时段。",
                train=train, loco=loco,
                suggestions=_loco_suggestions(train, locos, trains),
            ))


# ---------------- 成对检查 ----------------

def _check_pairs(trains, rules, conflicts):
    buf_min = rules["track_safety_buffer_min"]

    for i, a in enumerate(trains):
        for b in trains[i + 1:]:
            # 同股道时间检查
            if a.track_id and a.track_id == b.track_id:
                hard = _hard_overlap(
                    a.arrival_time, a.departure_time,
                    b.arrival_time, b.departure_time,
                )
                buffered, gap = _buffered_overlap(
                    a.arrival_time, a.departure_time,
                    b.arrival_time, b.departure_time, buf_min,
                )
                if hard and rules["check_track_overlap"]:
                    conflicts.append(_conflict(
                        "C01", "high",
                        f"货列 {a.code} 与 {b.code} 同时占用同一股道，作业时间窗 "
                        f"{a.arrival_time:%H:%M}–{a.departure_time:%H:%M} 与 "
                        f"{b.arrival_time:%H:%M}–{b.departure_time:%H:%M} 重叠。",
                        train=a, track=a.track, related=b,
                        suggestions=[{
                            "action": "reschedule",
                            "description": f"将 {b.code} 到达时间延后至 "
                                           f"{a.departure_time + timedelta(minutes=buf_min):%H:%M} 之后",
                            "new_arrival_time": a.departure_time + timedelta(minutes=buf_min),
                        }],
                    ))
                elif buffered and rules["check_track_buffer"]:
                    early_b, late_b = (a, b) if a.arrival_time <= b.arrival_time else (b, a)
                    suggested_b = early_b.departure_time + timedelta(minutes=2 * buf_min)
                    sugs_b = []
                    if suggested_b > late_b.arrival_time:
                        sugs_b = [{
                            "action": "reschedule",
                            "description": f"将 {late_b.code} 到达时间延后至 "
                                           f"{suggested_b:%Y-%m-%d %H:%M}（满足两端安全间隔）",
                            "new_arrival_time": suggested_b,
                        }]
                    conflicts.append(_conflict(
                        "C06", "medium",
                        f"货列 {a.code} 与 {b.code} 在同一股道的作业间隔仅 "
                        f"{gap:.0f} 分钟，低于安全间隔 {buf_min:.0f} 分钟"
                        f"（前后各需 {buf_min:.0f} 分钟）。",
                        train=a, track=a.track, related=b,
                        suggestions=sugs_b,
                    ))

                # 编组顺序检查（时间不重叠时才有意义）
                if (not hard and rules["check_sequence"]
                        and a.sequence_no is not None and b.sequence_no is not None):
                    early, late = (a, b) if a.arrival_time <= b.arrival_time else (b, a)
                    if early.sequence_no > late.sequence_no:
                        conflicts.append(_conflict(
                            "C07", "medium",
                            f"股道上编组顺序与到达顺序不一致：{early.code} 先到达"
                            f"（{early.arrival_time:%H:%M}）但编组序号为 "
                            f"{early.sequence_no}，{late.code} 序号为 {late.sequence_no}，"
                            f"将产生调车钩计划冲突。",
                            train=early, track=a.track, related=late,
                            suggestions=[{
                                "action": "fix_sequence",
                                "description": f"将 {early.code} 编组序号调整为 "
                                               f"{late.sequence_no}（或对调两列序号）。",
                                "new_sequence_no": late.sequence_no,
                            }],
                        ))

            # 同机车时间检查
            if a.locomotive_id and a.locomotive_id == b.locomotive_id:
                hard = _hard_overlap(
                    a.arrival_time, a.departure_time,
                    b.arrival_time, b.departure_time,
                )
                buffered, gap = _buffered_overlap(
                    a.arrival_time, a.departure_time,
                    b.arrival_time, b.departure_time, buf_min,
                )
                if hard and rules["check_loco_double_booking"]:
                    # 换机车建议在 analyze 后处理中统一补充（需要全部机车列表）
                    conflicts.append(_conflict(
                        "C08", "high",
                        f"机车 {a.locomotive.name if a.locomotive else ''} 被同时指派给 "
                        f"{a.code} 与 {b.code}，两列作业时间窗重叠，无法兼顾。",
                        train=a, loco=a.locomotive, related=b,
                    ))
                elif buffered and rules["check_loco_double_booking"]:
                    conflicts.append(_conflict(
                        "C08", "medium",
                        f"机车 {a.locomotive.name if a.locomotive else ''} 连续担当 "
                        f"{a.code} 与 {b.code}，间隔仅 {gap:.0f} 分钟，不足安全间隔 "
                        f"{2 * buf_min:.0f} 分钟（含整备时间）。",
                        train=a, loco=a.locomotive, related=b,
                    ))


# ---------------- 机车资源总量检查 ----------------

def _check_loco_capacity(trains, locos, rules, conflicts):
    if not rules["check_loco_capacity"] or not trains:
        return
    available = [l for l in locos if _loco_status(l) == LocoStatus.available.value]
    # 扫描所有到达/发车事件，统计峰值并行作业数
    events = []
    for t in trains:
        if t.locomotive_id:  # 已纳入机车作业计划
            events.append((t.arrival_time, 1))
            events.append((t.departure_time, -1))
    events.sort(key=lambda e: (e[0], e[1]))
    active = peak = 0
    peak_time = None
    for ts, delta in events:
        active += delta
        if active > peak:
            peak, peak_time = active, ts
    if peak > len(available):
        conflicts.append(_conflict(
            "C09", "high",
            f"{peak_time:%Y-%m-%d %H:%M} 前后有 {peak} 列货列并行作业，"
            f"但仅 {len(available)} 台机车可用，存在 {peak - len(available)} 台机车缺口。",
            suggestions=[{
                "action": "manual_review",
                "description": "增派机车、安排跨区支援，或将部分列车作业时间错峰调整。",
            }],
        ))


# ---------------- 主入口 ----------------

def analyze(db: Session) -> dict:
    rules = load_rules(db)
    trains = db.query(Train).order_by(Train.arrival_time).all()
    tracks = db.query(Track).order_by(Track.id).all()
    locos = db.query(Locomotive).order_by(Locomotive.id).all()

    conflicts: list[dict] = []
    for train in trains:
        _check_single_train(train, tracks, locos, trains, rules, conflicts)
    _check_pairs(trains, rules, conflicts)

    # 为机车时间冲突补充换机车建议
    loco_by_id = {l.id: l for l in locos}
    for c in conflicts:
        if c["code"] == "C08" and not c["suggestions"]:
            target = next((t for t in trains if t.code == c["train_code"]), None)
            if target:
                c["suggestions"] = _loco_suggestions(target, locos, trains)
            if not c["suggestions"]:
                c["suggestions"] = [{
                    "action": "manual_review",
                    "description": "暂无空闲机车候选，请错峰安排作业或增派机车。",
                }]

    _check_loco_capacity(trains, locos, rules, conflicts)

    conflicts.sort(
        key=lambda c: (-_SEVERITY_ORDER[c["severity"]], c["code"], c["train_code"] or "")
    )

    summary = {"high": 0, "medium": 0, "low": 0, "total": len(conflicts)}
    for c in conflicts:
        summary[c["severity"]] += 1

    # 股道统计
    track_stats = []
    for tk in tracks:
        assigned = [t for t in trains if t.track_id == tk.id]
        used = tk.occupied_length_m + sum(t.length_m for t in assigned)
        track_stats.append({
            "track_id": tk.id,
            "track_name": tk.name,
            "trains": len(assigned),
            "used_length_m": round(used, 1),
            "capacity_m": tk.length_m,
            "utilization": round(used / tk.length_m, 3) if tk.length_m else 0.0,
        })
    unassigned = [t for t in trains if t.track_id is None]
    if unassigned:
        track_stats.append({
            "track_id": None,
            "track_name": "未分配",
            "trains": len(unassigned),
            "used_length_m": round(sum(t.length_m for t in unassigned), 1),
            "capacity_m": 0,
            "utilization": 0.0,
        })

    loco_stats = []
    for l in locos:
        loco_stats.append({
            "locomotive_id": l.id,
            "locomotive_name": l.name,
            "trains": sum(1 for t in trains if t.locomotive_id == l.id),
        })
    loco_orphans = [t for t in trains if t.locomotive_id is None]
    if loco_orphans:
        loco_stats.append({
            "locomotive_id": None,
            "locomotive_name": "未指派",
            "trains": len(loco_orphans),
        })

    return {
        "generated_at": datetime.now(),
        "train_count": len(trains),
        "track_count": len(tracks),
        "locomotive_count": len(locos),
        "conflicts": conflicts,
        "summary": summary,
        "timeline_start": min((t.arrival_time for t in trains), default=None),
        "timeline_end": max((t.departure_time for t in trains), default=None),
        "track_stats": track_stats,
        "loco_stats": loco_stats,
    }

"""编组冲突检测引擎（纯函数，便于单元测试）。

检测四类问题：
1. track_occupation —— 股道占用冲突：同一股道上两列车的时间窗重叠；
2. sequence         —— 顺序冲突：同一股道上后到列车先发（出发顺序与到达顺序矛盾），
                      或相邻出发间隔小于编组规则要求的最小间隔；
3. over_limit       —— 超限风险：列车长度超股道有效长、辆数/长度/重量超编组规则、
                      停留时间超规则上限；
4. locomotive       —— 机车冲突：牵引重量超机车能力、机车不可用、
                      同一机车时间窗重叠。

每类冲突都附带调整建议（suggestion）。
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta


@dataclass
class Conflict:
    type: str
    severity: str
    message: str
    train_ids: list[int]
    track_id: int | None = None
    suggestion: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class TrainView:
    """检测引擎使用的列车视图（与 ORM 解耦）。"""

    id: int
    train_number: str
    arrival_time: datetime
    departure_time: datetime | None
    wagon_count: int
    total_length_m: float
    total_weight_t: float
    priority: int = 3
    track_id: int | None = None
    locomotive_id: int | None = None
    extra: dict = field(default_factory=dict)

    @property
    def effective_departure(self) -> datetime:
        """未排出发时间时视为长期占用股道。"""
        return self.departure_time or datetime.max


def _fmt(dt: datetime) -> str:
    return dt.strftime("%m-%d %H:%M") if dt != datetime.max else "未定"


# ---------------------------------------------------------------- 股道占用
def detect_track_occupation(trains: list[TrainView], tracks: dict[int, dict]) -> list[Conflict]:
    conflicts: list[Conflict] = []
    by_track: dict[int, list[TrainView]] = {}
    for t in trains:
        if t.track_id is not None:
            by_track.setdefault(t.track_id, []).append(t)

    for track_id, group in by_track.items():
        group.sort(key=lambda t: t.arrival_time)
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                a, b = group[i], group[j]
                # b 的到达早于 a 的出发 => 时间窗重叠
                if b.arrival_time < a.effective_departure:
                    track_name = tracks.get(track_id, {}).get("name", f"股道{track_id}")
                    conflicts.append(Conflict(
                        type="track_occupation",
                        severity="high",
                        message=(
                            f"{track_name}：列车 {a.train_number}（{_fmt(a.arrival_time)}~{_fmt(a.effective_departure)}）"
                            f"与 {b.train_number}（{_fmt(b.arrival_time)}~{_fmt(b.effective_departure)}）占用时间重叠"
                        ),
                        train_ids=[a.id, b.id],
                        track_id=track_id,
                        suggestion=_suggest_reassign(b, trains, tracks, exclude_track=track_id),
                    ))
    return conflicts


def _suggest_reassign(train: TrainView, all_trains: list[TrainView],
                      tracks: dict[int, dict], exclude_track: int | None) -> str:
    """为列车寻找一条长度足够且时间窗空闲的替代股道。"""
    for tid, tk in sorted(tracks.items(), key=lambda kv: -kv[1].get("length_m", 0)):
        if tid == exclude_track or tk.get("status") != "active":
            continue
        if tk.get("length_m", 0) < train.total_length_m:
            continue
        overlap = any(
            o.track_id == tid and o.id != train.id
            and o.arrival_time < train.effective_departure
            and train.arrival_time < o.effective_departure
            for o in all_trains
        )
        if not overlap:
            return f"建议将列车 {train.train_number} 调整至 {tk.get('name')}（空闲且长度满足）"
    return f"建议推迟列车 {train.train_number} 的到达/出发时刻，错开股道占用窗口"


# ---------------------------------------------------------------- 顺序冲突
def detect_sequence(trains: list[TrainView], tracks: dict[int, dict],
                    rules: list[dict]) -> list[Conflict]:
    conflicts: list[Conflict] = []
    min_interval = min((r["min_departure_interval_min"] for r in rules if r.get("is_active")),
                       default=15)

    by_track: dict[int, list[TrainView]] = {}
    for t in trains:
        if t.track_id is not None and t.departure_time is not None:
            by_track.setdefault(t.track_id, []).append(t)

    for track_id, group in by_track.items():
        track_name = tracks.get(track_id, {}).get("name", f"股道{track_id}")
        # 1) 出发顺序与到达顺序矛盾（尽头式股道后到先发会堵死先到列车）
        by_arrival = sorted(group, key=lambda t: t.arrival_time)
        by_departure = sorted(group, key=lambda t: t.departure_time)
        arr_order = [t.id for t in by_arrival]
        dep_order = [t.id for t in by_departure]
        if arr_order != dep_order:
            # 找出第一对逆序的列车
            for i in range(len(by_arrival)):
                for j in range(i + 1, len(by_arrival)):
                    early, late = by_arrival[i], by_arrival[j]
                    if late.departure_time < early.departure_time:
                        conflicts.append(Conflict(
                            type="sequence",
                            severity="medium",
                            message=(
                                f"{track_name}：{late.train_number} 到达晚于 {early.train_number}，"
                                f"却计划于 {_fmt(late.departure_time)} 先于其 {_fmt(early.departure_time)} 出发，"
                                f"形成堵门"
                            ),
                            train_ids=[early.id, late.id],
                            track_id=track_id,
                            suggestion=(
                                f"建议将 {early.train_number} 的出发提前至 "
                                f"{_fmt(late.departure_time - timedelta(minutes=min_interval))} 之前，"
                                f"或将 {late.train_number} 调至其他股道"
                            ),
                        ))
                        break
                else:
                    continue
                break

        # 2) 相邻出发间隔不足
        for k in range(1, len(by_departure)):
            prev, cur = by_departure[k - 1], by_departure[k]
            gap = (cur.departure_time - prev.departure_time).total_seconds() / 60
            if gap < min_interval:
                conflicts.append(Conflict(
                    type="sequence",
                    severity="medium",
                    message=(
                        f"{track_name}：{prev.train_number} 与 {cur.train_number} 出发间隔 "
                        f"{gap:.0f} 分钟，小于规则要求的最小间隔 {min_interval} 分钟"
                    ),
                    train_ids=[prev.id, cur.id],
                    track_id=track_id,
                    suggestion=(
                        f"建议将 {cur.train_number} 出发时间推迟至 "
                        f"{_fmt(prev.departure_time + timedelta(minutes=min_interval))} 之后"
                    ),
                ))
    return conflicts


# ---------------------------------------------------------------- 超限风险
def detect_over_limit(trains: list[TrainView], tracks: dict[int, dict],
                      rules: list[dict]) -> list[Conflict]:
    conflicts: list[Conflict] = []
    active_rules = [r for r in rules if r.get("is_active")]
    # 取最严格（最小）的限制
    max_wagons = min((r["max_wagons"] for r in active_rules), default=None)
    max_length = min((r["max_length_m"] for r in active_rules), default=None)
    max_weight = min((r["max_weight_t"] for r in active_rules), default=None)
    max_dwell = min((r["max_dwell_time_min"] for r in active_rules), default=None)

    for t in trains:
        track = tracks.get(t.track_id) if t.track_id else None
        track_name = track.get("name") if track else None

        if track and t.total_length_m > track.get("length_m", 0):
            conflicts.append(Conflict(
                type="over_limit",
                severity="high",
                message=(
                    f"列车 {t.train_number} 长度 {t.total_length_m:.0f}m 超过 "
                    f"{track_name} 有效长 {track['length_m']:.0f}m"
                ),
                train_ids=[t.id],
                track_id=t.track_id,
                suggestion=_suggest_longer_track(t, tracks),
            ))
        if max_wagons is not None and t.wagon_count > max_wagons:
            conflicts.append(Conflict(
                type="over_limit",
                severity="medium",
                message=f"列车 {t.train_number} 编组 {t.wagon_count} 辆，超过规则上限 {max_wagons} 辆",
                train_ids=[t.id],
                track_id=t.track_id,
                suggestion=f"建议拆分列车，将辆数降至 {max_wagons} 辆以内（可分解为两列开行）",
            ))
        if max_length is not None and t.total_length_m > max_length:
            conflicts.append(Conflict(
                type="over_limit",
                severity="medium",
                message=f"列车 {t.train_number} 长度 {t.total_length_m:.0f}m 超过规则上限 {max_length:.0f}m",
                train_ids=[t.id],
                track_id=t.track_id,
                suggestion="建议减挂车辆或拆分编组以降低列车长度",
            ))
        if max_weight is not None and t.total_weight_t > max_weight:
            conflicts.append(Conflict(
                type="over_limit",
                severity="medium",
                message=f"列车 {t.train_number} 总重 {t.total_weight_t:.0f}t 超过规则上限 {max_weight:.0f}t",
                train_ids=[t.id],
                track_id=t.track_id,
                suggestion="建议减挂重车或拆分编组，必要时改用双机牵引",
            ))
        if max_dwell is not None and t.departure_time:
            dwell = (t.departure_time - t.arrival_time).total_seconds() / 60
            if dwell > max_dwell:
                conflicts.append(Conflict(
                    type="over_limit",
                    severity="low",
                    message=(
                        f"列车 {t.train_number} 计划停留 {dwell:.0f} 分钟，"
                        f"超过规则上限 {max_dwell} 分钟，长期占用股道"
                    ),
                    train_ids=[t.id],
                    track_id=t.track_id,
                    suggestion="建议提前编组出发，或转场至存车线释放到发线能力",
                ))
    return conflicts


def _suggest_longer_track(train: TrainView, tracks: dict[int, dict]) -> str:
    candidates = [tk["name"] for tk in tracks.values()
                  if tk.get("status") == "active" and tk.get("length_m", 0) >= train.total_length_m]
    if candidates:
        return f"建议将列车 {train.train_number} 调整至更长的股道：{'、'.join(candidates)}"
    return f"站内无足够长度的股道容纳列车 {train.train_number}，建议拆分编组"


# ---------------------------------------------------------------- 机车冲突
def detect_locomotive(trains: list[TrainView], locos: dict[int, dict]) -> list[Conflict]:
    conflicts: list[Conflict] = []

    for t in trains:
        if t.locomotive_id is None:
            continue
        loco = locos.get(t.locomotive_id)
        if loco is None:
            conflicts.append(Conflict(
                type="locomotive",
                severity="high",
                message=f"列车 {t.train_number} 指定的机车（ID {t.locomotive_id}）不存在",
                train_ids=[t.id],
                suggestion="请重新指派可用机车",
            ))
            continue
        if t.total_weight_t > loco.get("max_traction_weight_t", 0):
            conflicts.append(Conflict(
                type="locomotive",
                severity="high",
                message=(
                    f"机车 {loco['loco_number']} 最大牵引 {loco['max_traction_weight_t']:.0f}t，"
                    f"无法牵引总重 {t.total_weight_t:.0f}t 的列车 {t.train_number}"
                ),
                train_ids=[t.id],
                suggestion=_suggest_stronger_loco(t, locos),
            ))
        if loco.get("status") != "available":
            conflicts.append(Conflict(
                type="locomotive",
                severity="medium",
                message=f"机车 {loco['loco_number']} 当前状态为 {loco.get('status')}，不可担当牵引任务",
                train_ids=[t.id],
                suggestion=_suggest_stronger_loco(t, locos, exclude=loco["id"]),
            ))
        dep = t.departure_time
        if dep and loco.get("available_from") and dep < loco["available_from"]:
            conflicts.append(Conflict(
                type="locomotive",
                severity="medium",
                message=(
                    f"机车 {loco['loco_number']} 自 {_fmt(loco['available_from'])} 才可用，"
                    f"晚于列车 {t.train_number} 的出发时刻 {_fmt(dep)}"
                ),
                train_ids=[t.id],
                suggestion=f"建议推迟 {t.train_number} 出发或更换机车",
            ))

    # 同一机车时间窗重叠（按出发时刻前后各预留 60 分钟整备）
    by_loco: dict[int, list[TrainView]] = {}
    for t in trains:
        if t.locomotive_id is not None and t.departure_time is not None:
            by_loco.setdefault(t.locomotive_id, []).append(t)
    for loco_id, group in by_loco.items():
        group.sort(key=lambda t: t.departure_time)
        for k in range(1, len(group)):
            prev, cur = group[k - 1], group[k]
            gap = (cur.departure_time - prev.departure_time).total_seconds() / 60
            if gap < 60:
                loco_no = locos.get(loco_id, {}).get("loco_number", f"机车{loco_id}")
                conflicts.append(Conflict(
                    type="locomotive",
                    severity="medium",
                    message=(
                        f"机车 {loco_no} 需在 {gap:.0f} 分钟内连续担当 "
                        f"{prev.train_number} 与 {cur.train_number} 的牵引任务，整备时间不足"
                    ),
                    train_ids=[prev.id, cur.id],
                    suggestion=f"建议为 {cur.train_number} 另行指派机车，或推迟其出发时间",
                ))
    return conflicts


def _suggest_stronger_loco(train: TrainView, locos: dict[int, dict],
                           exclude: int | None = None) -> str:
    candidates = [
        l["loco_number"] for l in locos.values()
        if l.get("id") != exclude
        and l.get("status") == "available"
        and l.get("max_traction_weight_t", 0) >= train.total_weight_t
    ]
    if candidates:
        return f"建议改用牵引能力更强的机车：{'、'.join(candidates)}"
    return f"无机车可牵引 {train.total_weight_t:.0f}t，建议减挂或双机牵引"


# ---------------------------------------------------------------- 汇总入口
def run_analysis(trains: list[TrainView], tracks: dict[int, dict],
                 locos: dict[int, dict], rules: list[dict]) -> list[dict]:
    """执行全部检测，返回冲突字典列表（按严重程度排序）。"""
    severity_rank = {"high": 0, "medium": 1, "low": 2}
    conflicts: list[Conflict] = []
    conflicts += detect_track_occupation(trains, tracks)
    conflicts += detect_sequence(trains, tracks, rules)
    conflicts += detect_over_limit(trains, tracks, rules)
    conflicts += detect_locomotive(trains, locos)
    return [c.to_dict() for c in sorted(conflicts, key=lambda c: severity_rank.get(c.severity, 9))]

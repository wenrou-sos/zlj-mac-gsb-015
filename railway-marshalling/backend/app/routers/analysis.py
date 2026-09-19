"""冲突分析路由：运行分析、查询历史结果。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..conflict_engine import TrainView, run_analysis
from ..database import get_db

router = APIRouter(prefix="/analysis", tags=["冲突分析"])


def _load_views(db: Session):
    trains = [
        TrainView(
            id=t.id,
            train_number=t.train_number,
            arrival_time=t.arrival_time,
            departure_time=t.departure_time,
            wagon_count=t.wagon_count,
            total_length_m=t.total_length_m,
            total_weight_t=t.total_weight_t,
            priority=t.priority,
            track_id=t.track_id,
            locomotive_id=t.locomotive_id,
        )
        for t in db.query(models.Train).all()
    ]
    tracks = {
        t.id: {"id": t.id, "name": t.name, "length_m": t.length_m, "status": t.status}
        for t in db.query(models.Track).all()
    }
    locos = {
        l.id: {
            "id": l.id,
            "loco_number": l.loco_number,
            "status": l.status,
            "max_traction_weight_t": l.max_traction_weight_t,
            "available_from": l.available_from,
        }
        for l in db.query(models.Locomotive).all()
    }
    rules = [
        {
            "is_active": r.is_active,
            "max_wagons": r.max_wagons,
            "max_length_m": r.max_length_m,
            "max_weight_t": r.max_weight_t,
            "min_departure_interval_min": r.min_departure_interval_min,
            "max_dwell_time_min": r.max_dwell_time_min,
        }
        for r in db.query(models.MarshallingRule).all()
    ]
    return trains, tracks, locos, rules


@router.post("/run", response_model=schemas.AnalysisRunOut, status_code=201)
def run(db: Session = Depends(get_db)):
    """对当前全部数据执行一次冲突分析并保存结果。"""
    trains, tracks, locos, rules = _load_views(db)
    results = run_analysis(trains, tracks, locos, rules)
    record = models.AnalysisRun(
        train_count=len(trains),
        conflict_count=len(results),
        results=results,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/latest", response_model=schemas.AnalysisRunOut)
def latest(db: Session = Depends(get_db)):
    record = db.query(models.AnalysisRun).order_by(models.AnalysisRun.id.desc()).first()
    if record is None:
        raise HTTPException(status_code=404, detail="尚未运行过分析")
    return record


@router.get("/runs", response_model=list[schemas.AnalysisRunOut])
def history(limit: int = 20, db: Session = Depends(get_db)):
    return (
        db.query(models.AnalysisRun)
        .order_by(models.AnalysisRun.id.desc())
        .limit(limit)
        .all()
    )

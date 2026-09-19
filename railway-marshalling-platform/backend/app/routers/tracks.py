"""股道接口。"""
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/tracks", tags=["tracks"])


@router.get("", response_model=schemas.ListResponse[schemas.TrackOut])
def list_tracks(db: Session = Depends(get_db)):
    items = db.query(models.Track).order_by(models.Track.id).all()
    return {"total": len(items), "items": items}


@router.post("", response_model=schemas.TrackOut, status_code=status.HTTP_201_CREATED)
def create_track(data: schemas.TrackCreate, db: Session = Depends(get_db)):
    track = models.Track(**data.model_dump())
    db.add(track)
    db.commit()
    db.refresh(track)
    return track


@router.get("/{track_id}", response_model=schemas.TrackOut)
def get_track(track_id: int, db: Session = Depends(get_db)):
    track = db.get(models.Track, track_id)
    if not track:
        raise HTTPException(404, "股道不存在")
    return track


@router.put("/{track_id}", response_model=schemas.TrackOut)
def update_track(track_id: int, data: schemas.TrackUpdate, db: Session = Depends(get_db)):
    track = db.get(models.Track, track_id)
    if not track:
        raise HTTPException(404, "股道不存在")
    for k, v in data.model_dump().items():
        setattr(track, k, v)
    db.commit()
    db.refresh(track)
    return track


@router.delete("/{track_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_track(track_id: int, db: Session = Depends(get_db)):
    track = db.get(models.Track, track_id)
    if not track:
        raise HTTPException(404, "股道不存在")
    db.delete(track)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

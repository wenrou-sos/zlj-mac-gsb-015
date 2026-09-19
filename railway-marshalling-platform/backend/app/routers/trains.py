"""货列接口。"""
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/trains", tags=["trains"])


@router.get("", response_model=schemas.ListResponse[schemas.TrainOut])
def list_trains(db: Session = Depends(get_db)):
    items = db.query(models.Train).order_by(models.Train.arrival_time).all()
    return {"total": len(items), "items": items}


@router.post("", response_model=schemas.TrainOut, status_code=status.HTTP_201_CREATED)
def create_train(data: schemas.TrainCreate, db: Session = Depends(get_db)):
    _validate_refs(db, data)
    train = models.Train(**data.model_dump())
    db.add(train)
    db.commit()
    db.refresh(train)
    return train


@router.get("/{train_id}", response_model=schemas.TrainOut)
def get_train(train_id: int, db: Session = Depends(get_db)):
    train = db.get(models.Train, train_id)
    if not train:
        raise HTTPException(404, "货列不存在")
    return train


@router.put("/{train_id}", response_model=schemas.TrainOut)
def update_train(train_id: int, data: schemas.TrainUpdate, db: Session = Depends(get_db)):
    train = db.get(models.Train, train_id)
    if not train:
        raise HTTPException(404, "货列不存在")
    _validate_refs(db, data)
    for k, v in data.model_dump().items():
        setattr(train, k, v)
    db.commit()
    db.refresh(train)
    return train


@router.delete("/{train_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_train(train_id: int, db: Session = Depends(get_db)):
    train = db.get(models.Train, train_id)
    if not train:
        raise HTTPException(404, "货列不存在")
    db.delete(train)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _validate_refs(db: Session, data: schemas.TrainBase):
    if data.track_id is not None and not db.get(models.Track, data.track_id):
        raise HTTPException(422, f"股道 {data.track_id} 不存在")
    if data.locomotive_id is not None and not db.get(models.Locomotive, data.locomotive_id):
        raise HTTPException(422, f"机车 {data.locomotive_id} 不存在")

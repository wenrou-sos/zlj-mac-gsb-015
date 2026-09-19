"""机车接口。"""
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/locomotives", tags=["locomotives"])


@router.get("", response_model=schemas.ListResponse[schemas.LocomotiveOut])
def list_locomotives(db: Session = Depends(get_db)):
    items = db.query(models.Locomotive).order_by(models.Locomotive.id).all()
    return {"total": len(items), "items": items}


@router.post("", response_model=schemas.LocomotiveOut, status_code=status.HTTP_201_CREATED)
def create_locomotive(data: schemas.LocomotiveCreate, db: Session = Depends(get_db)):
    loco = models.Locomotive(**data.model_dump())
    db.add(loco)
    db.commit()
    db.refresh(loco)
    return loco


@router.get("/{locomotive_id}", response_model=schemas.LocomotiveOut)
def get_locomotive(locomotive_id: int, db: Session = Depends(get_db)):
    loco = db.get(models.Locomotive, locomotive_id)
    if not loco:
        raise HTTPException(404, "机车不存在")
    return loco


@router.put("/{locomotive_id}", response_model=schemas.LocomotiveOut)
def update_locomotive(locomotive_id: int, data: schemas.LocomotiveUpdate,
                      db: Session = Depends(get_db)):
    loco = db.get(models.Locomotive, locomotive_id)
    if not loco:
        raise HTTPException(404, "机车不存在")
    for k, v in data.model_dump().items():
        setattr(loco, k, v)
    db.commit()
    db.refresh(loco)
    return loco


@router.delete("/{locomotive_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_locomotive(locomotive_id: int, db: Session = Depends(get_db)):
    loco = db.get(models.Locomotive, locomotive_id)
    if not loco:
        raise HTTPException(404, "机车不存在")
    db.delete(loco)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

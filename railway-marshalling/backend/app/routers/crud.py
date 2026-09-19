"""通用 CRUD 路由工厂，供各资源路由复用。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import get_db


def make_crud_router(*, model, create_schema, update_schema, prefix: str, tag: str) -> APIRouter:
    router = APIRouter(prefix=prefix, tags=[tag])

    @router.get("")
    def list_items(db: Session = Depends(get_db)):
        return db.query(model).order_by(model.id).all()

    @router.post("", status_code=201)
    def create_item(payload: create_schema, db: Session = Depends(get_db)):
        obj = model(**payload.model_dump())
        db.add(obj)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=409, detail="唯一性冲突：名称/编号已存在")
        db.refresh(obj)
        return obj

    @router.get("/{item_id}")
    def get_item(item_id: int, db: Session = Depends(get_db)):
        obj = db.get(model, item_id)
        if obj is None:
            raise HTTPException(status_code=404, detail="资源不存在")
        return obj

    @router.put("/{item_id}")
    def update_item(item_id: int, payload: update_schema, db: Session = Depends(get_db)):
        obj = db.get(model, item_id)
        if obj is None:
            raise HTTPException(status_code=404, detail="资源不存在")
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(obj, key, value)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=409, detail="唯一性冲突：名称/编号已存在")
        db.refresh(obj)
        return obj

    @router.delete("/{item_id}", status_code=204)
    def delete_item(item_id: int, db: Session = Depends(get_db)):
        obj = db.get(model, item_id)
        if obj is None:
            raise HTTPException(status_code=404, detail="资源不存在")
        db.delete(obj)
        db.commit()

    return router

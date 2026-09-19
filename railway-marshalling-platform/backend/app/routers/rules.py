"""编组规则接口。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import crud, models, schemas
from ..database import get_db
from ..detector import DEFAULT_RULES

router = APIRouter(prefix="/rules", tags=["rules"])


@router.get("")
def list_rules(db: Session = Depends(get_db)):
    """返回默认规则 + 数据库覆盖值（标注是否被自定义）。"""
    overrides = {r.key: r for r in db.query(models.Rule).all()}
    items = []
    for key, (default, vtype, label, category, desc) in DEFAULT_RULES.items():
        row = overrides.get(key)
        items.append({
            "key": key,
            "value": default,
            "value_type": vtype,
            "label": label,
            "category": category,
            "description": desc,
            "customized": False,
            **({"id": row.id, "customized": True,
                "value": crud.serialize_rule(row)["value"]} if row else {}),
        })
    # 数据库中自定义的额外规则
    for key, row in overrides.items():
        if key not in DEFAULT_RULES:
            payload = crud.serialize_rule(row)
            payload["customized"] = True
            items.append(payload)
    return {"total": len(items), "items": items}


@router.put("/{key}")
def upsert_rule(key: str, data: schemas.RuleUpdate, db: Session = Depends(get_db)):
    if key not in DEFAULT_RULES:
        raise HTTPException(404, f"未知规则项：{key}")
    row = db.query(models.Rule).filter_by(key=key).first()
    if not row:
        import json
        default, vtype, label, category, desc = DEFAULT_RULES[key]
        row = models.Rule(
            key=key,
            value=json.dumps(data.value, ensure_ascii=False),
            value_type=vtype,
            label=label,
            category=category,
            description=desc,
        )
        db.add(row)
        db.flush()
    return crud.update_rule(db, row, data)


@router.delete("/{key}")
def reset_rule(key: str, db: Session = Depends(get_db)):
    """删除自定义值，恢复默认。"""
    row = db.query(models.Rule).filter_by(key=key).first()
    if not row:
        raise HTTPException(404, "该规则当前为默认值，无需重置")
    db.delete(row)
    db.commit()
    return {"detail": f"规则 {key} 已恢复默认"}

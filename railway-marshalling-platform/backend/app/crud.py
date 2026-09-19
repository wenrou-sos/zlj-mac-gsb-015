"""通用 CRUD 辅助。"""
import json
from typing import Any

from sqlalchemy.orm import Session

from . import models, schemas

MODEL_BY_NAME = {
    "track": models.Track,
    "locomotive": models.Locomotive,
}


def _rule_value_type(value: Any) -> str:
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        return "number"
    return "string"


def create_rule(db: Session, data: schemas.RuleCreate) -> models.Rule:
    vt = _rule_value_type(data.value)
    existing = db.query(models.Rule).filter_by(key=data.key).first()
    if existing:
        existing.value = json.dumps(data.value, ensure_ascii=False)
        existing.value_type = vt
        existing.label = data.label or existing.label
        existing.category = data.category or existing.category
        if data.description:
            existing.description = data.description
        db.commit()
        db.refresh(existing)
        return existing

    default = models_detector_default(data.key)
    rule = models.Rule(
        key=data.key,
        value=json.dumps(data.value, ensure_ascii=False),
        value_type=vt,
        label=data.label or default[2],
        category=data.category or default[3],
        description=data.description or default[4],
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


def models_detector_default(key: str) -> tuple:
    from .detector import DEFAULT_RULES
    return DEFAULT_RULES.get(key, (None, "string", key, "custom", ""))


def update_rule(db: Session, rule: models.Rule, data: schemas.RuleUpdate) -> models.Rule:
    rule.value = json.dumps(data.value, ensure_ascii=False)
    rule.value_type = _rule_value_type(data.value)
    for field in ("label", "category", "description"):
        val = getattr(data, field)
        if val is not None:
            setattr(rule, field, val)
    db.commit()
    db.refresh(rule)
    return rule


def serialize_rule(rule: models.Rule) -> dict:
    try:
        value = json.loads(rule.value)
    except (json.JSONDecodeError, TypeError):
        value = rule.value
    return {
        "id": rule.id,
        "key": rule.key,
        "value": value,
        "value_type": rule.value_type,
        "label": rule.label,
        "category": rule.category,
        "description": rule.description,
    }

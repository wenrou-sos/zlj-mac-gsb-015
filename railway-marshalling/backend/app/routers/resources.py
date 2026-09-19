"""股道、机车、编组规则、货列的 CRUD 路由。"""
from .. import models, schemas
from .crud import make_crud_router

tracks_router = make_crud_router(
    model=models.Track,
    create_schema=schemas.TrackCreate,
    update_schema=schemas.TrackUpdate,
    prefix="/tracks",
    tag="股道",
)

locomotives_router = make_crud_router(
    model=models.Locomotive,
    create_schema=schemas.LocomotiveCreate,
    update_schema=schemas.LocomotiveUpdate,
    prefix="/locomotives",
    tag="机车",
)

rules_router = make_crud_router(
    model=models.MarshallingRule,
    create_schema=schemas.RuleCreate,
    update_schema=schemas.RuleUpdate,
    prefix="/rules",
    tag="编组规则",
)

trains_router = make_crud_router(
    model=models.Train,
    create_schema=schemas.TrainCreate,
    update_schema=schemas.TrainUpdate,
    prefix="/trains",
    tag="货列",
)

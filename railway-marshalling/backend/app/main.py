"""FastAPI 应用入口。"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, SessionLocal, engine
from .routers.analysis import router as analysis_router
from .routers.resources import locomotives_router, rules_router, tracks_router, trains_router
from .seed import seed_if_empty


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_if_empty(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="铁路货运编组冲突分析平台",
    description="货列到发、股道、机车与编组规则管理及冲突自动检测",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tracks_router, prefix="/api")
app.include_router(locomotives_router, prefix="/api")
app.include_router(rules_router, prefix="/api")
app.include_router(trains_router, prefix="/api")
app.include_router(analysis_router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok"}

"""FastAPI 应用入口。

启动时：等待数据库可用 -> 建表 -> 空库写入演示数据。
"""
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from .config import CORS_ORIGINS
from .database import Base, SessionLocal, engine
from .routers import analysis, locomotives, rules, tracks, trains
from .seed import seed_data


def wait_for_database(max_retries: int = 30, delay: float = 2.0) -> None:
    for attempt in range(1, max_retries + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return
        except OperationalError:
            if attempt == max_retries:
                raise
            time.sleep(delay)


@asynccontextmanager
async def lifespan(app: FastAPI):
    wait_for_database()
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        created = seed_data(db)
        if created:
            print("[启动] 已写入演示数据（8 列 / 4 股道 / 3 机车）")
    finally:
        db.close()
    yield


app = FastAPI(
    title="铁路货运编组冲突分析平台",
    description="配置货列到达时间、股道长度、机车资源与编组规则，自动检测股道占用、"
                "顺序冲突与超限风险，并给出调整建议。",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_PREFIX = "/api"
app.include_router(trains.router, prefix=API_PREFIX)
app.include_router(tracks.router, prefix=API_PREFIX)
app.include_router(locomotives.router, prefix=API_PREFIX)
app.include_router(rules.router, prefix=API_PREFIX)
app.include_router(analysis.router, prefix=API_PREFIX)


@app.get("/api/health", tags=["system"])
def health():
    return {"status": "ok", "service": "railway-marshalling-platform"}

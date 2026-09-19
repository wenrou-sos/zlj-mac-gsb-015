"""数据库连接配置。

默认连接 PostgreSQL（与 docker-compose 中的 db 服务一致），
可通过环境变量 DATABASE_URL 覆盖，测试时使用 SQLite。
"""
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://railway:railway@localhost:5432/railway",
)

# SQLite 需要 check_same_thread，PostgreSQL 不需要
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

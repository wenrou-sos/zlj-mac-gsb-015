"""测试夹具：每个用例使用独立的内存 SQLite + 全新 FastAPI 客户端。"""
import os

import pytest

# 必须在导入 app 之前设置
os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"

from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.seed import seed_data  # noqa: E402


@pytest.fixture(scope="function")
def db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    seed_data(session)
    session.close()
    yield session
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    with TestClient(app) as c:  # 触发 lifespan（库非空，不会重复种子）
        yield c

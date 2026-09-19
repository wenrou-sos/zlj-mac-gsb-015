"""测试配置：使用 SQLite 内存库替代 PostgreSQL。"""
import os

os.environ["DATABASE_URL"] = "sqlite:///./test_railway.db"

import pytest
from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app


@pytest.fixture(scope="session")
def client():
    # 建库建表（lifespan 会执行种子数据写入）
    Base.metadata.drop_all(bind=engine)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)
    db_file = "./test_railway.db"
    if os.path.exists(db_file):
        os.remove(db_file)

"""应用配置：数据库连接等。

可通过环境变量 DATABASE_URL 直接覆盖（本地测试使用 SQLite，
Docker 部署使用 PostgreSQL 连接串）。
"""
import os


def get_database_url() -> str:
    url = os.getenv("DATABASE_URL", "").strip()
    if url:
        return url

    user = os.getenv("POSTGRES_USER", "railway")
    password = os.getenv("POSTGRES_PASSWORD", "railway")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "railway")
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"


DATABASE_URL = get_database_url()

# 跨域配置（本地前端 Vite 开发服务器）
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173",
).split(",")

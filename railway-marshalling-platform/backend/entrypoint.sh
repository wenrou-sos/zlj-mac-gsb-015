#!/bin/sh
# 容器入口：等待 PostgreSQL 就绪 -> 建表/种子 -> 启动 API
set -e

echo "[entrypoint] 启动 FastAPI 服务（应用内会等待数据库并初始化）..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000

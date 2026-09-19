#!/usr/bin/env bash
# 铁路货运编组冲突分析平台 —— 一键启动脚本
#
# 用法：
#   ./start.sh          Docker 模式（推荐）：构建并启动 PostgreSQL + 后端 + 前端
#   ./start.sh --dev    本地开发模式：SQLite + uvicorn 热重载 + Vite 开发服务器
#   ./start.sh --test   运行后端 pytest 与前端 vitest 测试
#   ./start.sh --stop   停止 Docker 模式的所有服务
set -euo pipefail
cd "$(dirname "$0")"

MODE="${1:-docker}"

case "$MODE" in
  --dev)
    echo "==> 本地开发模式"
    cd backend
    if [ ! -d .venv ]; then
      python3 -m venv .venv 2>/dev/null || python3 -m virtualenv .venv
    fi
    ./.venv/bin/pip install -q -r requirements.txt
    # 未显式指定 DATABASE_URL 时使用 SQLite，便于零依赖本地运行；
    # 如需 PostgreSQL：export DATABASE_URL=postgresql+psycopg2://railway:railway@localhost:5432/railway
    export DATABASE_URL="${DATABASE_URL:-sqlite:///./railway_dev.db}"
    ./.venv/bin/uvicorn app.main:app --reload --port 8000 &
    BACKEND_PID=$!
    cd ../frontend
    [ -d node_modules ] || npm install
    npm run dev &
    FRONTEND_PID=$!
    trap 'kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true' EXIT
    echo "==> 后端 http://localhost:8000/docs ｜ 前端 http://localhost:3000"
    wait
    ;;

  --test)
    echo "==> 运行后端测试"
    cd backend
    if [ ! -d .venv ]; then
      python3 -m venv .venv 2>/dev/null || python3 -m virtualenv .venv
      ./.venv/bin/pip install -q -r requirements.txt
    fi
    ./.venv/bin/python -m pytest tests/ -q
    cd ../frontend
    [ -d node_modules ] || npm install
    echo "==> 运行前端测试"
    npm test
    ;;

  --stop)
    docker compose down
    ;;

  docker|*)
    if ! command -v docker >/dev/null 2>&1; then
      echo "未检测到 Docker，请安装 Docker 或改用本地模式：./start.sh --dev" >&2
      exit 1
    fi
    echo "==> 构建并启动全部服务（PostgreSQL + FastAPI + React/Nginx）"
    docker compose up --build -d
    echo ""
    echo "==> 启动完成："
    echo "    前端界面   http://localhost:3000"
    echo "    后端 API   http://localhost:8000/docs"
    echo "    停止服务   ./start.sh --stop"
    ;;
esac

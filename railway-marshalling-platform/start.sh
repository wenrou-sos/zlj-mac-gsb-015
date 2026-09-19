#!/usr/bin/env bash
# 铁路货运编组冲突分析平台 - 一键管理脚本
#
# 用法:
#   ./start.sh up        构建并启动全部服务（PostgreSQL + FastAPI + React/Nginx）
#   ./start.sh down      停止并移除容器
#   ./start.sh restart   重启服务
#   ./start.sh logs      查看全部服务日志（-f 跟踪）
#   ./start.sh status    查看服务状态
#   ./start.sh rebuild   不使用缓存重新构建并启动
#   ./start.sh test      运行后端 pytest 测试（本地 Python 环境，不依赖 Docker）
#   ./start.sh dev       本地开发模式（SQLite + uvicorn + vite，无需 Docker）
#   ./start.sh smoke     启动后冒烟测试（健康检查 + 分析接口）
set -euo pipefail

cd "$(dirname "$0")"

BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-8080}"

find_compose() {
  if docker compose version >/dev/null 2>&1; then
    echo "docker compose"
  elif command -v docker-compose >/dev/null 2>&1; then
    echo "docker-compose"
  else
    echo ""
  fi
}

ensure_env() {
  if [ ! -f .env ]; then
    cp .env.example .env
    echo "[start.sh] 已从 .env.example 创建 .env"
  fi
}

wait_health() {
  echo "[start.sh] 等待后端健康检查..."
  for i in $(seq 1 60); do
    if curl -fsS "http://localhost:${BACKEND_PORT}/api/health" >/dev/null 2>&1; then
      echo "[start.sh] ✅ 后端就绪"
      return 0
    fi
    sleep 2
  done
  echo "[start.sh] ❌ 后端健康检查超时，请查看日志：$0 logs"
  exit 1
}

cmd_up() {
  ensure_env
  local dc; dc="$(find_compose)"
  if [ -z "$dc" ]; then
    echo "未检测到 Docker / Docker Compose，请先安装 Docker Desktop 或 Docker Engine。"
    echo "也可以使用本地开发模式：./start.sh dev"
    exit 1
  fi
  echo "[start.sh] 构建并启动服务..."
  $dc up -d --build
  wait_health
  echo ""
  echo "============================================================"
  echo "  🚦 铁路货运编组冲突分析平台已启动"
  echo "  前端页面:  http://localhost:${FRONTEND_PORT}"
  echo "  API 文档:  http://localhost:${BACKEND_PORT}/docs"
  echo "  健康检查:  http://localhost:${BACKEND_PORT}/api/health"
  echo "  PostgreSQL 端口见 .env（默认 5432），首启自动写入演示数据"
  echo "============================================================"
}

cmd_down() {
  local dc; dc="$(find_compose)"
  [ -z "$dc" ] && { echo "Docker Compose 不可用"; exit 1; }
  $dc down
  echo "[start.sh] 服务已停止（数据卷保留，加 -v 参数可手动清除：docker compose down -v）"
}

cmd_logs() {
  local dc; dc="$(find_compose)"
  $dc logs -f --tail=200
}

cmd_status() {
  local dc; dc="$(find_compose)"
  $dc ps
}

cmd_rebuild() {
  ensure_env
  local dc; dc="$(find_compose)"
  $dc build --no-cache
  $dc up -d
  wait_health
}

cmd_smoke() {
  echo "== 健康检查 =="
  curl -fsS "http://localhost:${BACKEND_PORT}/api/health" && echo
  echo "== 冲突分析（统计摘要）=="
  curl -fsS "http://localhost:${BACKEND_PORT}/api/analysis" \
    | python3 -c "import json,sys; d=json.load(sys.stdin); print('货列:',d['train_count'],'股道:',d['track_count'],'机车:',d['locomotive_count']); print('冲突统计:', d['summary'])"
  echo "== 前端页面 =="
  curl -fsS "http://localhost:${FRONTEND_PORT}/" -o /dev/null -w "HTTP %{http_code}\n"
  echo "✅ 冒烟测试通过"
}

cmd_test() {
  cd backend
  if [ ! -d ".venv" ]; then
    python3 -m venv .venv
  fi
  . .venv/bin/activate
  pip install -q -r requirements.txt
  DATABASE_URL="sqlite+pysqlite:///:memory:" python -m pytest -v
  cd ..
}

cmd_dev() {
  echo "[start.sh] 本地开发模式（SQLite，无需 Docker / PostgreSQL）"
  ensure_env
  cd backend
  python3 -m uvicorn app.main:app --reload --port "${BACKEND_PORT}" &
  API_PID=$!
  cd ../frontend
  if [ ! -d node_modules ]; then
    npm install
  fi
  VITE_API_TARGET="http://localhost:${BACKEND_PORT}" npm run dev &
  WEB_PID=$!
  trap "kill $API_PID $WEB_PID 2>/dev/null || true" EXIT INT TERM
  echo "开发服务运行中：前端 http://localhost:5173 ，API http://localhost:${BACKEND_PORT}/docs"
  wait
}

case "${1:-up}" in
  up) cmd_up ;;
  down) cmd_down ;;
  restart) cmd_down; cmd_up ;;
  logs) cmd_logs ;;
  status) cmd_status ;;
  rebuild) cmd_rebuild ;;
  smoke) cmd_smoke ;;
  test) cmd_test ;;
  dev) cmd_dev ;;
  *)
    echo "用法: $0 {up|down|restart|logs|status|rebuild|smoke|test|dev}"
    exit 1
    ;;
esac

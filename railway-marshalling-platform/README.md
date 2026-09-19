# 铁路货运编组冲突分析平台

面向铁路货运编组站（驼峰/牵出线车间）的班计划校核工具：可配置 **货列到达时间、股道长度、机车资源与编组规则**，自动检查 **股道占用、编组顺序冲突与超限风险**，并对每个问题给出可一键采纳的调整建议。

## 功能特性

### 可配置项
- **货列到达计划**：车次、类型（普通 / 危险品 / 超限重载）、到达与发车时间、车列长度与总重、货物最大宽高、指派股道/机车、编组序号
- **股道资源**：有效长度、现存车辆占用长度、允许载重、危险品 / 超限接车条件
- **机车资源**：型号功率、检修状态、当班可用时间窗
- **编组规则**：安全间隔分钟数、长度预警余量比例、机车车辆限界宽高、机车备用比例，以及各检查项开关，可恢复默认

### 自动检查（12 类冲突，高 / 中 / 低三级）
| 代码 | 检查项 | 风险 |
|---|---|---|
| C01 | 同一股道作业时间窗重叠（股道占用冲突） | 高 |
| C02 | 车列长度 + 现存占用超过股道有效长度 | 高 |
| C03 | 货列总重超过股道允许载重 | 高 |
| C04 | 危险品 / 超限列车进入不具备条件的股道 | 高 |
| C05 | 货物宽高超过机车车辆限界（超限风险） | 中 |
| C06 | 同股道相邻车间隔小于安全间隔 | 中 |
| C07 | 编组序号与到达顺序不一致（调车钩冲突） | 中 |
| C08 | 同一机车被同时/连续指派且间隔不足 | 高/中 |
| C09 | 并行作业峰值超过可用机车数（资源缺口） | 高 |
| C10 | 货列未分配股道 / 未指派机车 | 低 |
| C11 | 机车检修中或可用时间窗不覆盖作业时段 | 高/中 |
| C12 | 股道接入后利用率接近上限 | 低 |

### 调整建议
每条冲突附带结构化建议（改派股道、更换机车、延后到达时间、修正编组序号、人工复核），在前端点击 **采纳** 即可回写并重新分析。

### 可视化
- 甘特式班计划时间轴：股道 / 机车双泳道，色块按该货列最高冲突等级着色
- 概览统计卡片与股道利用率条形图
- 冲突清单按严重程度排序，标注关联货列、股道、机车

## 技术栈

- **前端**：React 18 + Vite + 原生 CSS（Nginx 托管并反代 API）
- **后端**：FastAPI + SQLAlchemy 2 + Pydantic v2
- **数据库**：PostgreSQL 16（测试与本地开发可使用 SQLite，无需额外依赖）
- **部署**：Docker Compose 三容器编排（db / backend / frontend）

## 快速开始

### 方式一：Docker 一键启动（推荐）

```bash
./start.sh up
```

启动后：
- 前端平台：<http://localhost:8080>
- API 文档（Swagger）：<http://localhost:8000/docs>
- 首次启动自动建表并写入演示数据（8 列 / 4 股道 / 3 机车，含预置冲突）

端口可在 `.env` 中调整（`FRONTEND_PORT` / `BACKEND_PORT` / `POSTGRES_PORT`）。

其他命令：

```bash
./start.sh status    # 查看服务状态
./start.sh logs      # 跟踪日志
./start.sh smoke     # 冒烟测试（健康检查 + 分析接口 + 前端页面）
./start.sh restart   # 重启
./start.sh down      # 停止（保留数据卷）
./start.sh rebuild   # 无缓存重建
```

或直接使用 Docker Compose：

```bash
cp .env.example .env
docker compose up -d --build
```

### 方式二：本地开发模式（无需 Docker，使用 SQLite）

```bash
./start.sh dev
```

脚本会分别启动 `uvicorn --reload`（:8000）和 Vite 开发服务器（:5173，自动代理 `/api`）。

手动启动：

```bash
# 后端
cd backend
pip install -r requirements.txt
DATABASE_URL="sqlite+pysqlite:///./dev.db" uvicorn app.main:app --reload

# 前端
cd frontend
npm install
npm run dev
```

### 连接已有 PostgreSQL

设置环境变量后启动后端即可（也支持直接给完整连接串）：

```bash
export DATABASE_URL="postgresql+psycopg2://user:pass@host:5432/dbname"
uvicorn app.main:app
```

## 测试

```bash
./start.sh test
```

或手动执行：

```bash
cd backend
pip install -r requirements.txt
DATABASE_URL="sqlite+pysqlite:///:memory:" python -m pytest -v
```

测试覆盖（16 个用例）：

- `test_startup.py`：应用启动、健康检查、Swagger 文档、演示数据初始化
- `test_api.py`：货列/股道/机车 CRUD、参数校验（发车早于到达、引用不存在的股道）、
  规则更新与重置、**端到端"采纳建议消除冲突"流程**
- `test_detector.py`：12 类冲突的检测、建议完整性、规则改动生效、合规零冲突、危货进普通线

## API 概览

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/health` | 健康检查 |
| GET | `/api/analysis` | 执行冲突分析，返回冲突、建议、统计与时间轴边界 |
| GET/POST/PUT/DELETE | `/api/trains` | 货列计划 |
| GET/POST/PUT/DELETE | `/api/tracks` | 股道资源 |
| GET/POST/PUT/DELETE | `/api/locomotives` | 机车资源 |
| GET/PUT/DELETE | `/api/rules/{key}` | 规则查看 / 更新 / 恢复默认 |

完整交互模型见 <http://localhost:8000/docs>。

## 项目结构

```
railway-marshalling-platform/
├── docker-compose.yml        # PostgreSQL + FastAPI + Nginx/React 编排
├── start.sh                  # 一键启动 / 停止 / 测试 / 开发
├── .env.example
├── backend/
│   ├── Dockerfile
│   ├── entrypoint.sh
│   ├── requirements.txt
│   ├── pytest.ini
│   ├── app/
│   │   ├── main.py           # FastAPI 入口（建库重试、建表、种子）
│   │   ├── config.py         # 数据库/CORS 配置
│   │   ├── database.py       # 引擎与会话（SQLite/PostgreSQL 自适应）
│   │   ├── models.py         # Train / Track / Locomotive / Rule
│   │   ├── schemas.py        # Pydantic 模型
│   │   ├── detector.py       # ★ 冲突检测引擎（纯函数，12 类检查）
│   │   ├── crud.py
│   │   ├── seed.py           # 演示数据
│   │   └── routers/          # trains / tracks / locomotives / rules / analysis
│   └── tests/
└── frontend/
    ├── Dockerfile            # 多阶段构建：node 编译 + nginx 托管
    ├── nginx.conf
    └── src/
        ├── App.jsx
        ├── api.js
        └── components/       # Timeline / ConflictPanel / 各配置面板
```

## 说明

- 所有时间按本地时间处理（前端 `datetime-local`，后端 naive datetime），跨时区部署时请保证容器时区一致。
- 检测引擎为无状态计算：修改任意配置后重新请求 `/api/analysis` 即得到最新结果，冲突结果不落库。
- 演示数据仅在数据库为空时自动写入；清空数据后重启服务会重新初始化。

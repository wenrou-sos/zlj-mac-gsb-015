# 铁路货运编组冲突分析平台

可配置货列到达时间、股道长度、机车资源与编组规则，自动检测**股道占用冲突、顺序冲突、超限风险、机车冲突**，并针对每项冲突给出调整建议。

## 技术栈

| 层 | 技术 |
|----|------|
| 前端 | React 18 + Vite + React Router（Nginx 托管） |
| 后端 | FastAPI + SQLAlchemy 2.0 |
| 数据库 | PostgreSQL 16（本地开发可回退 SQLite） |
| 测试 | pytest（后端 20 例）+ Vitest（前端 5 例） |
| 部署 | Docker Compose 一键编排 |

## 快速开始

```bash
# Docker 模式（推荐）：PostgreSQL + 后端 + 前端整体启动
./start.sh
# 前端 http://localhost:3000 ｜ API 文档 http://localhost:8000/docs

# 本地开发模式（无需 Docker，默认 SQLite 零依赖运行）
./start.sh --dev

# 运行全部测试
./start.sh --test

# 停止 Docker 服务
./start.sh --stop
```

首次启动自动建表并写入示例数据（含故意构造的冲突场景，便于演示检测效果）。

## 功能说明

### 资源管理（前端四个管理页 + RESTful CRUD API）
- **货列管理**：车次、到达/出发时间、编组辆数、长度、总重、货物类型、优先级、所在股道、牵引机车
- **股道管理**：股道名称、有效长度、类型（到发线/调车线/存车线）、状态
- **机车资源**：编号、机型、最大牵引重量、状态、可用时间窗
- **编组规则**：最大辆数/长度/重量、同股道最小出发间隔、最大停留时间，支持启停

### 冲突检测引擎（`backend/app/conflict_engine.py`，纯函数实现）
| 类型 | 检测内容 | 建议示例 |
|------|----------|----------|
| 股道占用冲突 | 同股道列车时间窗重叠 | 推荐长度足够且空闲的替代股道，或调整时刻 |
| 顺序冲突 | 后到先发"堵门"；出发间隔小于规则下限 | 提前先到列车出发 / 调换股道 / 推迟出发 |
| 超限风险 | 列车超股道有效长；辆数/长度/重量超规则；停留超时 | 更换长股道、拆分编组、减挂、转存车线 |
| 机车冲突 | 牵引超重、机车检修中、可用时间不匹配、连续任务整备不足 | 推荐能力足够的可用机车、双机牵引 |

分析结果按严重程度（高/中/低）排序，持久化到 `analysis_runs` 表，可查询历史。

### 仪表盘
- 四类冲突统计卡片
- **股道占用甘特图**：按股道展示各列车占用时间窗，涉冲突列车标红
- 冲突明细卡片：每条冲突附带具体调整建议

## API 概览

```
GET/POST/PUT/DELETE  /api/tracks         股道
GET/POST/PUT/DELETE  /api/locomotives    机车
GET/POST/PUT/DELETE  /api/rules          编组规则
GET/POST/PUT/DELETE  /api/trains         货列
POST                 /api/analysis/run   运行冲突分析
GET                  /api/analysis/latest 最近一次结果
GET                  /api/analysis/runs   历史记录
GET                  /api/health          健康检查
```

交互式文档：启动后访问 `http://localhost:8000/docs`。

## 项目结构

```
railway-marshalling/
├── start.sh                  # 一键启动（docker / --dev / --test / --stop）
├── docker-compose.yml        # PostgreSQL + 后端 + 前端编排
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py           # FastAPI 入口（lifespan 建表 + 种子数据）
│   │   ├── database.py       # DATABASE_URL 可配置，默认 PostgreSQL
│   │   ├── models.py         # 股道/机车/规则/货列/分析记录
│   │   ├── schemas.py        # Pydantic 模型
│   │   ├── conflict_engine.py# 冲突检测引擎（纯函数）
│   │   ├── seed.py           # 示例数据
│   │   └── routers/          # CRUD 工厂 + 分析路由
│   └── tests/                # pytest：引擎单测 + API 冒烟测试
└── frontend/
    ├── Dockerfile            # 多阶段构建：Vite build → Nginx
    ├── nginx.conf            # SPA 回退 + /api 反向代理
    └── src/
        ├── pages/            # 仪表盘 + 四个资源管理页
        ├── components/       # 通用 CRUD 表格组件
        └── utils.js          # 纯函数工具（含 Vitest 测试）
```

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DATABASE_URL` | `postgresql+psycopg2://railway:railway@localhost:5432/railway` | 后端数据库连接串；测试自动使用 SQLite |
| `VITE_API_URL` | `/api` | 前端 API 基础路径 |

## 测试

```bash
cd backend && python -m pytest tests/ -q   # 20 例：引擎单测 + API 冒烟
cd frontend && npm test                    # 5 例：工具函数单测
```

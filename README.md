# 智能学习 Agent

基于 LangGraph 的多智能体自适应学习系统。通过 Supervisor + 子智能体协作模式，为学生提供苏格拉底式的互动学习体验——讲解概念、生成测验、批改答案、追踪知识掌握度、推荐学习资源。

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | FastAPI + Uvicorn (Python 3.12) |
| 智能体编排 | LangGraph + LangChain |
| LLM | DeepSeek (兼容 OpenAI API) |
| 数据库 | PostgreSQL 16 + pgvector |
| 前端 | React 19 + TypeScript + Vite |
| 状态管理 | Zustand |
| 样式 | Tailwind CSS 4 |
| 可视化 | ECharts (知识图谱) |

## 环境要求

- **Python** ≥ 3.12
- **Node.js** ≥ 18
- **PostgreSQL** 16（需启用 pgvector 扩展）
- **Docker**（可选，用于本地启动数据库）

## 快速启动

### 1. 克隆项目

```bash
git clone <repo-url>
cd agent_learning_helper
```

### 2. 启动数据库

**方式一：Docker（推荐）**

```bash
docker compose up -d
```

**方式二：手动启动本地 PostgreSQL**

确保已安装 PostgreSQL 16 和 pgvector 扩展，然后：

```bash
python scripts/init_db.py
```

### 3. 配置环境变量

复制模板并填入你的 API Key：

```bash
cp .env.example .env
```

编辑 `.env`，至少需要填写：

```env
# DeepSeek API Key（必填）
OPENAI_API_KEY=sk-your-deepseek-key

# Tavily Search API Key（必填，用于联网检索）
TAVILY_API_KEY=tvly-your-tavily-key

# 数据库连接（如果使用 Docker 本地启动，使用以下配置）
DATABASE_URL=postgresql+asyncpg://agent:agent123@localhost:5432/agent_learning
DATABASE_URL_SYNC=postgresql+psycopg2://agent:agent123@localhost:5432/agent_learning
```

完整的环境变量说明：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `OPENAI_API_KEY` | DeepSeek API 密钥（必填） | — |
| `OPENAI_BASE_URL` | API 基础地址 | `https://api.deepseek.com` |
| `SUPERVISOR_MODEL` | 路由/调度模型 | `deepseek-v4-pro` |
| `EXPLAINER_MODEL` | 讲解模型 | `deepseek-v4-flash` |
| `QUIZZER_MODEL` | 出题模型 | `deepseek-v4-pro` |
| `CHECKER_MODEL` | 批改模型 | `deepseek-v4-flash` |
| `RECOMMENDER_MODEL` | 推荐模型 | `deepseek-v4-flash` |
| `EMBEDDING_MODEL` | 向量嵌入模型 | `text-embedding-3-small` |
| `DATABASE_URL` | 异步数据库连接 | — |
| `DATABASE_URL_SYNC` | 同步数据库连接（迁移用） | — |
| `TAVILY_API_KEY` | Tavily 搜索 API 密钥（必填） | — |
| `APP_HOST` | 服务监听地址 | `0.0.0.0` |
| `APP_PORT` | 服务端口 | `8000` |
| `LOG_LEVEL` | 日志级别 | `INFO` |
| `CORS_ORIGINS` | 前端跨域来源 | `http://localhost:5173` |

### 4. 数据库迁移

```bash
alembic upgrade head
```

### 5. 安装后端依赖

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 6. 安装前端依赖

```bash
cd frontend
npm install
```

### 7. 启动服务

**启动后端：**

```bash
# 项目根目录
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**启动前端：**

```bash
cd frontend
npm run dev
```

启动后访问 [http://localhost:5173](http://localhost:5173) 即可使用。

## 项目结构

```
agent_learning_helper/
├── app/                        # 后端 (FastAPI)
│   ├── api/                    # API 路由、中间件、依赖注入
│   │   └── routes/             # chat (SSE 流式), sessions (CRUD), health
│   ├── core/                   # 核心业务逻辑
│   │   ├── agents/             # 智能体实现（讲解、出题、批改、推荐）
│   │   ├── graph/              # LangGraph 状态图（构建器、Supervisor、节点）
│   │   ├── prompts/            # 提示词模板
│   │   ├── state.py            # AgentState 定义
│   │   └── tools/              # LangChain 工具（搜索、RAG、知识图谱）
│   ├── db/                     # 数据访问层（连接池、仓库、向量存储）
│   ├── models/                 # Pydantic 数据模型
│   ├── streaming/              # SSE 流式响应处理
│   └── utils/                  # 日志、异常
├── frontend/                   # 前端 (React + Vite)
│   └── src/
│       ├── api/                # API 客户端（SSE、REST）
│       ├── components/         # UI 组件
│       ├── hooks/              # 自定义 Hook
│       └── store/              # Zustand 状态管理
├── scripts/                    # 工具脚本
├── tests/                      # 测试
├── docker-compose.yml          # PostgreSQL + pgvector
├── requirements.txt            # Python 依赖
├── alembic.ini                 # 数据库迁移配置
└── .env.example                # 环境变量模板
```

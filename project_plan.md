# 智能学习 Agent 项目整体架构规划

> 本文档基于 `function.md`（功能需求）与 `technology.md`（技术栈规范），对项目进行从零到一的完整架构设计。  
> **核心设计原则**：管理层与执行层分离、异步优先、状态幂等、一库多用。

---

## 一、总体架构层次

项目采用 **前后端分离 + 后端四层架构**：

```
┌──────────────────────────────────────────────────┐
│                  前端 (frontend/)                  │  ← React 18 + Vite + Zustand
│            SSE 消费、聊天 UI、知识图谱可视化          │
└──────────────────────┬───────────────────────────┘
                       │ SSE (POST /chat/{session_id}/stream)
                       │ REST (GET/POST/DELETE /sessions)
┌──────────────────────▼───────────────────────────┐
│              API 层 (api/)                        │  ← HTTP 请求/响应、SSE 流
│              FastAPI Router + Middleware           │
├──────────────────────────────────────────────────┤
│              核心业务层 (core/)                     │  ← Agent 逻辑、图编排、工具调用
│        LangGraph Supervisor → Nodes → Tools        │
├──────────────────────────────────────────────────┤
│              数据访问层 (db/)                       │  ← Repository + Vector Store
│         PostgreSQL (业务表 + Checkpoint + Vector)  │
├──────────────────────────────────────────────────┤
│              基础设施层 (utils/ + 外部)              │  ← 配置、日志、LLM Provider、Search API
│         Config / Logging / LLM Client / Tavily     │
└──────────────────────────────────────────────────┘
```

**关键约束**：
- 上层可以调用下层，下层**绝不**引用上层。
- 核心业务层不接触 `Request`/`Response` 对象——它只操作 `AgentState` 和领域模型。
- 数据访问层不包含任何业务逻辑，只做 CRUD 和查询。
- 前端与后端通过 SSE + REST 通信，前后端共享 TypeScript/Pydantic 类型定义（手动镜像）。

---

## 二、完整目录结构

```
agent_learning_helper/
│
├── app/                              # 应用主包
│   ├── __init__.py
│   ├── main.py                       # FastAPI 应用入口、生命周期管理
│   ├── config.py                     # 全局配置（Pydantic Settings，读 .env）
│   │
│   ├── api/                          # ─── API 层 ───
│   │   ├── __init__.py
│   │   ├── dependencies.py           # FastAPI Depends（DB Session、Graph 实例注入）
│   │   ├── middleware.py             # CORS、请求日志、异常处理中间件
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── chat.py               # POST /chat/{session_id}/stream  ← SSE 聊天流
│   │       ├── sessions.py           # CRUD /sessions                   ← 学习会话管理
│   │       └── health.py             # GET /health                      ← 健康检查
│   │
│   ├── core/                         # ─── 核心业务层 ───
│   │   ├── __init__.py
│   │   │
│   │   ├── state.py                  # ★ AgentState 全局状态定义（Pydantic v2）
│   │   │                              #   包含：messages, knowledge_map, error_notebook,
│   │   │                              #        learning_goal, progress, current_phase
│   │   │
│   │   ├── graph/                    # LangGraph 图编排
│   │   │   ├── __init__.py
│   │   │   ├── supervisor.py         # ★ Supervisor 路由节点（总控大脑）
│   │   │   ├── builder.py            # 图构建 & compile（含 checkpointer 绑定）
│   │   │   └── nodes/                # 各个子 Agent 节点实现
│   │   │       ├── __init__.py
│   │   │       ├── explainer.py      # 解惑 Agent 节点
│   │   │       ├── quizzer.py        # 出题 Agent 节点
│   │   │       ├── check_answer.py   # 批改 & 反馈节点
│   │   │       └── recommender.py    # 推荐 Agent 节点
│   │   │
│   │   ├── agents/                   # Agent 实现细节（Prompt + LLM 调用）
│   │   │   ├── __init__.py
│   │   │   ├── base.py               # Agent 基类（统一 LLM 绑定、流式回调）
│   │   │   ├── explainer.py          # 解惑 Agent：RAG 检索 + 知识讲解
│   │   │   ├── quizzer.py            # 出题 Agent：结构化 JSON 输出
│   │   │   ├── checker.py            # 批改 Agent：答案判定 + 进度更新逻辑
│   │   │   └── recommender.py        # 推荐 Agent：盲点分析 + 资源搜索
│   │   │
│   │   ├── tools/                    # LangChain Tool 定义（Agent 可调用的工具）
│   │   │   ├── __init__.py
│   │   │   ├── search.py             # Tavily 联网搜索工具
│   │   │   ├── rag_retriever.py      # 本地 pgvector RAG 检索工具
│   │   │   └── knowledge_map.py      # 知识点掌握度读写工具
│   │   │
│   │   └── prompts/                  # Prompt 模板集中管理
│   │       ├── __init__.py
│   │       ├── supervisor.py         # 主管路由 Prompt
│   │       ├── explainer.py          # 解惑 Prompt
│   │       ├── quizzer.py            # 出题 Prompt（含 few-shot 示例）
│   │       ├── checker.py            # 批改 Prompt
│   │       └── recommender.py        # 推荐 Prompt
│   │
│   ├── models/                       # ─── Pydantic 模型 / Schema ───
│   │   ├── __init__.py
│   │   ├── session.py                # Session 创建/响应 Schema
│   │   ├── chat.py                   # ChatMessage 请求/响应 Schema
│   │   ├── quiz.py                   # QuizCard（题干+选项+解析）结构化 Schema
│   │   ├── knowledge.py              # KnowledgeMap 条目 Schema
│   │   └── recommendation.py         # ResourceCard（标题+链接+简介）Schema
│   │
│   ├── db/                           # ─── 数据访问层 ───
│   │   ├── __init__.py
│   │   ├── connection.py             # asyncpg 连接池管理 & Session 工厂
│   │   ├── migrations/               # Alembic 数据库迁移脚本
│   │   │   ├── env.py
│   │   │   └── versions/
│   │   │       └── 001_initial.py    # 初始表结构
│   │   ├── repositories/             # 关系型数据访问（Repository Pattern）
│   │   │   ├── __init__.py
│   │   │   ├── base.py               # 基础 Repository（通用 CRUD）
│   │   │   ├── session_repo.py       # 学习会话表
│   │   │   ├── knowledge_repo.py     # 知识点掌握度表
│   │   │   ├── error_repo.py         # 错题本表
│   │   │   └── user_repo.py          # 用户表
│   │   └── vector/                   # 向量存储操作
│   │       ├── __init__.py
│   │       ├── embedding.py          # Embedding 模型封装（text-embedding-3-small）
│   │       ├── store.py              # pgvector 增删查（cosine 相似度检索）
│   │       └── loader.py             # PDF/文档加载 → 分块 → 入库管道
│   │
│   ├── streaming/                    # ─── SSE 流式输出层 ───
│   │   ├── __init__.py
│   │   ├── filters.py                # LangGraph astream_events 事件过滤器
│   │   │                              #   只透传 explainer 的 on_chat_model_stream
│   │   └── formatters.py             # SSE 格式编码（"data: {...}\n\n"）
│   │
│   └── utils/                        # ─── 通用工具 ───
│       ├── __init__.py
│       ├── logging_config.py         # 结构化日志配置
│       └── exceptions.py             # 自定义异常类（AppException 体系）
│
├── frontend/                         # ─── 前端 ───
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   │
│   ├── src/
│   │   ├── main.tsx                  # 入口，挂载 App
│   │   ├── App.tsx                   # 路由根组件
│   │   │
│   │   ├── api/                      # 后端通信层
│   │   │   ├── client.ts             # fetch-event-source 封装（POST + SSE 解析）
│   │   │   ├── sessions.ts           # 会话 CRUD REST 调用
│   │   │   └── types.ts              # ★ 从后端 Pydantic models 镜像的 TS 接口
│   │   │
│   │   ├── store/                    # Zustand 状态管理
│   │   │   ├── chatStore.ts          # ★ 核心 store：消息、SSE、阶段、进度
│   │   │   └── sessionStore.ts       # 会话列表 store
│   │   │
│   │   ├── components/               # UI 组件
│   │   │   ├── chat/
│   │   │   │   ├── ChatPanel.tsx     # 聊天面板（消息列表 + 输入框）
│   │   │   │   ├── MessageBubble.tsx # 消息气泡（支持 Markdown 渲染）
│   │   │   │   ├── StreamingText.tsx # 流式文本追加动画
│   │   │   │   └── ChatInput.tsx     # 底部输入框 + 发送按钮
│   │   │   ├── quiz/
│   │   │   │   ├── QuizCard.tsx      # 题目卡片（题干 + 选项列表）
│   │   │   │   ├── QuizOption.tsx    # 单个选项按钮
│   │   │   │   └── CheckResult.tsx   # 批改结果展示（对错 + 解析）
│   │   │   ├── knowledge/
│   │   │   │   ├── KnowledgeGraph.tsx# 知识点掌握度关系图（ECharts）
│   │   │   │   └── ProgressBar.tsx   # 总体进度条（Recharts）
│   │   │   ├── recommendation/
│   │   │   │   └── ResourceCard.tsx  # 资源卡片（标题 + 链接 + 简介）
│   │   │   ├── session/
│   │   │   │   ├── SessionList.tsx   # 侧边栏会话列表
│   │   │   │   └── SessionCreate.tsx # 新建会话表单（输入学习目标）
│   │   │   └── common/
│   │   │       ├── ErrorBanner.tsx   # 顶部错误提示条
│   │   │       ├── PhaseIndicator.tsx# 当前阶段指示器
│   │   │       └── LoadingDots.tsx   # LLM 思考中动画
│   │   │
│   │   └── hooks/
│   │       ├── useSSE.ts             # SSE 连接管理
│   │       └── useAutoScroll.ts      # 消息列表自动滚底
│   │
│   └── public/
│       └── favicon.ico
│
├── tests/                            # 测试目录（与 app/ 结构镜像）
│   ├── __init__.py
│   ├── conftest.py                   # pytest fixtures（测试 DB、Mock LLM）
│   ├── test_core/
│   │   ├── test_state.py             # AgentState 状态更新幂等性测试
│   │   ├── test_graph/
│   │   │   ├── test_supervisor.py    # Supervisor 路由决策测试
│   │   │   ├── test_explainer.py     # 解惑节点测试
│   │   │   ├── test_quizzer.py       # 出题节点结构化输出测试
│   │   │   ├── test_checker.py       # 批改节点测试
│   │   │   └── test_recommender.py   # 推荐节点测试
│   │   └── test_tools.py             # 工具调用测试
│   ├── test_api/
│   │   ├── test_chat.py              # SSE 流端点测试
│   │   └── test_sessions.py          # 会话 CRUD 端点测试
│   └── test_db/
│       ├── test_repositories.py      # Repository 集成测试
│       └── test_vector.py            # pgvector 检索精度测试
│
├── scripts/                          # 运维脚本
│   ├── init_db.py                    # 数据库初始化（建表 + 启 pgvector 扩展）
│   ├── seed_knowledge.py             # 知识库种子数据导入
│   └── migrate.py                    # 迁移快捷命令
│
├── .env.example                      # 环境变量模板
├── requirements.txt                  # ★ 锁死版本的依赖清单
├── alembic.ini                       # Alembic 配置
├── docker-compose.yml                # PostgreSQL 16 + pgvector 一键启动
├── Dockerfile                        # 应用容器化
└── README.md                         # 项目说明
```

---

## 三、各目录职责详解

### 3.1 `app/main.py` — 应用入口
- 创建 FastAPI 实例
- 注册路由、中间件
- 管理生命周期事件（`startup`：初始化 DB 连接池、预编译 LangGraph 图；`shutdown`：关闭连接池）
- Graph 实例作为**单例**常驻内存，供所有请求复用

### 3.2 `app/config.py` — 全局配置
- 使用 `pydantic-settings` 的 `BaseSettings`，自动从 `.env` 加载
- 集中管理：LLM API Key、DB 连接字符串、Tavily API Key、Embedding 模型名、流式超时时间等

### 3.3 API 层 (`app/api/`)

| 文件 | 职责 |
|------|------|
| `dependencies.py` | FastAPI `Depends` 注入：获取 DB 连接、获取 Graph 实例、获取当前用户 |
| `middleware.py` | CORS 配置、全局异常捕获 → 统一错误响应 |
| `routes/chat.py` | **核心端点**。接收用户消息 → 调用 `graph.astream_events()` → `StreamingResponse` 输出 SSE |
| `routes/sessions.py` | 会话列表、创建（绑定 `thread_id` + 学习目标）、删除 |
| `routes/health.py` | 存活检测 |

### 3.4 核心业务层 (`app/core/`)

#### 3.4.1 `state.py` — 全局状态（项目灵魂）

```python
# 伪代码示意（实际用 Pydantic v2 + TypedDict + Annotated）
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]     # 对话历史（自动追加）
    thread_id: str                               # 会话隔离 ID
    learning_goal: str                           # 学习目标（创建会话时设定，不可变）
    knowledge_map: dict[str, str]                # {"知识点": "已掌握"|"未掌握"|"学习中"}
    error_notebook: Annotated[list, add]         # 错题归档（幂等追加）
    current_phase: str                           # 当前阶段：explaining/quiz/checking/recommending
    progress: float                              # 0.0 ~ 1.0 总体进度
    quiz_pending: Optional[QuizCard]             # 当前待答题目
```

**关键设计**：
- `messages` 和 `error_notebook` 使用 `Annotated[list, add]`，保证多节点并发写入时**只追加不覆盖**。
- 其余字段使用覆盖逻辑，由对应节点显式更新。

#### 3.4.2 `graph/` — LangGraph 图编排

```
        ┌──────────┐
        │  __start__ │
        └─────┬─────┘
              │
        ┌─────▼─────┐
        │ Supervisor │  ← 总控路由节点，读 state 判断下一步
        └──┬──┬──┬──┘
           │  │  │  │
    ┌──────┘  │  │  └──────┐
    │         │  │         │
    ▼         ▼  ▼         ▼
┌───────┐ ┌──────┐ ┌──────┐ ┌──────────┐
│Explain│ │Quiz  │ │Check │ │Recommend │
│       │ │      │ │Answer│ │          │
└───┬───┘ └──┬───┘ └──┬───┘ └────┬─────┘
    │        │        │          │
    └────────┴────────┴──────────┘
              │
        ┌─────▼─────┐
        │   __end__  │
        └───────────┘
```

- **`supervisor.py`**：LLM 调用，根据 `current_phase` + 用户最新消息 + `knowledge_map`，输出下一个要执行的目标节点（`"explainer"` / `"quizzer"` / `"check_answer"` / `"recommender"` / `"FINISH"`）。
  - **严禁在此节点做任何状态修改**，只做路由决策。
- **`builder.py`**：`StateGraph(AgentState)` 的构建函数，添加所有节点 → 注册 conditional edges → 绑定 `PostgresSaver` checkpointer → `.compile()`。
- **`nodes/explainer.py`**：解惑节点。调用 RAG 检索 + LLM 流式生成，流式输出讲解内容。
- **`nodes/quizzer.py`**：出题节点。根据 `knowledge_map` 中的薄弱点 + 错题本 + 当前学习目标，使用 `with_structured_output()` 生成 QuizCard JSON。
- **`nodes/check_answer.py`**：批改节点。比对用户提交的选项与正确答案，正确则更新 `knowledge_map` + `progress`，错误则追加 `error_notebook` 并切换回 explainer。
- **`nodes/recommender.py`**：推荐节点。分析错误盲点 → 拼关键词 → Tavily 搜索 → 结构化为 ResourceCard 列表。

#### 3.4.3 `agents/` — Agent 实现

每个 Agent 文件包含：
1. **System Prompt 构建函数**：从 state 中提取相关上下文，拼入 Prompt
2. **Agent 主逻辑**：`async def run(state: AgentState, config: RunnableConfig) -> dict`  —— 每个节点函数的签名
3. **输出解析**：Quizzer 用 `PydanticOutputParser` + `with_structured_output()`；Explainer 用流式 token

#### 3.4.4 `tools/` — 外部工具

| 工具 | 封装内容 | 被谁调用 |
|------|---------|---------|
| `search.py` | Tavily Search API 异步封装 | Explainer（扩展搜索）、Recommender |
| `rag_retriever.py` | pgvector 相似度搜索 → 格式化文本返回 | Explainer（本地知识检索） |
| `knowledge_map.py` | 读写 State 中的 `knowledge_map` | Quizzer、Checker、Recommender |

#### 3.4.5 `prompts/` — Prompt 管理

**为什么要独立目录？**
- Prompt 是 Agent 行为的核心资产，需要版本管理和集中调优。
- 每个 Agent 的 System Prompt 独立为模块，方便 A/B 测试和调试。
- 出题 Agent 的 `quizzer.py` 包含 **few-shot 示例**（3-5 组标准题目 JSON），确保结构化输出格式稳定。

### 3.5 数据模型层 (`app/models/`)

这层定义的是 **Pydantic v2 模型**，横跨 API 输入/输出、LangGraph State、数据库 ORM：

| 文件 | 核心 Schema | 用途 |
|------|------------|------|
| `session.py` | `SessionCreate`, `SessionResponse` | API 请求体/响应体 |
| `chat.py` | `ChatRequest`, `SSEEvent` | 聊天输入 & SSE 事件格式 |
| `quiz.py` | `QuizCard`, `QuizOption`, `AnswerSubmission` | 结构化题目卡片 + 用户作答 |
| `knowledge.py` | `KnowledgePoint`, `KnowledgeMap` | 知识点掌握状态 |
| `recommendation.py` | `ResourceCard` | 推荐资源卡片 |

### 3.6 数据访问层 (`app/db/`)

#### 3.6.1 PostgreSQL 的三个角色

| 角色 | 使用技术 | 存储内容 |
|------|---------|---------|
| **Checkpoint 持久化** | `langgraph-checkpoint-postgres` | LangGraph 状态快照（每次 super-step 自动保存） |
| **业务表** | SQLAlchemy 2.0 (async) 或 raw asyncpg | 用户、会话、知识点映射、错题本 |
| **向量库** | `pgvector` 扩展 | 教材/题库的 chunk embedding，用于 RAG 相似度搜索 |

#### `repositories/` — 仓储模式

每个 Repository 封装对一张（或多张关联）表的操作，全部为 `async` 方法：
- `session_repo.py`：`create_session()`, `get_session()`, `list_sessions()`, `delete_session()`
- `knowledge_repo.py`：`upsert_knowledge_point()`, `get_knowledge_map(session_id)`
- `error_repo.py`：`add_error()`, `get_error_notebook(session_id)`, `sample_old_errors()`（间隔复习用）
- `user_repo.py`：`create_user()`, `get_user()`

#### `vector/` — 向量存储

- `embedding.py`：封装 OpenAI `text-embedding-3-small`（或 `bge-large-zh-v1.5`），提供 `async def embed(texts: list[str]) -> list[list[float]]`
- `store.py`：`pgvector` 的查询封装 —— `async def similarity_search(query: str, top_k: int, filter: dict) -> list[Document]`
- `loader.py`：PDF 加载（`PyMuPDF` 或 `Unstructured`）→ 递归字符分割（`RecursiveCharacterTextSplitter`）→ 批量 embed → 写入 pgvector

### 3.7 流式输出层 (`app/streaming/`)

**这是保障前端"打字机效果"的核心模块。**

- **`filters.py`**：从 LangGraph 的 `astream_events(version="v2")` 全量事件中，精准过滤出 `on_chat_model_stream` 类型且来源为 `explainer` 节点的事件。
- **`formatters.py`**：将 token 事件编码为 SSE 标准格式：
  ```
  data: {"type": "token", "content": "异"}

  data: {"type": "token", "content": "步"}

  ...
  data: {"type": "done"}

  ```
  非流式事件（如 QuizCard、ResourceCard）以 `{"type": "quiz_card", "data": {...}}` 一次性推送。

### 3.8 测试目录 (`tests/`)

结构与应用目录镜像。关键要点：
- `conftest.py`：提供 `asyncpg` 测试数据库 fixture、Mock LLM fixture（避免测试烧钱）、预编译的测试 Graph fixture
- `test_core/`：核心测试 State 更新幂等性、Supervisor 路由准确性、Quizzer 输出格式合规性
- `test_api/`：使用 `httpx.AsyncClient` 测试 FastAPI 端点
- `test_db/`：用真实 PostgreSQL 测试 Repository 和 pgvector

---

## 四、数据流全景

```
用户浏览器
   │  POST /chat/{session_id}/stream
   │  { "message": "什么是事件循环？" }
   ▼
FastAPI Router (chat.py)
   │  获取 thread_id → 构建 config = {"configurable": {"thread_id": session_id}}
   ▼
graph.astream_events({"messages": [HumanMessage(...)]}, config, version="v2")
   │
   ▼
LangGraph 运行时
   │  1. Checkpointer 从 PostgreSQL 恢复该 thread_id 的历史 State
   │  2. Supervisor 节点分析 → 路由到 "explainer"
   │  3. Explainer 节点：
   │     - RAG 检索本地知识库
   │     - (可选) Tavily 联网搜索
   │     - LLM 流式生成回答
   │     - yield on_chat_model_stream 事件
   │  4. 流式事件 → filters.py 过滤 → formatters.py 编码
   │  5. 每次 super-step 结束，Checkpointer 自动写 PostgreSQL
   ▼
StreamingResponse → SSE 字节流 → 浏览器逐 token 渲染
```

---

## 五、推荐实施顺序（分阶段推进）

### 阶段 0：环境搭建（预计 1 天）
1. 创建项目目录骨架（按上述结构）
2. `docker-compose.yml` 启动 PostgreSQL 16 + pgvector
3. `requirements.txt` 锁死版本（LangGraph、LangChain、FastAPI、asyncpg、pgvector、openai 等）
4. `.env` 配置、`config.py` 读取
5. `alembic init` + 初始迁移脚本
6. 前端项目脚手架：`npm create vite@latest frontend -- --template react-ts`，安装 Tailwind + Zustand + fetch-event-source

### 阶段 1：最简可跑链路（预计 2-3 天）
**目标**：一个不崩溃的 Echo Agent，验证整条链路通。

1. **`state.py`**：定义初始 `AgentState`
2. **`graph/builder.py`**：构建单节点图（只有 explainer 节点，直接 echo 用户消息）
3. **`streaming/`**：实现 SSE filter + formatter
4. **`api/routes/chat.py`**：`StreamingResponse` 端点
5. **`main.py`**：组装 FastAPI + 生命周期
6. **前端**：搭建 ChatPanel + SSE 消费（fetch-event-source），实现打字机效果
7. **验证**：浏览器发送消息，看到流式返回

### 阶段 2：Supervisor 路由 + 多 Agent（预计 3-4 天）
**目标**：实现 Supervisor → Explainer / Quizzer / CheckAnswer / Recommender 的完整路由循环。

1. 实现所有 Prompt 模板（`prompts/`）
2. 实现 Supervisor 节点（`graph/supervisor.py`）
3. 实现各子 Agent 节点（`graph/nodes/`）
4. 实现各 Agent 逻辑（`agents/`）
5. 引入 Logger，记录路由决策链路
6. **前端**：实现 QuizCard + CheckResult + PhaseIndicator 组件，对接 phase_change / quiz_card / check_result 事件
7. **验证**：多轮对话能正确切换 Agent，前端正确渲染题目卡片和批改结果

### 阶段 3：知识图谱 + 进度系统（预计 2 天）
**目标**：让学习"可量化"。

1. 实现 `knowledge_map` 更新逻辑（Checker 节点）
2. 实现 `progress` 计算逻辑
3. SSE 事件中增加进度推送
4. **前端**：实现 ProgressBar + KnowledgeGraph 组件，对接 progress_update 事件
5. **验证**：答题正确 → 进度上升，答题错误 → 错题归档，前端图表联动

### 阶段 4：数据库完善（预计 2-3 天）
**目标**：三层数据存储全部到位。

1. `langgraph-checkpoint-postgres` 对接（替换内存 Checkpointer）
2. Repository 层全部实现（session / knowledge / error / user）
3. pgvector 向量库搭建 + `loader.py` 实现
4. RAG 工具（`tools/rag_retriever.py`）对接 Explainer
5. **前端**：实现 SessionList + SessionCreate 组件，对接 sessions REST API
6. **验证**：重启服务后对话历史不丢失；RAG 检索返回相关内容

### 阶段 5：外部工具 + 推荐系统（预计 2 天）
1. Tavily Search 工具封装（`tools/search.py`）
2. Recommender Agent 完整实现
3. Explainer 接入联网搜索（当本地知识库无法覆盖时）
4. **前端**：实现 ResourceCard 组件，对接 resource_cards 事件
5. **验证**：推荐 Agent 返回结构化资源卡片，前端正确渲染

### 阶段 6：错题本 + 间隔复习（预计 2 天）
1. 错题持久化到 `error_notebook` 表
2. Quizzer 实现"温故知新"抽样逻辑
3. 复习触发策略（低概率随机 + 知识点关联）
4. **验证**：学习过程中自动弹出旧题

### 阶段 7：测试 + 打磨（预计 2-3 天）
1. 补全单元测试 + 集成测试
2. 异常处理完善（LLM 超时重试、搜索 API 降级）
3. 日志结构化
4. 性能调优（连接池大小、chunk size）
5. 前端错误处理完善（网络断开重连、SSE 解析容错）

---

## 六、关键技术决策备忘

| 决策点 | 选择 | 理由 |
|--------|------|------|
| 数据库 | PostgreSQL **唯一** | 技术栈文档要求，一库三用（业务 + Checkpoint + Vector） |
| Checkpointer | `langgraph-checkpoint-postgres` | 与 LangGraph 深度集成，自动序列化 State |
| 异步方式 | `async def` 全链路 | FastAPI + LangGraph 都原生支持 async |
| State 定义 | `TypedDict` + `Annotated` | LangGraph 原生支持，支持 reducer（add_messages, add） |
| 结构化输出 | `with_structured_output()` (Pydantic v2) | 工程层面杜绝 Quizzer 输出格式错误 |
| 流式方案 | `astream_events(version="v2")` | 官方推荐，能按节点 + tag 精准过滤事件 |
| Embedding | 先用 `text-embedding-3-small` | 性价比高，中文兼容；后续可换 bge系列 |
| LLM 选型 | 路由/出题用强模型，讲解用性价比模型 | 文档明确要求，不同 Agent 可用不同 model |
| 前端框架 | React 18 + TypeScript + Vite | 聊天组件生态丰富、JSX 适合多类型卡片混排、Vite 秒级 HMR |
| 样式方案 | Tailwind CSS | 聊天 UI 间距/颜色/响应式写得快，无需维护独立 CSS 文件 |
| 前端状态管理 | Zustand | 极轻量，一个 store 管全部前端状态，比 Redux 省 90% 代码 |
| SSE 消费 | @microsoft/fetch-event-source | 支持 POST 请求、自定义 headers、错误自动重连 |
| Markdown 渲染 | react-markdown + rehype-katex | LLM 输出含代码块和数学公式，KaTeX 排版必备 |
| 图表 | ECharts + Recharts | 知识图谱用 ECharts（中文文档好），进度用 Recharts（React 原生） |

---

## 七、SSE 事件类型契约（前后端联调核心）

前后端通过 SSE 字节流通信，所有事件遵循统一 JSON 格式：`data: {"type": "...", ...}\n\n`

| event type | payload | 触发时机 | 前端行为 |
|---|---|---|---|
| `token` | `{content: string}` | explainer 流式输出每个 token | 追加到当前消息气泡末尾（打字机效果） |
| `done` | `{node: string}` | 当前节点执行完毕 | 标记该消息完成，恢复输入框 |
| `phase_change` | `{phase: string, from: string}` | supervisor 路由切换节点 | 更新顶部状态栏（如"正在出题…"） |
| `quiz_card` | `QuizCard` | quizzer 生成题目 | 渲染题目卡片（选项按钮 + 提交） |
| `check_result` | `{correct: bool, explanation: string, correct_answer: string}` | checker 批改完成 | 显示对勾/叉号 + 解析 + 正确答案 |
| `resource_cards` | `{cards: ResourceCard[]}` | recommender 推荐完成 | 渲染推荐资源卡片列表 |
| `progress_update` | `{progress: float, knowledge_map: dict}` | 进度或知识点状态变化 | 更新侧边栏进度条 + 知识图谱 |
| `error` | `{code: string, detail: string}` | 任何异常 | 显示红色错误提示条，不中断流 |

**关键约定**：
- `QuizCard` 和 `ResourceCard` 的字段定义以后端 `app/models/` 下的 Pydantic Schema 为准，前端 `types.ts` 使用完全相同的 TypeScript 接口。
- 每次请求至少以一个 `done` 或 `error` 事件结束，前端以此判断本次流结束。
- 前端不可假设事件顺序——`progress_update` 可能在 `token` 流中间穿插推送。

---

## 八、前端架构

### 8.1 核心组件树

```
App
├── SessionList (侧边栏)
│   ├── SessionCreate (新建按钮 + 弹窗)
│   └── SessionItem[] (会话列表项)
│
└── ChatPanel (主区域)
    ├── PhaseIndicator (顶部：当前阶段 + 进度条)
    │   └── ProgressBar
    ├── MessageList (消息列表，自动滚底)
    │   ├── MessageBubble (用户消息)
    │   ├── MessageBubble (AI 消息)
    │   │   └── StreamingText (流式 token 动画)
    │   ├── QuizCard (题目卡片)
    │   │   └── QuizOption[]
    │   ├── CheckResult (批改结果)
    │   ├── ResourceCard[] (推荐资源列表)
    │   └── ErrorBanner (错误提示)
    ├── KnowledgeGraph (知识图谱面板，可收起)
    └── ChatInput (底部输入框)
```

### 8.2 Zustand Store 设计

```typescript
// store/chatStore.ts
interface ChatStore {
  // ── 连接状态 ──
  streaming: boolean               // 是否正在接收 SSE 流
  currentPhase: 'idle' | 'explaining' | 'quiz' | 'checking' | 'recommending'

  // ── 当前渲染内容 ──
  messages: Message[]              // 对话历史（含流式片段）
  quizCard: QuizCard | null        // 当前待答题目
  checkResult: CheckResult | null  // 当前批改结果
  resourceCards: ResourceCard[]    // 当前推荐列表
  errorMessage: string | null      // 当前错误信息

  // ── 学习状态 ──
  knowledgeMap: Record<string, 'mastered' | 'learning' | 'unfamiliar'>
  progress: number                 // 0.0 ~ 1.0

  // ── Actions ──
  startStream: (sessionId: string) => void
  appendToken: (token: string) => void
  setQuizCard: (card: QuizCard) => void
  setCheckResult: (result: CheckResult) => void
  submitAnswer: (sessionId: string, option: string) => Promise<void>
  sendMessage: (sessionId: string, text: string) => Promise<void>
  clearError: () => void
}
```

**关键设计**：
- `messages` 中最后一条 AI 消息在 `streaming=true` 期间持续追加 token；收到 `done` 事件后 `streaming` 置为 false，该消息冻结。
- `submitAnswer` 内部也是走 SSE（因为答案提交后要走 Supervisor → Checker 流程），不是普通 REST。
- 收到 `error` 事件只设置 `errorMessage`，不清空已有消息——保证已输出的内容不丢失。

### 8.3 SSE 消费流程

```
用户点击发送
  │
  ▼
chatStore.sendMessage(sessionId, text)
  │  1. messages.push({role: 'user', content: text})
  │  2. messages.push({role: 'ai', content: '', streaming: true})
  │  3. streaming = true
  │  4. 调用 fetchEventSource(`POST /chat/${sessionId}/stream`, {body: {message: text}})
  ▼
onmessage 回调 → 解析 JSON → 按 event.type 分发：
  │
  ├─ "token"          → chatStore.appendToken(event.content)
  ├─ "phase_change"   → chatStore.currentPhase = event.phase
  ├─ "quiz_card"      → chatStore.setQuizCard(event)
  ├─ "check_result"   → chatStore.setCheckResult(event)
  ├─ "resource_cards" → chatStore.resourceCards = event.cards
  ├─ "progress_update"→ chatStore.progress = event.progress
  │                     chatStore.knowledgeMap = event.knowledge_map
  ├─ "done"           → chatStore.streaming = false
  │                     chatStore.currentPhase = 'idle'
  └─ "error"          → chatStore.errorMessage = event.detail
                         chatStore.streaming = false
onclose 回调 → chatStore.streaming = false（安全兜底）
```

### 8.4 路由设计

| 路由 | 组件 | 说明 |
|---|---|---|
| `/` | `SessionList` + 空白占位 | 首页，无活跃会话时提示新建 |
| `/chat/:sessionId` | `SessionList` + `ChatPanel` | 聊天主界面，从后端恢复历史消息 |

仅需两个路由，单页应用即可覆盖全部功能。

### 8.5 错误处理 & 降级

- **网络断开**：fetch-event-source 自动重连（最多 3 次，间隔递增），重连失败后显示"连接中断"错误条。
- **SSE 解析失败**：跳过该条事件，记录 console.warn，不影响后续事件。
- **LLM 超时 / 后端 500**：后端返回 `error` SSE 事件 → 前端显示红色提示条，用户可重试发送上一条消息。
- **空状态**：无会话时引导创建；无消息时显示学习目标作为 placeholder。

---

## 九、下一步行动

建议从**阶段 0**开始，按顺序执行。每完成一个阶段，我会帮你：

1. **生成该阶段涉及的所有文件骨架代码**
2. **编写对应的测试用例**
3. **提供验证命令（curl / pytest）**

你可以随时说"开始阶段 0"，我会立即帮你搭建项目骨架。

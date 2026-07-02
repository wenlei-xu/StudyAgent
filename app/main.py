import sys

# Windows: psycopg (used by langgraph-checkpoint-postgres) requires SelectorEventLoop.
# Must run before any other asyncio imports or event loop creation.
if sys.platform == "win32":
    import asyncio
    import selectors
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import re
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.api.middleware import setup_middleware
from app.api.routes.chat import router as chat_router
from app.api.routes.health import router as health_router
from app.api.routes.sessions import router as sessions_router
from app.api.routes.stages import router as stages_router
from app.api.routes.knowledge import router as knowledge_router, notes_router as knowledge_notes_router
from app.config import settings
from app.utils.logging_config import setup_logging
from app.core.graph.builder import build_graph


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(settings.log_level)

    # PostgresSaver for LangGraph checkpoint persistence
    pg_url = re.sub(r'\+.*?(?=://)', '', settings.database_url_sync)
    async with AsyncPostgresSaver.from_conn_string(pg_url) as checkpointer:
        await checkpointer.setup()
        app.state.graph = build_graph(checkpointer=checkpointer)
        yield


app = FastAPI(title="智能学习 Agent", version="0.1.0", lifespan=lifespan)

setup_middleware(app)

app.include_router(health_router, tags=["health"])
app.include_router(chat_router, prefix="/chat", tags=["chat"])
app.include_router(sessions_router, prefix="/sessions", tags=["sessions"])
app.include_router(stages_router, prefix="/sessions", tags=["stages"])
app.include_router(knowledge_router, prefix="/sessions", tags=["knowledge"])
app.include_router(knowledge_notes_router, tags=["knowledge"])

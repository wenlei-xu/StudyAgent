from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.middleware import setup_middleware
from app.api.routes.chat import router as chat_router
from app.api.routes.health import router as health_router
from app.api.routes.sessions import router as sessions_router
from app.config import settings
from app.utils.logging_config import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(settings.log_level)
    # DB connection pool will be initialized here in Phase 4
    # Graph will be compiled and cached here in Phase 1
    yield
    # DB connection pool will be closed here in Phase 4


app = FastAPI(title="智能学习 Agent", version="0.1.0", lifespan=lifespan)

setup_middleware(app)

app.include_router(health_router, tags=["health"])
app.include_router(chat_router, prefix="/chat", tags=["chat"])
app.include_router(sessions_router, prefix="/sessions", tags=["sessions"])

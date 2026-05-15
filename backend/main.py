import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.config import CORS_ORIGINS
from backend.database import init_db
from backend.routers import auth
from backend.services.rate_limit_service import (
    FastAPILimiter,
    enforce_chat_rate_limit,
    shutdown_rate_limiter,
)
from backend.services.redis_service import close_redis, init_redis
from graph.hybrid_rag import generate_response

logger = logging.getLogger("graphrag.api")


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()

    redis = await init_redis()
    if redis:
        await FastAPILimiter.init(redis)
    else:
        await FastAPILimiter.init_disabled()

    try:
        yield
    finally:
        await shutdown_rate_limiter()
        await close_redis()


app = FastAPI(
    title="GraphRAG API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")


class ChatRequest(BaseModel):
    query: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/chat", dependencies=[Depends(enforce_chat_rate_limit)])
async def chat(request: ChatRequest):
    answer = generate_response(request.query)
    return {"answer": answer}

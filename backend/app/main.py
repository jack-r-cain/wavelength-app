import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import health, items, knowledge
from app.core.config import settings
from app.database import create_db_and_tables
from app.utils.logging import configure_logging
from app.utils.request_context import set_request_id


configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    logger.info("application_started")
    yield
    logger.info("application_stopped")


app = FastAPI(
    title=settings.APP_NAME,
    description="Personal knowledge agent with grounded retrieval and semantic search",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    request_id = set_request_id(request.headers.get("X-Request-ID"))
    try:
        response = await call_next(request)
    except Exception as exc:  # noqa: BLE001
        logger.exception("request_failed")
        return JSONResponse(
            status_code=500,
            content={
                "detail": "The server hit an unexpected error.",
                "request_id": request_id,
                "error_type": type(exc).__name__,
            },
        )

    response.headers["X-Request-ID"] = request_id
    return response


app.include_router(items.router)
app.include_router(knowledge.router)
app.include_router(health.router)


@app.get("/")
def read_root():
    return {
        "name": settings.APP_NAME,
        "status": "ok",
        "knowledge_api": "/knowledge/ask",
    }

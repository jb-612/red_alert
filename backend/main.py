import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.alerts import router as alerts_router
from backend.api.analytics import router as analytics_router
from backend.api.locations import router as locations_router
from backend.config import settings
from backend.database import init_db

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Initialize database on startup."""
    init_db()
    yield


app = FastAPI(
    title="Red Alert Analytics API",
    description="Analytics API for Israel's OREF alert history data",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(alerts_router)
app.include_router(analytics_router)
app.include_router(locations_router)


@app.get("/api/health")
def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}

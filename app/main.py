from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.config import settings
from app.database import close_db
from app.core.logging import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    logger.info("Starting Portfolio API")
    yield
    logger.info("Shutting down Portfolio API")
    await close_db()


app = FastAPI(
    title="Portfolio API",
    description="A portfolio management API with authentication and real-time market data",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz")
async def health_check():
    """Health check endpoint."""
    return {"ok": True, "service": "portfolio-api"}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Portfolio API",
        "version": "1.0.0",
        "docs": "/docs",
    }

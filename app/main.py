from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.config import settings
from app.database import close_db, AsyncSessionLocal
from app.core.logging import setup_logging
from app.auth.routes import router as auth_router
from app.etl.service import run_etl
from app.portfolio.routes import router as portfolio_router

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Portfolio API")
    if settings.etl_on_startup:
        logger.info("ETL on startup enabled; running ETL job")
        try:
            async with AsyncSessionLocal() as session:
                await run_etl(session)
        except Exception as exc:  # pragma: no cover - startup logging
            logger.exception(f"ETL on startup failed: {exc}")
    if settings.etl_schedule_enabled:
        logger.info(f"ETL scheduling enabled for {settings.etl_schedule_hour}:00")
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
    return {"ok": True, "service": "portfolio-api"}


@app.get("/")
async def root():
    return {
        "message": "Portfolio API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "auth": "/auth/login, /auth/social, /auth/me",
            "health": "/healthz"
        }
    }


app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(portfolio_router, tags=["Portfolio"])

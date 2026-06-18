from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from prometheus_fastapi_instrumentator import Instrumentator

from app.core.config import settings
from app.core.database import engine, Base
from app.api.swift import router as swift_router
from app.utils.swift_utils import refresh_exchange_rates
from apscheduler.schedulers.asyncio import AsyncIOScheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        print(f"⚠️ DB init warning: {e}")
    await refresh_exchange_rates()
    scheduler = AsyncIOScheduler()
    scheduler.add_job(refresh_exchange_rates, "interval", hours=1, id="refresh_rates")
    scheduler.start()
    print(f"✅ {settings.APP_NAME} démarré")
    yield
    scheduler.shutdown(wait=False)
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Instrumentator().instrument(app).expose(app)
app.include_router(swift_router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "version": settings.VERSION,
        "supported_currencies": ["EUR", "USD", "GBP", "MAD", "CHF", "JPY", "CAD", "AUD"],
    }

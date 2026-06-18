from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from prometheus_fastapi_instrumentator import Instrumentator

from app.core.config import settings
from app.core.database import engine, Base
from app.api.sepa import router as sepa_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        print(f"⚠️ DB init warning: {e}")
    print(f"✅ {settings.APP_NAME} démarré")
    yield
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
app.include_router(sepa_router, prefix="/api/v1")


@app.get("/health")
async def health():
    from sqlalchemy import text as sa_text
    checks = {}
    try:
        async with engine.begin() as conn:
            await conn.execute(sa_text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {str(e)[:50]}"
    overall = "ok" if all(v == "ok" for v in checks.values()) else "degraded"
    return {
        "status": overall,
        "service": settings.APP_NAME,
        "version": settings.VERSION,
        "checks": checks,
    }

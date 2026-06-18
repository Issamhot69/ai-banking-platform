from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from prometheus_fastapi_instrumentator import Instrumentator

from app.core.config import settings
from sqlalchemy import text
from app.core.database import engine, Base
from app.core.redis import init_redis, close_redis
from app.api.transactions import router as transactions_router
from app.api.standing_orders import router as standing_orders_router
from app.api.savings_goals import router as savings_goals_router
from app.tasks.standing_orders import execute_due_standing_orders
from app.tasks.outbox_publisher import publish_pending_events
from app.models.outbox import OutboxEvent  # noqa: F401
from apscheduler.schedulers.asyncio import AsyncIOScheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        print(f"⚠️  Skipping create_all (tables managed externally): {e}")
    await init_redis()
    scheduler = AsyncIOScheduler()
    scheduler.add_job(execute_due_standing_orders, "interval", seconds=60, id="standing_orders")
    scheduler.add_job(publish_pending_events, "interval", seconds=5, id="outbox_publisher")
    scheduler.start()
    print(f"✅ {settings.APP_NAME} démarré")
    yield
    scheduler.shutdown(wait=False)
    await close_redis()
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
app.include_router(transactions_router, prefix="/api/v1")
app.include_router(standing_orders_router, prefix="/api/v1/standing-orders")
app.include_router(savings_goals_router, prefix="/api/v1/savings-goals")


@app.get("/health")
async def health():
    from app.core.database import engine
    from app.core.redis import get_redis
    import asyncio

    checks = {}

    # DB check
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {str(e)[:50]}"

    # Redis check
    try:
        r = await get_redis()
        await r.ping()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {str(e)[:50]}"

    # Kafka check (connectivité basique)
    try:
        from kafka import KafkaAdminClient
        admin = KafkaAdminClient(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            request_timeout_ms=2000,
        )
        admin.close()
        checks["kafka"] = "ok"
    except Exception as e:
        checks["kafka"] = f"error: {str(e)[:50]}"

    overall = "ok" if all(v == "ok" for v in checks.values()) else "degraded"

    return {
        "status": overall,
        "service": settings.APP_NAME,
        "version": settings.VERSION,
        "checks": checks,
    }

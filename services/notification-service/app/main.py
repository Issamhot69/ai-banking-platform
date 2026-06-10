from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from prometheus_fastapi_instrumentator import Instrumentator
import asyncio

from app.core.config import settings
from app.core.database import engine, Base
from app.core.redis import init_redis, close_redis
from app.api.notifications import router as notifications_router
from app.consumers.kafka_consumer import notification_consumer


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await init_redis()
    asyncio.create_task(notification_consumer.start())
    print(f"✅ {settings.APP_NAME} démarré")
    print("📱 Push Firebase: prêt")
    print("📧 Email SendGrid: prêt")
    print("💬 SMS Twilio: prêt")
    print("🔔 Kafka Consumer: démarré")
    yield
    notification_consumer.stop()
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
app.include_router(notifications_router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "version": settings.VERSION,
        "providers": ["firebase", "sendgrid", "twilio"],
    }

from fastapi import FastAPI
from .api.routes import menu
from .core.database import init_pool, close_pool
from .core.redis_client import get_redis

app = FastAPI(title="Raf Coffee API")

app.include_router(menu.router)

@app.on_event("startup")
async def startup():
    await init_pool()
    redis = get_redis()
    redis.ping()
    print("✅ База и Redis готовы")

@app.on_event("shutdown")
async def shutdown():
    await close_pool()
    print("👋 Приложение остановлено")

@app.get("/ping")
async def ping():
    return {"status": "ok", "message": "Raf Coffee API works!"}
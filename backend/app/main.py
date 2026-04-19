from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api.routes import menu, admin
from app.core.database import init_pool, close_pool
from app.core.redis_client import get_redis, close_redis
app = FastAPI(title="Raf Coffee API")

static_dir = "static"

app.mount("/static", StaticFiles(directory=static_dir), name="static")

app.include_router(menu.router)
app.include_router(admin.router)

@app.on_event("startup")
async def startup():
    await init_pool()
    redis = await get_redis()
    await redis.ping()
    print("✅ База и Redis готовы")

@app.on_event("shutdown")
async def shutdown():
    await close_redis()
    await close_pool()
    print("👋 Приложение остановлено")

@app.get("/ping")
async def ping():
    return {"status": "ok", "message": "Raf Coffee API works!"}
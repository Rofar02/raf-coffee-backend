from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.routes import menu, admin
from app.core.database import init_pool, close_pool
from app.core.redis_client import get_redis, close_redis

app = FastAPI(title="Raf Coffee API")

static_dir = "static"

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

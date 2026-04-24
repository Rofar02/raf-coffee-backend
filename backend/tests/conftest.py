"""
Переменные окружения должны быть заданы до импорта app: database/redis/auth
читают get_settings() при импорте модулей.
"""
from __future__ import annotations

import os
import sys
from collections.abc import Generator

# --- env (должно быть до import app) ---
if "DATABASE_URL" not in os.environ:
    if os.path.exists("/.dockerenv"):
        os.environ["DATABASE_URL"] = "postgresql://rafuser:rafpass@postgres:5432/rafcoffee"
        os.environ["REDIS_URL"] = "redis://redis:6379/0"
    else:
        os.environ["DATABASE_URL"] = "postgresql://rafuser:rafpass@127.0.0.1:5432/rafcoffee"
        os.environ["REDIS_URL"] = "redis://127.0.0.1:6379/0"
os.environ.setdefault("ADMIN_TOKEN", "test-admin-token-raf-coffee")

# backend/ в PYTHONPATH (pytest [tool.pytest] pythonpath = ["."] относительно pyproject)
_backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _backend_root not in sys.path:
    sys.path.insert(0, _backend_root)

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    from app.main import app

    with TestClient(app) as c:
        yield c


@pytest.fixture
def admin_headers() -> dict[str, str]:
    return {"X-Admin-Token": os.environ["ADMIN_TOKEN"]}

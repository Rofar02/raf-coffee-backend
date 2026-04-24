"""
Интеграционные тесты HTTP API админки (нужны PostgreSQL и Redis, как в docker compose).
Запуск из каталога backend:  poetry run pytest
Или:  docker compose exec backend poetry run pytest
"""
from __future__ import annotations

import base64
import os
from pathlib import Path
from typing import Any

import pytest

# Минимальный валидный PNG 1x1
_PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAfKm27QAAAABJRU5ErkJggg=="
)


def _j(r: Response) -> Any:
    return r.json()


def test_admin_missing_token_for_categories(client) -> None:
    r = client.get("/admin/categories")
    # Starlette: отсутствие API-ключа → 401
    assert r.status_code == 401


def test_admin_invalid_token(client) -> None:
    r = client.get(
        "/admin/categories", headers={"X-Admin-Token": "definitely-wrong-" + os.environ["ADMIN_TOKEN"]}
    )
    assert r.status_code == 403


def test_list_categories_and_flush_cache(client, admin_headers) -> None:
    r = client.get("/admin/categories", headers=admin_headers)
    assert r.status_code == 200
    cats = _j(r)
    assert isinstance(cats, list) and len(cats) >= 1
    assert "id" in cats[0] and "name" in cats[0]

    r2 = client.post("/admin/flush-menu-cache", headers=admin_headers)
    assert r2.status_code == 200
    assert _j(r2) == {"ok": True}


def test_subcategory_crud_and_bad_category(client, admin_headers) -> None:
    r = client.get("/admin/categories", headers=admin_headers)
    kitchen_id = next(c["id"] for c in _j(r) if "кух" in c["name"].lower() or c.get("id") == 1)
    r_bad = client.post(
        "/admin/subcategories",
        headers=admin_headers,
        json={"category_id": 999_999, "name": "X", "sort_order": 0},
    )
    assert r_bad.status_code == 400
    assert _j(r_bad)["detail"] == "Category not found"

    r0 = client.post(
        "/admin/subcategories",
        headers=admin_headers,
        json={"category_id": kitchen_id, "name": "Автотест-рубрика", "sort_order": 99},
    )
    assert r0.status_code == 200
    sub = _j(r0)
    sid = sub["id"]
    assert sub["subcategory_name"] == "Автотест-рубрика"

    r1 = client.put(
        f"/admin/subcategories/{sid}",
        headers=admin_headers,
        json={"name": "Автотест-рубрика-2"},
    )
    assert r1.status_code == 200
    assert "Автотест" in _j(r1)["subcategory_name"]

    r_empty = client.put(
        f"/admin/subcategories/{sid}",
        headers=admin_headers,
        json={},
    )
    assert r_empty.status_code == 400

    r_del = client.delete(f"/admin/subcategories/{sid}", headers=admin_headers)
    assert r_del.status_code == 200
    assert _j(r_del)["ok"] is True

    r_nf = client.delete(f"/admin/subcategories/{sid}", headers=admin_headers)
    assert r_nf.status_code == 404


def test_dish_create_update_delete(client, admin_headers) -> None:
    r = client.get("/admin/categories", headers=admin_headers)
    kitchen_id = next(c["id"] for c in _j(r) if c.get("id") == 1 or "кух" in c["name"].lower())
    r0 = client.post(
        "/admin/subcategories",
        headers=admin_headers,
        json={"category_id": kitchen_id, "name": "Автотест-блюда", "sort_order": 1},
    )
    assert r0.status_code == 200
    sub_id = _j(r0)["id"]
    try:
        r1 = client.post(
            "/admin/dishes",
            headers=admin_headers,
            json={
                "name": "Тестовое блюдо",
                "price": 100,
                "is_base_menu": True,
                "subcategory_id": sub_id,
            },
        )
        assert r1.status_code == 200
        dish = _j(r1)
        d_id = dish["id"]
        assert dish["name"] == "Тестовое блюдо"

        r2 = client.put(
            f"/admin/dishes/{d_id}",
            headers=admin_headers,
            json={
                "name": "Тестовое блюдо (правка)",
                "price": 150,
                "is_base_menu": True,
                "subcategory_id": sub_id,
            },
        )
        assert r2.status_code == 200
        assert "правка" in _j(r2)["name"]

        r_nf = client.put(
            "/admin/dishes/999_999_999",
            headers=admin_headers,
            json={
                "name": "X",
                "price": 1,
                "is_base_menu": True,
            },
        )
        assert r_nf.status_code == 404

        r3 = client.delete(f"/admin/dishes/{d_id}", headers=admin_headers)
        assert r3.status_code == 200
    finally:
        client.delete(f"/admin/subcategories/{sub_id}", headers=admin_headers)


def test_season_create_and_delete(client, admin_headers) -> None:
    r1 = client.post(
        "/admin/seasons",
        headers=admin_headers,
        json={"name": "Сезон pytest", "is_active": False, "sort_order": 99},
    )
    assert r1.status_code == 200
    new = _j(r1)
    new_id = new["id"]
    assert "pytest" in new["slug"] or "pytest" in new["name"].lower()

    r_del = client.delete(f"/admin/seasons/{new_id}", headers=admin_headers)
    assert r_del.status_code == 200


def test_cannot_delete_last_season(client, admin_headers) -> None:
    r = client.get("/admin/seasons", headers=admin_headers)
    assert r.status_code == 200
    only = _j(r)
    if len(only) != 1:
        pytest.skip("в БД должен быть ровно один сезон, чтобы проверить запрет удаления")
    rid = only[0]["id"]
    r2 = client.delete(f"/admin/seasons/{rid}", headers=admin_headers)
    assert r2.status_code == 400
    d = str(_j(r2).get("detail", "")).lower()
    assert "last" in d or "season" in d


def test_season_dish_link_and_season_dishes_list(client, admin_headers) -> None:
    r_seasons = client.get("/admin/seasons", headers=admin_headers)
    assert r_seasons.status_code == 200
    season_id = _j(r_seasons)[0]["id"]

    r = client.get("/admin/categories", headers=admin_headers)
    kitchen_id = next(c["id"] for c in _j(r) if c.get("id") == 1 or "кух" in c["name"].lower())
    r0 = client.post(
        "/admin/subcategories",
        headers=admin_headers,
        json={"category_id": kitchen_id, "name": "Автотест-линк", "sort_order": 2},
    )
    assert r0.status_code == 200
    sub_id = _j(r0)["id"]
    try:
        r1 = client.post(
            "/admin/dishes",
            headers=admin_headers,
            json={"name": "Для привязки к сезону", "price": 10, "is_base_menu": True, "subcategory_id": sub_id},
        )
        d_id = _j(r1)["id"]
        r_link = client.post(
            f"/admin/seasons/{season_id}/dishes/{d_id}",
            headers=admin_headers,
            json={"sort_order": 0, "is_visible": True},
        )
        assert r_link.status_code == 200
        r_list = client.get(f"/admin/seasons/{season_id}/dishes", headers=admin_headers)
        assert r_list.status_code == 200
        ids = {d["id"] for d in _j(r_list)}
        assert d_id in ids
        r_un = client.delete(
            f"/admin/seasons/{season_id}/dishes/{d_id}",
            headers=admin_headers,
        )
        assert r_un.status_code == 200
        client.delete(f"/admin/dishes/{d_id}", headers=admin_headers)
    finally:
        client.delete(f"/admin/subcategories/{sub_id}", headers=admin_headers)


def test_upload_image_and_reject_bad_type(client, admin_headers) -> None:
    r_bad = client.post(
        "/admin/upload",
        headers=admin_headers,
        files=[("file", ("x.bin", b"not an image", "application/octet-stream"))],
    )
    assert r_bad.status_code == 400

    r_ok = client.post(
        "/admin/upload",
        headers=admin_headers,
        files=[("file", ("px.png", _PNG_1X1, "image/png"))],
    )
    assert r_ok.status_code == 200
    data = _j(r_ok)
    assert "url" in data and data["url"].startswith("/static/uploads/images/")
    rel = data["url"].replace("/static/", "static/", 1)
    path = Path(__file__).resolve().parent.parent / rel
    if path.is_file():
        path.unlink(missing_ok=True)

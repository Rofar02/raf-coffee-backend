import json
from typing import Any, Dict, List, Optional

import asyncpg

_DEFAULT_TITLES = {
    "kirova-45a": "Кирова 45а",
    "kirova-12": "Кирова 12",
}


class InteriorRepository:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def list_all(self) -> List[Dict[str, Any]]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT slug, title, description, images_json, updated_at
                FROM interior_galleries
                ORDER BY slug
                """
            )
            out: List[Dict[str, Any]] = []
            for row in rows:
                item = dict(row)
                raw = item.pop("images_json", "[]")
                try:
                    imgs = json.loads(raw) if raw else []
                    if not isinstance(imgs, list):
                        imgs = []
                except Exception:
                    imgs = []
                item["images"] = [str(x).strip() for x in imgs if x and str(x).strip()]
                out.append(item)
            return out

    async def get_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT slug, title, description, images_json, updated_at
                FROM interior_galleries
                WHERE slug = $1
                """,
                slug,
            )
            if not row:
                return None
            item = dict(row)
            raw = item.pop("images_json", "[]")
            try:
                imgs = json.loads(raw) if raw else []
                if not isinstance(imgs, list):
                    imgs = []
            except Exception:
                imgs = []
            item["images"] = [str(x).strip() for x in imgs if x and str(x).strip()]
            return item

    async def upsert(self, slug: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        async with self.pool.acquire() as conn:
            existing_row = await conn.fetchrow(
                "SELECT title, images_json FROM interior_galleries WHERE slug = $1",
                slug,
            )
            existing_title = (dict(existing_row).get("title") if existing_row else None) or None
            images = payload.get("images")
            if images is None:
                existing_raw = (dict(existing_row).get("images_json") if existing_row else "[]") or "[]"
                try:
                    existing_images = json.loads(existing_raw)
                    if not isinstance(existing_images, list):
                        existing_images = []
                except Exception:
                    existing_images = []
                images_json = json.dumps(existing_images, ensure_ascii=False)
            else:
                images_json = json.dumps([str(x).strip() for x in images if x and str(x).strip()], ensure_ascii=False)
            title = payload.get("title")
            if not title:
                title = existing_title or _DEFAULT_TITLES.get(slug) or slug
            row = await conn.fetchrow(
                """
                INSERT INTO interior_galleries (slug, title, description, images_json)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (slug)
                DO UPDATE SET
                    title = COALESCE(EXCLUDED.title, interior_galleries.title),
                    description = COALESCE(EXCLUDED.description, interior_galleries.description),
                    images_json = EXCLUDED.images_json,
                    updated_at = NOW()
                RETURNING slug, title, description, images_json, updated_at
                """,
                slug,
                title,
                payload.get("description"),
                images_json,
            )
            item = dict(row)
            raw = item.pop("images_json", "[]")
            try:
                imgs = json.loads(raw) if raw else []
                if not isinstance(imgs, list):
                    imgs = []
            except Exception:
                imgs = []
            item["images"] = [str(x).strip() for x in imgs if x and str(x).strip()]
            return item

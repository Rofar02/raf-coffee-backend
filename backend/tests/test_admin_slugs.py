"""Юнит-тесты вспомогательной логики админ-роутов (без HTTP)."""
from __future__ import annotations

import pytest

from app.api.routes import admin as admin_routes


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("  Лето  ", "leto"),
        ("Кухня", "kuhnya"),  # х → h в _CYR_TO_LAT
        ("", "season"),
    ],
)
def test_slugify_normalizes_cyrillic_and_whitespace(raw: str, expected: str) -> None:
    assert admin_routes._slugify(raw) == expected


def test_slugify_only_punctuation_falls_back_to_season() -> None:
    assert admin_routes._slugify("!!!") == "season"

"""Optional live smoke test against the real Yandex Metrika API.

Skipped unless a token is available. Reads YANDEX_METRIKA_TOKEN from the
environment or from the project .env (one level above the mcp/ engine).
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from yandex_metrika_mcp import YandexMetrikaClient

# mcp/tests/ -> mcp/ -> yandex-metrika-mcp/  (project root holding .env)
_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


def _live_token() -> str | None:
    token = os.environ.get("YANDEX_METRIKA_TOKEN")
    if token:
        return token
    if _ENV_FILE.exists():
        for line in _ENV_FILE.read_text().splitlines():
            line = line.strip()
            if line.startswith("YANDEX_METRIKA_TOKEN="):
                value = line.split("=", 1)[1].strip().strip('"').strip("'")
                return value or None
    return None


TOKEN = _live_token()


@pytest.mark.skipif(not TOKEN, reason="no YANDEX_METRIKA_TOKEN available")
async def test_live_list_counters_returns_at_least_one():
    counters = await YandexMetrikaClient(TOKEN).list_counters()
    assert isinstance(counters, list)
    assert len(counters) >= 1
    first = counters[0]
    assert "id" in first and "name" in first and "site" in first

"""Tests for build_server: tool surface, resolver wiring, auth passthrough."""

from __future__ import annotations

import yandex_metrika_mcp.server as server_mod
from yandex_metrika_mcp import build_server


async def test_exposes_exactly_two_tools():
    async def resolver() -> str:
        return "tok"

    server = build_server(token_resolver=resolver)
    tools = await server.list_tools()
    names = {t.name for t in tools}
    assert names == {"list_counters", "query"}


async def test_name_passed_through():
    async def resolver() -> str:
        return "tok"

    server = build_server(token_resolver=resolver, name="custom-name")
    assert server.name == "custom-name"


async def test_auth_passed_through(monkeypatch):
    captured = {}

    real_init = server_mod.FastMCP.__init__

    def spy_init(self, *args, **kwargs):
        captured["auth"] = kwargs.get("auth")
        return real_init(self, *args, **kwargs)

    monkeypatch.setattr(server_mod.FastMCP, "__init__", spy_init)

    async def resolver() -> str:
        return "tok"

    sentinel = object()
    build_server(token_resolver=resolver, auth=sentinel)
    assert captured["auth"] is sentinel


async def test_list_counters_tool_awaits_resolver_and_calls_client(monkeypatch):
    calls = {"resolver": 0}

    async def resolver() -> str:
        calls["resolver"] += 1
        return "resolved-token"

    seen = {}

    class FakeClient:
        def __init__(self, token):
            seen["token"] = token

        async def list_counters(self):
            return [{"id": 1, "name": "n", "site": "s"}]

        async def query(self, **kwargs):  # pragma: no cover - not used here
            return {}

    monkeypatch.setattr(server_mod, "YandexMetrikaClient", FakeClient)

    server = build_server(token_resolver=resolver)
    tool = await server.get_tool("list_counters")

    result = await tool.fn()

    assert calls["resolver"] == 1
    assert seen["token"] == "resolved-token"
    assert result == [{"id": 1, "name": "n", "site": "s"}]


async def test_query_tool_awaits_resolver_and_forwards_args(monkeypatch):
    calls = {"resolver": 0}

    async def resolver() -> str:
        calls["resolver"] += 1
        return "resolved-token"

    seen = {}

    class FakeClient:
        def __init__(self, token):
            seen["token"] = token

        async def list_counters(self):  # pragma: no cover - not used here
            return []

        async def query(self, **kwargs):
            seen["query_kwargs"] = kwargs
            return {"ok": True}

    monkeypatch.setattr(server_mod, "YandexMetrikaClient", FakeClient)

    server = build_server(token_resolver=resolver)
    tool = await server.get_tool("query")

    result = await tool.fn(
        counter_id=42,
        metrics="ym:s:visits",
        dimensions="ym:s:date",
        sort="-ym:s:visits",
        limit=5,
    )

    assert calls["resolver"] == 1
    assert seen["token"] == "resolved-token"
    assert result == {"ok": True}
    assert seen["query_kwargs"] == {
        "counter_id": 42,
        "metrics": "ym:s:visits",
        "dimensions": "ym:s:date",
        "date1": "7daysAgo",
        "date2": "today",
        "filters": None,
        "sort": "-ym:s:visits",
        "limit": 5,
    }

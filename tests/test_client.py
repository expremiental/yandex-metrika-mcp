"""Unit tests for YandexMetrikaClient: URL, params, headers, parsing."""

from __future__ import annotations

import httpx
import pytest
import respx

from yandex_metrika_mcp import YandexMetrikaClient
from yandex_metrika_mcp.server import API_BASE

TOKEN = "test-token-123"


@respx.mock
async def test_list_counters_request_and_parsing():
    route = respx.get(f"{API_BASE}/management/v1/counters").mock(
        return_value=httpx.Response(
            200,
            json={
                "counters": [
                    {"id": 111, "name": "Site A", "site": "a.example"},
                    {"id": 222, "name": "Site B", "site": "b.example"},
                    # missing name/site -> should become None, not raise
                    {"id": 333},
                ]
            },
        )
    )

    result = await YandexMetrikaClient(TOKEN).list_counters()

    # correct URL + auth header + per_page param
    assert route.called
    request = route.calls.last.request
    assert request.url.path == "/management/v1/counters"
    assert request.url.params["per_page"] == "1000"
    assert request.headers["Authorization"] == f"OAuth {TOKEN}"

    # parsed shape: only id/name/site, in order
    assert result == [
        {"id": 111, "name": "Site A", "site": "a.example"},
        {"id": 222, "name": "Site B", "site": "b.example"},
        {"id": 333, "name": None, "site": None},
    ]


@respx.mock
async def test_query_request_params_and_passthrough():
    raw = {"query": {"ids": [555]}, "totals": [42], "data": [{"metrics": [42]}]}
    route = respx.get(f"{API_BASE}/stat/v1/data").mock(
        return_value=httpx.Response(200, json=raw)
    )

    result = await YandexMetrikaClient(TOKEN).query(
        counter_id=555,
        metrics="ym:s:visits,ym:s:users",
        dimensions="ym:s:date",
        date1="2026-06-01",
        date2="2026-06-07",
        filters="ym:s:deviceCategory=='mobile'",
        sort="-ym:s:visits",
        limit=50,
    )

    # raw response is passed straight through
    assert result == raw

    assert route.called
    request = route.calls.last.request
    assert request.url.path == "/stat/v1/data"
    assert request.headers["Authorization"] == f"OAuth {TOKEN}"

    params = request.url.params
    assert params["ids"] == "555"
    assert params["metrics"] == "ym:s:visits,ym:s:users"
    assert params["dimensions"] == "ym:s:date"
    assert params["date1"] == "2026-06-01"
    assert params["date2"] == "2026-06-07"
    assert params["filters"] == "ym:s:deviceCategory=='mobile'"
    assert params["sort"] == "-ym:s:visits"
    assert params["limit"] == "50"
    assert params["accuracy"] == "full"


@respx.mock
async def test_query_omits_optional_params_when_unset():
    route = respx.get(f"{API_BASE}/stat/v1/data").mock(
        return_value=httpx.Response(200, json={})
    )

    await YandexMetrikaClient(TOKEN).query(counter_id=1, metrics="ym:s:visits")

    params = route.calls.last.request.url.params
    # defaults applied
    assert params["date1"] == "7daysAgo"
    assert params["date2"] == "today"
    assert params["limit"] == "100"
    # optional ones not sent
    assert "dimensions" not in params
    assert "filters" not in params
    assert "sort" not in params


@respx.mock
async def test_api_error_propagates():
    respx.get(f"{API_BASE}/stat/v1/data").mock(
        return_value=httpx.Response(403, json={"errors": [{"code": 403}]})
    )

    with pytest.raises(httpx.HTTPStatusError):
        await YandexMetrikaClient(TOKEN).query(counter_id=1, metrics="ym:s:visits")

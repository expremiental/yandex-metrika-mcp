"""Yandex Metrica MCP — read-only access to Yandex Metrica analytics via MCP.

An aiaiai open-source AI-native tool. Read scope only (`metrika:read`):
the server never creates, edits or deletes anything in the account.
"""

from __future__ import annotations

import os

import httpx
from fastmcp import FastMCP

API_BASE = "https://api-metrika.yandex.net"
TOKEN_ENV = "YANDEX_METRIKA_TOKEN"

mcp = FastMCP("yandex-metrica-mcp")


def _token() -> str:
    token = os.environ.get(TOKEN_ENV)
    if not token:
        raise RuntimeError(
            f"{TOKEN_ENV} is not set. Create an OAuth token with the `metrika:read` "
            f"scope at https://oauth.yandex.ru and export it as {TOKEN_ENV}."
        )
    return token


async def _get(path: str, params: dict) -> dict:
    """GET a Metrica API endpoint with OAuth auth and return parsed JSON."""
    headers = {"Authorization": f"OAuth {_token()}"}
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(f"{API_BASE}{path}", params=params, headers=headers)
        resp.raise_for_status()
        return resp.json()


@mcp.tool
async def list_counters() -> list[dict]:
    """List Yandex Metrica counters available to the token.

    Returns each counter's id, name and site so you can pick a `counter_id`
    for `query`. Read scope is enough.
    """
    data = await _get("/management/v1/counters", {"per_page": 1000})
    return [
        {"id": c["id"], "name": c.get("name"), "site": c.get("site")}
        for c in data.get("counters", [])
    ]


@mcp.tool
async def query(
    counter_id: int,
    metrics: str,
    dimensions: str | None = None,
    date1: str = "7daysAgo",
    date2: str = "today",
    filters: str | None = None,
    sort: str | None = None,
    limit: int = 100,
) -> dict:
    """Run a Reporting API query against a Metrica counter (aggregated stats).

    Pass Metrica field names directly. Common ones:

    Metrics (comma-separated):
      ym:s:visits, ym:s:users, ym:s:pageviews, ym:s:bounceRate,
      ym:s:avgVisitDurationSeconds, ym:s:newUsers

    Dimensions (comma-separated, optional — groups the result):
      ym:s:date, ym:s:lastTrafficSource, ym:s:startURL,
      ym:s:deviceCategory, ym:s:regionCountry, ym:s:<attribution>UTMSource

    date1 / date2: YYYY-MM-DD or relative (today, yesterday, NdaysAgo).
    filters: Metrica filter expression, e.g. "ym:s:deviceCategory=='mobile'".
    sort: field to sort by; prefix with '-' for descending, e.g. "-ym:s:visits".

    Returns the raw Reporting API response (query meta, totals and data rows).
    """
    params: dict[str, object] = {
        "ids": counter_id,
        "metrics": metrics,
        "date1": date1,
        "date2": date2,
        "limit": limit,
        "accuracy": "full",
    }
    if dimensions:
        params["dimensions"] = dimensions
    if filters:
        params["filters"] = filters
    if sort:
        params["sort"] = sort
    return await _get("/stat/v1/data", params)


def main() -> None:
    # Transport is stdio by default (local clients like Claude Desktop).
    # Set MCP_TRANSPORT=http for the hosted/remote deployment.
    transport = os.environ.get("MCP_TRANSPORT", "stdio")
    if transport == "http":
        mcp.run(
            transport="http",
            host=os.environ.get("HOST", "127.0.0.1"),
            port=int(os.environ.get("PORT", "8000")),
        )
    else:
        mcp.run()


if __name__ == "__main__":
    main()

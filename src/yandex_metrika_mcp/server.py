"""Yandex Metrika MCP — read-only access to Yandex Metrika analytics via MCP.

An aiaiai open-source AI-native tool. Read scope only (`metrika:read`):
the server never creates, edits or deletes anything in the account.

This module is the public engine. It knows how to talk to the Metrika API
given an OAuth token, but it does not know where the token comes from.
The token is supplied through an injectable resolver (`TokenResolver`), so the
same engine powers both standalone BYO-token mode and a hosted multi-tenant
backend. See docs/contract.md.
"""

from __future__ import annotations

import os
from typing import Awaitable, Callable

import httpx
from fastmcp import FastMCP

API_BASE = "https://api-metrika.yandex.net"
TOKEN_ENV = "YANDEX_METRIKA_TOKEN"

# A resolver returns a valid `metrika:read` OAuth token for the CURRENT request.
TokenResolver = Callable[[], Awaitable[str]]


class YandexMetrikaClient:
    """Thin async client over the Yandex Metrika API, scoped to one token.

    A client instance carries a single OAuth token. Construct a fresh client
    per request from a resolver so per-user token isolation is preserved.
    """

    def __init__(self, token: str) -> None:
        self._token = token

    async def _get(self, path: str, params: dict) -> dict:
        """GET a Metrika API endpoint with OAuth auth and return parsed JSON."""
        headers = {"Authorization": f"OAuth {self._token}"}
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{API_BASE}{path}", params=params, headers=headers
            )
            resp.raise_for_status()
            return resp.json()

    async def list_counters(self) -> list[dict]:
        """List the counters available to the token.

        Returns each counter's id, name and site.
        """
        data = await self._get("/management/v1/counters", {"per_page": 1000})
        return [
            {"id": c["id"], "name": c.get("name"), "site": c.get("site")}
            for c in data.get("counters", [])
        ]

    async def query(
        self,
        counter_id: int,
        metrics: str,
        dimensions: str | None = None,
        date1: str = "7daysAgo",
        date2: str = "today",
        filters: str | None = None,
        sort: str | None = None,
        limit: int = 100,
    ) -> dict:
        """Run a Reporting API query against a counter (aggregated stats).

        Returns the raw Reporting API response (query meta, totals and rows).
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
        return await self._get("/stat/v1/data", params)


def build_server(
    *,
    token_resolver: TokenResolver,
    auth=None,
    name: str = "yandex-metrika-mcp",
) -> FastMCP:
    """Build a configured FastMCP server exposing the read-only Metrika tools.

    Registers `list_counters` and `query`. Each tool obtains a token via
    `await token_resolver()` and calls `YandexMetrikaClient(token)`. The
    `auth` argument (if given) is passed straight through to `FastMCP(auth=...)`,
    which is how the hosted backend wires in its OAuthProxy.
    """
    mcp = FastMCP(name, auth=auth)

    @mcp.tool
    async def list_counters() -> list[dict]:
        """List Yandex Metrika counters available to the token.

        Returns each counter's id, name and site so you can pick a `counter_id`
        for `query`. Read scope is enough.
        """
        token = await token_resolver()
        return await YandexMetrikaClient(token).list_counters()

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
        """Run a Reporting API query against a Metrika counter (aggregated stats).

        Pass Metrika field names directly. Common ones:

        Metrics (comma-separated):
          ym:s:visits, ym:s:users, ym:s:pageviews, ym:s:bounceRate,
          ym:s:avgVisitDurationSeconds, ym:s:newUsers

        Dimensions (comma-separated, optional — groups the result):
          ym:s:date, ym:s:lastTrafficSource, ym:s:startURL,
          ym:s:deviceCategory, ym:s:regionCountry, ym:s:<attribution>UTMSource

        date1 / date2: YYYY-MM-DD or relative (today, yesterday, NdaysAgo).
        filters: Metrika filter expression, e.g. "ym:s:deviceCategory=='mobile'".
        sort: field to sort by; prefix with '-' for descending, e.g. "-ym:s:visits".

        Returns the raw Reporting API response (query meta, totals and data rows).
        """
        token = await token_resolver()
        return await YandexMetrikaClient(token).query(
            counter_id=counter_id,
            metrics=metrics,
            dimensions=dimensions,
            date1=date1,
            date2=date2,
            filters=filters,
            sort=sort,
            limit=limit,
        )

    return mcp


async def env_token_resolver() -> str:
    """Standalone resolver: read the token from the environment (BYO-token)."""
    token = os.environ.get(TOKEN_ENV)
    if not token:
        raise RuntimeError(
            f"{TOKEN_ENV} is not set. Create an OAuth token with the `metrika:read` "
            f"scope at https://oauth.yandex.ru and export it as {TOKEN_ENV}."
        )
    return token


def main() -> None:
    # Transport is stdio by default (local clients like Claude Desktop).
    # Set MCP_TRANSPORT=http for the hosted/remote deployment.
    server = build_server(token_resolver=env_token_resolver)
    transport = os.environ.get("MCP_TRANSPORT", "stdio")
    if transport == "http":
        server.run(
            transport="http",
            host=os.environ.get("HOST", "0.0.0.0"),
            port=int(os.environ.get("PORT", "8000")),
        )
    else:
        server.run()


if __name__ == "__main__":
    main()

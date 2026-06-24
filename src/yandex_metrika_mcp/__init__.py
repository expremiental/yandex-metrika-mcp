"""Read-only MCP server for Yandex Metrika analytics.

Public engine. Exposes the token-resolver seam from docs/contract.md so the
same code powers standalone BYO-token mode and a hosted multi-tenant backend.
"""

from .server import (
    API_BASE,
    TOKEN_ENV,
    TokenResolver,
    YandexMetrikaClient,
    build_server,
    env_token_resolver,
    main,
)

__version__ = "0.1.0"

__all__ = [
    "API_BASE",
    "TOKEN_ENV",
    "TokenResolver",
    "YandexMetrikaClient",
    "build_server",
    "env_token_resolver",
    "main",
]

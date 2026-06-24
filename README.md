# yandex-metrica-mcp

Спрашивай **Яндекс.Метрику** обычным языком — прямо в Claude. «Сколько визитов за неделю?», «топ источников за месяц», «доля мобильных?» — ассистент сам сходит в Метрику и ответит. Без дашбордов и отчётов.

Open-source инструмент от [aiaiai](https://getaiaiai.ru) — мы строим то, чему учим.

## Подключить за минуту

Ставить ничего не нужно — это готовый сервис, он просто подключается к твоему AI:

1. В Claude открой **коннекторы** (Settings → Connectors) и добавь новый по адресу:
   ```
   https://metrica-mcp.getaiaiai.ru/mcp
   ```
2. Нажми **Подключить** → **войди через Яндекс** → разреши доступ.
3. Готово. Спроси: *«покажи мои счётчики»* или *«сколько визитов на сайте за неделю?»*

Своё приложение, токены, ключи — **ничего создавать не надо.** Доступ **только на чтение**: сервис ничего не меняет и не удаляет в твоей Метрике.

<!-- TODO демо-GIF: подключение → вход через Яндекс → вопрос про трафик → ответ -->

## Что можно спросить

- «Сколько визитов и пользователей за неделю?»
- «Топ источников трафика за июнь.»
- «Какая доля мобильного трафика на этой неделе?»
- «Покажи мои счётчики.»

---

## Бонус: self-host со своими ключами

<details>
<summary>Для разработчиков — крутить движок у себя со своим токеном (полный контроль над данными). Развернуть.</summary>

Open-source MCP-сервер на Python (FastMCP). Нужны Python 3.10+ и [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/expremiental/yandex-metrica-mcp.git
cd yandex-metrica-mcp
uv sync
```

**Токен.** На [oauth.yandex.ru](https://oauth.yandex.ru) создай приложение (платформа «Веб-сервисы»), включи доступ **Яндекс.Метрика → Получение статистики, чтение параметров** (`metrika:read`), получи OAuth-токен:

```bash
export YANDEX_METRIKA_TOKEN="<токен>"
```

**Подключение** (Claude Desktop / Cursor — в `mcpServers`):

```json
{
  "mcpServers": {
    "yandex-metrica": {
      "command": "uv",
      "args": ["run", "yandex-metrica-mcp"],
      "env": { "YANDEX_METRIKA_TOKEN": "<токен>" }
    }
  }
}
```

**Remote по HTTP:**
```bash
MCP_TRANSPORT=http PORT=8000 uv run yandex-metrica-mcp   # endpoint: http://<host>:8000/mcp
```

**Инструменты:** `list_counters` (список счётчиков) и `query` (произвольный отчёт Reporting API). Скоуп только `metrika:read`.

**Встраивание.** Движок получает токен через инъектируемый async-резолвер — можно обернуть своей авторизацией:
```python
from yandex_metrica_mcp import build_server
async def token_resolver() -> str: return "<metrika:read token>"
build_server(token_resolver=token_resolver).run(transport="stdio")
```
Экспорт: `build_server`, `YandexMetrikaClient`, `TokenResolver`, `env_token_resolver`, `main`.

</details>

## Roadmap

- [ ] Ещё проще подключение для нетехнарей (one-click / agent-driven)
- [ ] Хелперы под частые отчёты (трафик, источники, конверсии)
- [ ] **Яндекс.Директ** — реклама в том же сервере

## Лицензия

[MIT](LICENSE) · сделано в [aiaiai](https://getaiaiai.ru)

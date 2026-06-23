# yandex-metrica-mcp

Read-only MCP-сервер для **Яндекс.Метрики**. Подключаешь к Claude / Cursor / ChatGPT и спрашиваешь про трафик, источники и конверсии обычным языком — модель сама ходит в API Метрики и приносит цифры.

Open-source инструмент от [aiaiai](https://getaiaiai.ru) — мы строим то, чему учим.

> ✅ **Статус: ядро работает локально.** Оба tool'а (`list_counters`, `query`) проверены против живого API Метрики через FastMCP-сервер. Дальше — hosted multi-tenant (см. [Roadmap](#roadmap)).

## Что умеет (MVP)

| Tool | Что делает |
|------|-----------|
| `list_counters` | Показать доступные счётчики (id, имя, сайт) — чтобы выбрать, по какому спрашивать |
| `query` | Произвольный отчёт через Reporting API: метрики, измерения, период, фильтры, сортировка |

**Только чтение.** Сервер ничего не меняет и не удаляет — нужен OAuth-скоуп `metrika:read`, и только он.

## Установка (dev)

Пока репозиторий не опубликован — запуск из исходников:

```bash
# из корня движка (папка mcp/)
uv sync          # или: pip install -e .
```

## Токен

1. Зайди на [oauth.yandex.ru](https://oauth.yandex.ru), создай приложение, запроси доступ **Яндекс.Метрика → получение статистики (`metrika:read`)**.
2. Получи OAuth-токен и положи в окружение:

```bash
export YANDEX_METRIKA_TOKEN="<твой токен>"
```

(см. `.env.example`)

## Подключение к клиенту

Claude Desktop / Cursor — в `mcpServers`:

```json
{
  "mcpServers": {
    "yandex-metrica": {
      "command": "uv",
      "args": ["run", "yandex-metrica-mcp"],
      "env": { "YANDEX_METRIKA_TOKEN": "<твой токен>" }
    }
  }
}
```

## Self-host по HTTP (remote)

Тот же сервер по Streamable HTTP — для remote-клиентов:

```bash
MCP_TRANSPORT=http HOST=0.0.0.0 PORT=8000 uv run yandex-metrica-mcp
# endpoint: http://<host>:8000/mcp
```

По умолчанию транспорт `stdio`. При `MCP_TRANSPORT=http`: `HOST` (по умолчанию `0.0.0.0`), `PORT` (по умолчанию `8000`).

## Встраивание движка (advanced)

Движок не знает про OAuth и хранилища — токен он получает через инъектируемый резолвер. Это тот же стык, на котором приватный hosted-backend подключает свой OAuth (см. `../docs/contract.md`).

```python
import os
from yandex_metrica_mcp import build_server, YandexMetrikaClient

async def my_token_resolver() -> str:
    return os.environ["YANDEX_METRIKA_TOKEN"]   # или достать из своего стора

server = build_server(token_resolver=my_token_resolver, auth=None)
server.run(transport="stdio")

# или напрямую клиентом, без MCP:
counters = await YandexMetrikaClient(token).list_counters()
```

Экспортируется из пакета: `YandexMetrikaClient`, `TokenResolver`, `build_server`, `env_token_resolver`, `main`.

## Примеры запросов

- «Сколько визитов и пользователей за последние 7 дней на счётчике 110088107?»
- «Топ источников трафика за июнь, по визитам.»
- «Какая доля мобильного трафика на этой неделе?»

## Roadmap

- [x] Прогнать `query`/`list_counters` против живого API (✓ 23.06.2026, 4 счётчика, данные отдаёт)
- [ ] Хелперы под частые отчёты (трафик, источники, конверсии) — чтобы модель меньше угадывала имена метрик
- [ ] **Яндекс.Директ** (реклама) — наш дифференциатор: в MCP его не делает никто
- [ ] Хостед-вариант: подключение без локального сетапа (воронка в aiaiai)
- [ ] Выезд в отдельный публичный репозиторий

## Лицензия

[MIT](LICENSE)

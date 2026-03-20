# Remote Playwright Grid (Docker)

This setup runs a Playwright server on `ws://127.0.0.1:9323/`.

## Start

```bash
docker compose -f tools/remote/docker-compose.yml up -d
```

## Stop

```bash
docker compose -f tools/remote/docker-compose.yml down
```

## Run tests on remote browser

```bash
IS_GRID_AVAILABLE=1 GRID_WS_ENDPOINT=ws://127.0.0.1:9323/ python -m pytest -m smoke -q
```

## Grid provider selection

- `GRID_PROVIDER=auto` (default): tries Playwright endpoint first, then Selenium CDP bridge.
- `GRID_PROVIDER=playwright`: forces Playwright protocol (`browser_type.connect`).
- `GRID_PROVIDER=selenium_cdp`: forces Selenium Grid CDP bridge (`connect_over_cdp`, Chromium-only).

### Selenium Grid hub example (`:4444`)

```bash
IS_GRID_AVAILABLE=1 GRID_PROVIDER=auto GRID_WS_ENDPOINT=http://127.0.0.1:4444 python -m pytest -m smoke -q
```

If your grid does not expose CDP in capabilities, provide explicit endpoint:

```bash
IS_GRID_AVAILABLE=1 GRID_PROVIDER=selenium_cdp GRID_WS_ENDPOINT=http://127.0.0.1:4444 GRID_CDP_ENDPOINT=http://127.0.0.1:9222 python -m pytest -m smoke -q
```

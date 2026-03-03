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

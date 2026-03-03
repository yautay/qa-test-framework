# Local MinIO for visual baselines

Starts local MinIO instance for baseline storage tests.

## Start

```bash
docker compose -f tools/minio/docker-compose.yml up -d
```

## Console

- URL: `http://127.0.0.1:9001`
- User: `minioadmin`
- Password: `minioadmin`

## S3 endpoint

- `http://127.0.0.1:9000`

## Stop

```bash
docker compose -f tools/minio/docker-compose.yml down
```

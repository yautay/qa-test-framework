# Local MinIO for visual baselines

Starts local MinIO instance for baseline storage tests.

Compose also runs one-shot `minio-init` that:

- creates bucket `visual-baselines` (or `MINIO_BUCKET` override),
- creates users `visual-readonly` and `visual-release`,
- attaches policies from `tools/minio/policies/`,
- sets bucket quota (`MINIO_BUCKET_QUOTA`, default: `20GiB`).

## Optional overrides

You can export env vars before start:

```bash
export MINIO_ROOT_USER=minioadmin
export MINIO_ROOT_PASSWORD=minioadmin
export MINIO_BUCKET=visual-baselines
export MINIO_BUCKET_QUOTA=20GiB
export VISUAL_READONLY_USER=visual-readonly
export VISUAL_READONLY_PASSWORD=readonly-pass-change-me
export VISUAL_RELEASE_USER=visual-release
export VISUAL_RELEASE_PASSWORD=release-pass-change-me
```

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

## Suggested framework credentials

Local developer `.env` should use readonly user:

```env
VISUAL_BASELINE_PROVIDER=minio
VISUAL_MINIO_ENDPOINT=127.0.0.1:9000
VISUAL_MINIO_BUCKET=visual-baselines
VISUAL_MINIO_ACCESS_KEY=visual-readonly
VISUAL_MINIO_SECRET_KEY=readonly-pass-change-me
VISUAL_MINIO_SECURE=0
```

Release operations without CI:

- keep readonly values in `.env`,
- use interactive prompt for release credentials:

```bash
python tools/visual/version_baselines.py create \
  --from-version latest \
  --to-version 2026-03-03_1 \
  --with-minio \
  --apply \
  --ask-release-credentials

python tools/visual/retention_baselines.py \
  --with-minio \
  --apply \
  --ask-release-credentials
```

## Stop

```bash
docker compose -f tools/minio/docker-compose.yml down
```

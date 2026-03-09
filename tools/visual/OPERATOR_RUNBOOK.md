# Visual Baseline Operator Runbook

This runbook describes a minimal operator flow for baseline lifecycle.

## Quick cheat sheet

```bash
# 0) Debug MinIO permissions (readonly/release)
python tools/visual/debug.py --check-profile readonly --src-key qa/visual/baselines/sample_suite/default/latest/sample.png --dst-key qa/visual/baselines/_debug/tmp/sample-copy.png
python tools/visual/debug.py --check-profile release --ask-release-credentials --src-key qa/visual/baselines/sample_suite/default/latest/sample.png --dst-key qa/visual/baselines/_debug/tmp/sample-copy.png

# 1) Local promote candidates -> latest
python tools/visual/promote_candidates_local.py --apply

# 2) Create immutable snapshot version
python tools/visual/version_baselines.py create --from-version latest --to-version 2026-03-03_1 --with-minio --force --ask-release-credentials

# 3) Promote snapshot -> latest (with cleanup)
python tools/visual/version_baselines.py promote --from-version 2026-03-03_1 --with-minio --prune-missing --force --ask-release-credentials

# 4) Retention (TTL candidates=7 days, keep 5 versions)
python tools/visual/retention_baselines.py --with-minio --apply --ask-release-credentials

# 5) Verify
python tools/visual/version_baselines.py list --with-minio
python tools/visual/version_baselines.py check --sync-tests --with-minio
```

## 0) Prerequisites

- MinIO started (`docker compose -f tools/minio/docker-compose.yml up -d`),
- local `.env` uses readonly MinIO credentials,
- release credentials are provided only on prompt for write operations.

## 1) Debug MinIO permissions

Readonly account checks (`list/get`):

```bash
python tools/visual/debug.py \
  --check-profile readonly \
  --src-key qa/visual/baselines/sample_suite/default/latest/sample.png \
  --dst-key qa/visual/baselines/_debug/tmp/sample-copy.png
```

Release account checks (`list/get/copy/delete` with temporary scratch path):

```bash
python tools/visual/debug.py \
  --check-profile release \
  --ask-release-credentials \
  --src-key qa/visual/baselines/sample_suite/default/latest/sample.png \
  --dst-key qa/visual/baselines/_debug/tmp/sample-copy.png
```

In `--check-profile auto` (default), release checks are skipped automatically when credentials are readonly.

## 2) Review and approve candidates in report UI

```bash
make test-visual
make report-serve
```

In UI:

- open run,
- tag rows with `BASELINE`,
- click `SEND BASELINE`.

Effect: selected images are written to local `candidates` lane.

## 3) Promote candidates to latest locally

Dry-run:

```bash
python tools/visual/promote_candidates_local.py
```

Apply:

```bash
python tools/visual/promote_candidates_local.py --apply
```

Optional cleanup of stale latest targets:

```bash
python tools/visual/promote_candidates_local.py --prune-missing --apply
```

## 4) Create version snapshot

Dry-run:

```bash
python tools/visual/version_baselines.py create --from-version latest --to-version 2026-03-03_1
```

Apply (local + MinIO with prompt credentials):

```bash
python tools/visual/version_baselines.py create \
  --from-version latest \
  --to-version 2026-03-03_1 \
  --with-minio \
  --force \
  --ask-release-credentials
```

Effect: creates versioned baselines and manifest file.

## 5) Promote version to latest

Dry-run:

```bash
python tools/visual/version_baselines.py promote --from-version 2026-03-03_1 --with-minio
```

Apply:

```bash
python tools/visual/version_baselines.py promote \
  --from-version 2026-03-03_1 \
  --with-minio \
  --prune-missing \
  --force \
  --ask-release-credentials
```

## 6) Apply retention policy

Policy defaults:

- candidates TTL: 7 days,
- keep 5 latest historical versions per suite,
- `latest` is retained.

Dry-run:

```bash
python tools/visual/retention_baselines.py --with-minio
```

Apply:

```bash
python tools/visual/retention_baselines.py \
  --with-minio \
  --apply \
  --ask-release-credentials
```

## 7) Verify state

```bash
# list output now contains per-tag file/size stats and TOTAL
python tools/visual/version_baselines.py list
python tools/visual/version_baselines.py list --with-minio

# detect stale baseline PNGs no longer mapped to active scenarios (dry-run)
python tools/visual/version_baselines.py check --sync-tests
python tools/visual/version_baselines.py check --sync-tests --with-minio
```

Check manifest for promoted version:

- `qa/visual/baselines/_manifests/<profile>/<version>.json`

# DBeaver Export From Wizard

Script parses Test Wizard DOM and generates connection files ready for DBeaver import.

## What it does

- Opens wizard page with Playwright and `Authorization` header.
- Extracts MySQL and MariaDB connection details per test VM.
- Applies credentials/schemas overrides from local config.
- Generates:
  - `out/wizard_db_connections.json` (raw + normalized dump)
  - `out/dbeaver_data-sources.json` (for `.dbeaver/data-sources*.json` workflow)
  - `out/dbeaver_connections_import.csv` (fallback import through DBeaver UI)

## Setup

1. Copy template:

```bash
cp tools/dbeaver/db_dump_config.example.json tools/dbeaver/db_dump_config.json
```

2. Fill values in `tools/dbeaver/db_dump_config.json`:

- `wizard.auth_header` (or use env `WIZARD_AUTH_HEADER`)
- `testovki.<vm>.mysql.username/password`
- `testovki.<vm>.mariadb.schemas[]` with schema-level credentials
- optional host filtering in `filters.include_host_tokens` / `filters.exclude_host_tokens`

## Run

```bash
python tools/dbeaver/export_wizard_connections.py
python tools/dbeaver/export_wizard_connections.py --vm example-vm
python tools/dbeaver/export_wizard_connections.py --config tools/dbeaver/db_dump_config.json --out-dir tools/dbeaver/out
python tools/dbeaver/export_wizard_connections.py --exclude-host be124
python tools/dbeaver/export_wizard_connections.py --include-host node2 --exclude-host be124,be115
```

## DBeaver usage

- `dbeaver_data-sources.json`: copy to target project `.dbeaver/data-sources-*.json`.
- `dbeaver_connections_import.csv`: in DBeaver use import from CSV/XML.

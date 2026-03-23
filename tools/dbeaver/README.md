# DBeaver Export From Wizard

Script parses Test Wizard DOM and generates connection files ready for DBeaver import.

## What it does

- Opens wizard page with Playwright and `Authorization` header.
- Extracts MySQL and MariaDB connection details per test VM.
- Applies credentials/schemas overrides from local config.
- Generates:
  - `out/wizard_db_connections.json` (raw + normalized dump)
  - `out/dbeaver_data-sources.json` (for `.dbeaver/data-sources*.json` workflow)
  - `out/dbeaver_credentials-config.json` (for `.dbeaver/credentials-config.json` workflow)
  - `out/dbeaver_connections_import.csv` (fallback import through DBeaver UI)

## Setup

1. Copy template:

```bash
cp tools/dbeaver/db_dump_config.example.json tools/dbeaver/db_dump_config.json
```

2. Fill values in `tools/dbeaver/db_dump_config.json`:

- `wizard.auth_header` (or use env `WIZARD_AUTH_HEADER`)
- `test_vm.<vm>.mysql.username/password`
- `defaults.mariadb-<service>` for microservice credentials/schema (e.g. `mariadb-promotions`)
- `test_vm.<vm>.mariadb.schemas[]` for VM-specific schema-level overrides
- `dbeaver.copy_enabled` + `dbeaver.target_data_sources_path` for optional auto-copy after generation
- `dbeaver.target_credentials_config_path` (optional; default is sibling `credentials-config.json` next to `target_data_sources_path`)
- `dbeaver.create_target_dir` to auto-create missing destination directory
- optional host filtering in `filters.include_host_tokens` / `filters.exclude_host_tokens`

## Run

```bash
python tools/dbeaver/export_wizard_connections.py
python tools/dbeaver/export_wizard_connections.py --vm example-vm
python tools/dbeaver/export_wizard_connections.py --config tools/dbeaver/db_dump_config.json --out-dir tools/dbeaver/out
python tools/dbeaver/export_wizard_connections.py --exclude-host be124
python tools/dbeaver/export_wizard_connections.py --include-host node2 --exclude-host be124,be115
python tools/dbeaver/export_wizard_connections.py --test_vm perpetum.gamma
python tools/dbeaver/export_wizard_connections.py --test_vm "[perpetum.gamma, selenium.alfa]"
python tools/dbeaver/export_wizard_connections.py --copy-to-dbeaver --create-target-dir --dbeaver-target-path "~/.local/share/DBeaverData/workspace6/General/.dbeaver/data-sources-local.json" --dbeaver-credentials-path "~/.local/share/DBeaverData/workspace6/General/.dbeaver/credentials-config.json"
```

## DBeaver usage

- `dbeaver_data-sources.json`: copy to target project `.dbeaver/data-sources-*.json`.
- `dbeaver_credentials-config.json`: copy to `.dbeaver/credentials-config.json`.
- `dbeaver_connections_import.csv`: in DBeaver use import from CSV/XML.
- Auto-copy can be enabled by config (`dbeaver.copy_enabled: true`) or CLI (`--copy-to-dbeaver`).
- Destination directory can be auto-created by config (`dbeaver.create_target_dir: true`) or CLI (`--create-target-dir`).
- Credentials target path can be set in config (`dbeaver.target_credentials_config_path`) or CLI (`--dbeaver-credentials-path`).
- During auto-copy, existing top-level metadata (e.g. `connection-types`) in target file is preserved.

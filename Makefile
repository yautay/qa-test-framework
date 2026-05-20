ifeq ($(OS),Windows_NT)
PYTHON ?= python
else
ifneq ($(wildcard .venv/bin/python),)
PYTHON ?= .venv/bin/python
else
PYTHON ?= python3
endif
endif

PYTEST ?= $(PYTHON) -m pytest

.DEFAULT_GOAL := help

.PHONY: help report-serve test test-api test-visual test-e2e test-aso test-smoke test-smoke-prod-pl test-setup test-flaky check collect lint format format-check typecheck security verify-discovery verify-scenarios clean clean-artifacts clean-artifacts-older debug-remote-grid-up debug-remote-grid-down debug-minio-up debug-minio-down local-settings-ignore local-settings-track

help: ## Show this help
	$(PYTHON) tools/make/make_help.py
##@ Framework

report-serve: ## Uruchom lokalny serwer raportu visual
	$(PYTHON) -m framework.reporting.report_server $(if $(RUN_ID),--run-id $(RUN_ID),) $(if $(REPORT_DIR),--report-dir $(REPORT_DIR),) $(if $(PORT),--port $(PORT),)

##@ Tests

test: ## Uruchom wszystkie testy
	$(PYTEST) -q

test-api: ## Testy api
	$(PYTEST) -m api -q

test-visual: ## Testy regresji wizualnej
	$(PYTEST) -m visual -q

test-e2e: ## Testy funkcjonalne
	$(PYTEST) -m e2e -q

test-aso: ## Testy oznaczone markerem aso
	$(PYTEST) -m aso -q

test-smoke: ## Testy dymne
	$(PYTEST) qa/e2e/netcorner/nuxt/pl/tests/tests_smoke/test_smoke_basic_orders.py -m e2e_smoke -q

test-smoke-prod-pl: ## Smoke PL basic orders na prod (grid/headless off)
	IS_GRID_AVAILABLE=0 HEADLESS=0 $(PYTEST) qa/e2e/netcorner/nuxt/pl/tests/tests_smoke/test_smoke_basic_orders.py --server-name=prod -q

test-setup: ## Setupy środowiskowe Netcorner NUxT
	$(PYTEST) qa/e2e/netcorner/setup/tests -n 4 -q

test-flaky: ## Wykrywanie niestabilnych testów e2e_pl (flake-finder)
	$(PYTEST) \
	-m e2e_pl \
	--randomly-seed=$(shell date +%s) \
	--flake-finder \
	--flake-runs=10


##@ Development

check: ## Full check pipeline
check: test-aso lint format-check typecheck security verify-discovery verify-scenarios collect

collect: ## Collect-only (pytest)
	$(PYTEST) --collect-only -q

lint: ## Ruff lint
	$(PYTHON) -m ruff check qa framework tools

format: ## Formatowanie black
	$(PYTHON) -m black qa framework tools

format-check: ## Sprawdzenie formatowania
	$(PYTHON) -m black --check qa framework tools

typecheck: ## MyPy typecheck
	$(PYTHON) -m mypy qa framework tools

security: ## Bandit + pip-audit
	$(PYTHON) -m bandit -r -x qa --skip B101,B105,B106,B110,B112,B404,B603,B607,B311 framework tools
	$(PYTHON) -m pip_audit

verify-discovery: ## Guard dla pytest discovery
	$(PYTHON) framework/pytest_discovery_guard.py

verify-scenarios: ## Weryfikacja scenariuszy
	$(PYTHON) tools/scenarios/verify_scenarios.py


##@ Helpers

clean: ## Pelne sprzątanie lokalnych artefaktów i cache
	$(PYTHON) tools/artifacts/cleanup.py --all

clean-artifacts: ## Usuń artefakty runów, logi tools i common cache
	$(PYTHON) tools/artifacts/cleanup.py --all

clean-artifacts-older: ## Usuń artefakty starsze niż DAYS (domyślnie 14)
	$(PYTHON) tools/artifacts/cleanup.py --days $(if $(DAYS),$(DAYS),14)

debug-remote-grid-up: ## Uruchom lokalny Playwright grid przez Docker Compose
	docker compose -f tools/remote/docker-compose.yml up -d

debug-remote-grid-down: ## Zatrzymaj lokalny Playwright grid przez Docker Compose
	docker compose -f tools/remote/docker-compose.yml down

debug-minio-up: ## Uruchom lokalne MinIO przez Docker Compose
	docker compose -f tools/minio/docker-compose.yml up -d

debug-minio-down: ## Zatrzymaj lokalne MinIO przez Docker Compose
	docker compose -f tools/minio/docker-compose.yml down

local-settings-ignore: ## Ustaw skip-worktree dla settings.py i settings_cli.py
	git update-index --skip-worktree settings.py settings_cli.py

local-settings-track: ## Cofnij skip-worktree dla settings.py i settings_cli.py
	git update-index --no-skip-worktree settings.py settings_cli.py


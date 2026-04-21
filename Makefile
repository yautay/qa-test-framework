ifeq ($(OS),Windows_NT)
PYTHON ?= python
else
PYTHON ?= python3
endif

PYTEST ?= $(PYTHON) -m pytest

.DEFAULT_GOAL := help

.PHONY: help report-serve test test-api test-visual test-e2e test-aso test-smoke check collect lint format format-check typecheck security verify-discovery verify-scenarios clean clean-artifacts clean-artifacts-older debug-remote-grid-up debug-remote-grid-down debug-minio-up debug-minio-down

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
	$(PYTEST) -m smoke -q


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


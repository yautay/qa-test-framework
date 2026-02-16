ifeq ($(OS),Windows_NT)
PYTHON ?= python
else
PYTHON ?= python3
endif

PYTEST ?= $(PYTHON) -m pytest

.DEFAULT_GOAL := help

.PHONY: help test test-aso test-functional test-visual validate-config visual-validate visual-sync visual-approve clean-artifacts clean-artifacts-older collect lint format format-check typecheck security verify-discovery verify-scenarios scenario-report test-api remote-up remote-down remote-smoke minio-up minio-down check

help: ## Show this help
	$(PYTHON) tools/make/make_help.py

##@ Tests

test: ## Uruchom wszystkie testy
	$(PYTEST)

test-functional: ## Testy funkcjonalne
	$(PYTEST) -m "not aso"

test-smoke: ## Testy dymne
	$(PYTEST) -m "smoke"

test-api: ## Testy api
	$(PYTEST) -m "api"

test-visual: ## Testy regresji wizualnej
	REPORTING_ENABLED=0 VISUAL_ENABLED=1 $(PYTEST) -m visual -q

##@ Development

validate-config: ## Walidacja konfiguracji (scenariusze + visual)
validate-config: verify-scenarios visual-validate

check: ## Full check pipeline
check: lint format-check typecheck security verify-discovery validate-config collect

test-aso: ## Testy oznaczone markerem aso (bez reportingu)
	$(MAKE) validate-config
	REPORTING_ENABLED=0 $(PYTEST) -m aso -q

collect: ## Collect-only (pytest)
	$(PYTEST) --collect-only -q

lint: ## Ruff lint
	$(PYTHON) -m ruff check qa framework

format: ## Formatowanie black
	$(PYTHON) -m black qa framework

format-check: ## Sprawdzenie formatowania
	$(PYTHON) -m black --check qa framework

typecheck: ## MyPy typecheck
	$(PYTHON) -m mypy qa framework

security: ## Bandit + pip-audit
	$(PYTHON) -m bandit -q -r qa framework
	$(PYTHON) -m pip_audit

verify-discovery: ## Guard dla pytest discovery
	$(PYTHON) framework/pytest_discovery_guard.py

verify-scenarios: ## Weryfikacja scenariuszy
	$(PYTHON) tools/scenarios/verify_scenarios.py

scenario-report: ## Raport scenariuszy
	$(PYTHON) tools/scenarios/scenario_report.py

test-api: ## Test API reportingu
	$(PYTHON) tools/reporting/test_api.py

##@ Regresja wizualna

visual-validate: ## Walidacja scenariuszy visual
	$(PYTHON) tools/visual/validate_scenarios.py

visual-sync: ## Synchronizacja visual baseline
	$(PYTHON) tools/visual/sync_baseline.py

visual-approve: ## Akceptacja zmian visual
	REPORTING_ENABLED=0 VISUAL_ENABLED=1 $(PYTEST) -m visual -q --visual-approve

##@ Helpers

clean-artifacts: ## Usuń wszystkie artefakty
	$(PYTHON) tools/artifacts/cleanup.py --all

clean-artifacts-older: ## Usuń artefakty starsze niż DAYS (domyślnie 14)
	$(PYTHON) tools/artifacts/cleanup.py --days $(if $(DAYS),$(DAYS),14)

##@ Debug

remote-up: ## Start grid remote (docker)
	docker compose -f tools/remote/docker-compose.yml up -d

remote-down: ## Stop grid remote (docker)
	docker compose -f tools/remote/docker-compose.yml down

remote-smoke: ## Smoke testy na remote grid
	IS_GRID_AVAILABLE=1 GRID_WS_ENDPOINT=ws://127.0.0.1:9323/ $(PYTEST) -m smoke -q

minio-up: ## Start MinIO
	docker compose -f tools/minio/docker-compose.yml up -d

minio-down: ## Stop MinIO
	docker compose -f tools/minio/docker-compose.yml down


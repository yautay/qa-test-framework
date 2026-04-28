#!/bin/bash
# =============================================================================
# Benchmark E2E: headless seq vs xdist -n 2/3/4
# Uruchomienie: bash tools/benchmark/run_benchmark.sh
# Wyniki: bench_raw_<timestamp>.txt w katalogu głównym repo
# =============================================================================

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

TEST_FILE="qa/e2e/netcorner/nuxt/pl/tests/tests_orders/test_basic_orders.py"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
RESULTS_FILE="bench_raw_${TIMESTAMP}.txt"
RUNS_PER_MODE=5

# --- konfiguracja trybów ---------------------------------------------------
# Każdy tryb: "label|extra_pytest_args"
MODES=(
    "headless-seq|"
    "xdist-n2|-n 2"
    "xdist-n3|-n 3"
    "xdist-n4|-n 4"
)

# --- env vars wspólne dla wszystkich runów ----------------------------------
export HEADLESS=1
export REPORTING_ENABLED=0
export ALLURE_ENABLED=0
export PYTEST_HTML_ENABLED=0
export RECORD_VIDEO=0

# --- funkcje ----------------------------------------------------------------

log() {
    echo "$@" | tee -a "$RESULTS_FILE"
}

run_test() {
    local run_num=$1
    local mode_label=$2
    local extra_args=$3

    log ""
    log "=== Run $run_num ($mode_label) ==="
    log "START_TIME=$(date '+%Y-%m-%d %H:%M:%S')"

    local start_ts
    start_ts=$(date +%s%N)

    .venv/bin/python -m pytest "$TEST_FILE" -v --tb=line $extra_args 2>&1 | tee -a "$RESULTS_FILE"
    local exit_code=${PIPESTATUS[0]}

    local end_ts
    end_ts=$(date +%s%N)
    local duration_ms=$(( (end_ts - start_ts) / 1000000 ))
    local duration_s
    duration_s=$(echo "scale=2; $duration_ms / 1000" | bc)

    log "EXIT_CODE=$exit_code"
    log "DURATION_MS=$duration_ms"
    log "DURATION_S=${duration_s}s"
    log "END_TIME=$(date '+%Y-%m-%d %H:%M:%S')"
    log "---END_RUN---"
}

# --- main -------------------------------------------------------------------

log "============================================================"
log "BENCHMARK E2E"
log "Plik: $TEST_FILE"
log "Tryby: ${MODES[*]}"
log "Runów per tryb: $RUNS_PER_MODE"
log "Start: $(date '+%Y-%m-%d %H:%M:%S')"
log "Env: HEADLESS=$HEADLESS REPORTING_ENABLED=$REPORTING_ENABLED"
log "     ALLURE_ENABLED=$ALLURE_ENABLED PYTEST_HTML_ENABLED=$PYTEST_HTML_ENABLED"
log "     RECORD_VIDEO=$RECORD_VIDEO"
log "Platform: $(uname -srm)"
log "Python: $(.venv/bin/python --version 2>&1)"
log "Pytest: $(.venv/bin/python -m pytest --version 2>&1 | head -1)"
log "============================================================"
log ""

for mode_spec in "${MODES[@]}"; do
    IFS='|' read -r mode_label extra_args <<< "$mode_spec"
    log "########################################"
    log "# PHASE: $mode_label"
    log "########################################"
    for i in $(seq 1 $RUNS_PER_MODE); do
        run_test "$i" "$mode_label" "$extra_args"
    done
done

log ""
log "============================================================"
log "BENCHMARK COMPLETED: $(date '+%Y-%m-%d %H:%M:%S')"
log "Results file: $RESULTS_FILE"
log "============================================================"

# --- podsumowanie szybkie ---------------------------------------------------
echo ""
echo "=== QUICK SUMMARY ==="
echo ""
for mode_spec in "${MODES[@]}"; do
    IFS='|' read -r mode_label extra_args <<< "$mode_spec"
    echo "--- $mode_label ---"
    grep -A3 "=== Run.*($mode_label)" "$RESULTS_FILE" | grep -E "DURATION_S|EXIT_CODE" || true
    echo ""
done

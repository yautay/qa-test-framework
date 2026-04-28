#!/bin/bash
# =============================================================================
# Benchmark E2E: headless vs non-headless, seq vs xdist -n 2/3/4
# Uruchomienie: bash tools/benchmark/run_benchmark.sh
# Wyniki: bench_raw_<timestamp>.txt  +  bench_summary_<timestamp>.md
# =============================================================================

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

TEST_FILE="qa/e2e/netcorner/nuxt/pl/tests/tests_orders/test_basic_orders.py"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
RAW_FILE="bench_raw_${TIMESTAMP}.txt"
SUMMARY_FILE="bench_summary_${TIMESTAMP}.md"
RUNS_PER_MODE=2

# --- konfiguracja trybów ---------------------------------------------------
# Format: "label|headless_flag|extra_pytest_args"
#   headless_flag: 1 = headless, 0 = headed (non-headless)
MODES=(
    "headless-seq|1|"
    "headless-xdist-n2|1|-n 2"
    "headless-xdist-n3|1|-n 3"
    "headless-xdist-n4|1|-n 4"
    "headed-seq|0|"
    "headed-xdist-n2|0|-n 2"
    "headed-xdist-n3|0|-n 3"
    "headed-xdist-n4|0|-n 4"
)

# --- env vars wspólne (HEADLESS ustawiany per-run) --------------------------
export REPORTING_ENABLED=0
export ALLURE_ENABLED=0
export PYTEST_HTML_ENABLED=0
export RECORD_VIDEO=0

# --- tablice na wyniki (bash 4+ assoc arrays) -------------------------------
declare -A DURATIONS   # key: "mode_label|run_num"  value: duration_s
declare -A PASSED      # key: "mode_label|run_num"  value: passed_count
declare -A FAILED      # key: "mode_label|run_num"  value: failed_count
declare -A EXITCODES   # key: "mode_label|run_num"  value: exit_code
declare -A FAILURES    # key: "mode_label|run_num"  value: failed test names

# --- funkcje ----------------------------------------------------------------

log() {
    echo "$@" | tee -a "$RAW_FILE"
}

run_test() {
    local run_num=$1
    local mode_label=$2
    local headless_flag=$3
    local extra_args=$4

    export HEADLESS="$headless_flag"

    log ""
    log "=== Run $run_num ($mode_label) HEADLESS=$headless_flag ==="
    log "START_TIME=$(date '+%Y-%m-%d %H:%M:%S')"

    local start_ts
    start_ts=$(date +%s%N)

    local output
    output=$(.venv/bin/python -m pytest "$TEST_FILE" -v --tb=line $extra_args 2>&1) || true
    local exit_code=$?

    echo "$output" | tee -a "$RAW_FILE"

    local end_ts
    end_ts=$(date +%s%N)
    local duration_ms=$(( (end_ts - start_ts) / 1000000 ))
    local duration_s
    duration_s=$(echo "scale=2; $duration_ms / 1000" | bc)

    # Parse pytest summary line, e.g. "5 passed, 2 failed in 120.34s"
    local passed_count=0
    local failed_count=0
    local pytest_time=""
    local summary_line
    summary_line=$(echo "$output" | grep -E "=+ .*(passed|failed).* in " | tail -1 || true)
    if [[ -n "$summary_line" ]]; then
        passed_count=$(echo "$summary_line" | grep -oP '\d+(?= passed)' || echo 0)
        failed_count=$(echo "$summary_line" | grep -oP '\d+(?= failed)' || echo 0)
        pytest_time=$(echo "$summary_line" | grep -oP '[\d.]+(?=s)' | tail -1 || echo "")
    fi
    [[ -z "$passed_count" ]] && passed_count=0
    [[ -z "$failed_count" ]] && failed_count=0

    # Collect FAILED test names
    local failed_tests=""
    failed_tests=$(echo "$output" | grep -E "^FAILED " | sed 's/^FAILED //' | tr '\n' '; ' || true)

    log "EXIT_CODE=$exit_code"
    log "DURATION_MS=$duration_ms"
    log "DURATION_S=${duration_s}s"
    log "PYTEST_TIME=${pytest_time}s"
    log "PASSED=$passed_count"
    log "FAILED=$failed_count"
    log "FAILED_TESTS=$failed_tests"
    log "END_TIME=$(date '+%Y-%m-%d %H:%M:%S')"
    log "---END_RUN---"

    # Store in arrays
    local key="${mode_label}|${run_num}"
    DURATIONS["$key"]="$duration_s"
    PASSED["$key"]="$passed_count"
    FAILED["$key"]="$failed_count"
    EXITCODES["$key"]="$exit_code"
    FAILURES["$key"]="$failed_tests"
}

generate_summary() {
    local f="$SUMMARY_FILE"

    echo "# Benchmark E2E - Zestawienie wyników" > "$f"
    echo "" >> "$f"
    echo "**Data:** $(date '+%Y-%m-%d %H:%M:%S')" >> "$f"
    echo "**Plik testowy:** \`$TEST_FILE\`" >> "$f"
    echo "**Runów per tryb:** $RUNS_PER_MODE" >> "$f"
    echo "**Platform:** $(uname -srm)" >> "$f"
    echo "**Python:** $(.venv/bin/python --version 2>&1)" >> "$f"
    echo "" >> "$f"

    # ---- 1. Tabela podsumowująca ----
    echo "## 1. Podsumowanie" >> "$f"
    echo "" >> "$f"
    echo "| Tryb | Run 1 (s) | Run 2 (s) | Avg (s) | Min (s) | Max (s) | Avg Passed | Avg Failed | Pass Rate |" >> "$f"
    echo "|------|-----------|-----------|---------|---------|---------|------------|------------|-----------|" >> "$f"

    for mode_spec in "${MODES[@]}"; do
        IFS='|' read -r mode_label headless_flag extra_args <<< "$mode_spec"

        local sum_dur=0 min_dur=999999 max_dur=0
        local sum_passed=0 sum_failed=0
        local dur1="" dur2=""

        for i in $(seq 1 $RUNS_PER_MODE); do
            local key="${mode_label}|${i}"
            local d="${DURATIONS[$key]:-0}"
            local p="${PASSED[$key]:-0}"
            local fl="${FAILED[$key]:-0}"

            sum_dur=$(echo "$sum_dur + $d" | bc)
            sum_passed=$(echo "$sum_passed + $p" | bc)
            sum_failed=$(echo "$sum_failed + $fl" | bc)

            if (( $(echo "$d < $min_dur" | bc -l) )); then min_dur="$d"; fi
            if (( $(echo "$d > $max_dur" | bc -l) )); then max_dur="$d"; fi

            if [[ $i -eq 1 ]]; then dur1="$d"; fi
            if [[ $i -eq 2 ]]; then dur2="$d"; fi
        done

        local avg_dur avg_passed avg_failed pass_rate
        avg_dur=$(echo "scale=2; $sum_dur / $RUNS_PER_MODE" | bc)
        avg_passed=$(echo "scale=1; $sum_passed / $RUNS_PER_MODE" | bc)
        avg_failed=$(echo "scale=1; $sum_failed / $RUNS_PER_MODE" | bc)

        local total_tests
        total_tests=$(echo "$sum_passed + $sum_failed" | bc)
        if [[ "$total_tests" != "0" ]]; then
            pass_rate=$(echo "scale=1; $sum_passed * 100 / $total_tests" | bc)
        else
            pass_rate="N/A"
        fi

        echo "| $mode_label | $dur1 | $dur2 | $avg_dur | $min_dur | $max_dur | $avg_passed | $avg_failed | ${pass_rate}% |" >> "$f"
    done

    echo "" >> "$f"

    # ---- 2. Tabele szczegółowe per tryb ----
    echo "## 2. Szczegóły per tryb" >> "$f"
    echo "" >> "$f"

    for mode_spec in "${MODES[@]}"; do
        IFS='|' read -r mode_label headless_flag extra_args <<< "$mode_spec"
        echo "### $mode_label" >> "$f"
        echo "" >> "$f"
        echo "| Run | Czas (s) | Passed | Failed | Exit Code | Failures |" >> "$f"
        echo "|-----|----------|--------|--------|-----------|----------|" >> "$f"

        for i in $(seq 1 $RUNS_PER_MODE); do
            local key="${mode_label}|${i}"
            local d="${DURATIONS[$key]:-0}"
            local p="${PASSED[$key]:-0}"
            local fl="${FAILED[$key]:-0}"
            local ec="${EXITCODES[$key]:-?}"
            local fails="${FAILURES[$key]:-}"
            [[ -z "$fails" ]] && fails="-"
            echo "| $i | $d | $p | $fl | $ec | $fails |" >> "$f"
        done
        echo "" >> "$f"
    done

    # ---- 3. Porównanie speedup xdist vs sekwencyjny ----
    echo "## 3. Speedup: xdist vs sekwencyjne" >> "$f"
    echo "" >> "$f"
    echo "| Porównanie | Avg Seq (s) | Avg xdist (s) | Speedup |" >> "$f"
    echo "|------------|-------------|---------------|---------|" >> "$f"

    # Headless baseline
    local headless_seq_avg=0
    local headless_seq_sum=0
    for i in $(seq 1 $RUNS_PER_MODE); do
        local d="${DURATIONS[headless-seq|$i]:-0}"
        headless_seq_sum=$(echo "$headless_seq_sum + $d" | bc)
    done
    headless_seq_avg=$(echo "scale=2; $headless_seq_sum / $RUNS_PER_MODE" | bc)

    for n in 2 3 4; do
        local xdist_sum=0
        for i in $(seq 1 $RUNS_PER_MODE); do
            local d="${DURATIONS[headless-xdist-n${n}|$i]:-0}"
            xdist_sum=$(echo "$xdist_sum + $d" | bc)
        done
        local xdist_avg
        xdist_avg=$(echo "scale=2; $xdist_sum / $RUNS_PER_MODE" | bc)
        local speedup="N/A"
        if [[ "$xdist_avg" != "0" && "$xdist_avg" != ".00" ]]; then
            speedup=$(echo "scale=2; $headless_seq_avg / $xdist_avg" | bc)
        fi
        echo "| headless-seq vs headless-xdist-n$n | $headless_seq_avg | $xdist_avg | ${speedup}x |" >> "$f"
    done

    # Headed baseline
    local headed_seq_avg=0
    local headed_seq_sum=0
    for i in $(seq 1 $RUNS_PER_MODE); do
        local d="${DURATIONS[headed-seq|$i]:-0}"
        headed_seq_sum=$(echo "$headed_seq_sum + $d" | bc)
    done
    headed_seq_avg=$(echo "scale=2; $headed_seq_sum / $RUNS_PER_MODE" | bc)

    for n in 2 3 4; do
        local xdist_sum=0
        for i in $(seq 1 $RUNS_PER_MODE); do
            local d="${DURATIONS[headed-xdist-n${n}|$i]:-0}"
            xdist_sum=$(echo "$xdist_sum + $d" | bc)
        done
        local xdist_avg
        xdist_avg=$(echo "scale=2; $xdist_sum / $RUNS_PER_MODE" | bc)
        local speedup="N/A"
        if [[ "$xdist_avg" != "0" && "$xdist_avg" != ".00" ]]; then
            speedup=$(echo "scale=2; $headed_seq_avg / $xdist_avg" | bc)
        fi
        echo "| headed-seq vs headed-xdist-n$n | $headed_seq_avg | $xdist_avg | ${speedup}x |" >> "$f"
    done

    echo "" >> "$f"

    # ---- 4. Headless vs Headed porównanie ----
    echo "## 4. Headless vs Headed (ten sam tryb)" >> "$f"
    echo "" >> "$f"
    echo "| Tryb | Headless Avg (s) | Headed Avg (s) | Różnica (s) | Headed / Headless |" >> "$f"
    echo "|------|------------------|----------------|-------------|-------------------|" >> "$f"

    for suffix in "seq" "xdist-n2" "xdist-n3" "xdist-n4"; do
        local hl_sum=0 hd_sum=0
        for i in $(seq 1 $RUNS_PER_MODE); do
            local d_hl="${DURATIONS[headless-${suffix}|$i]:-0}"
            local d_hd="${DURATIONS[headed-${suffix}|$i]:-0}"
            hl_sum=$(echo "$hl_sum + $d_hl" | bc)
            hd_sum=$(echo "$hd_sum + $d_hd" | bc)
        done
        local hl_avg hd_avg diff ratio
        hl_avg=$(echo "scale=2; $hl_sum / $RUNS_PER_MODE" | bc)
        hd_avg=$(echo "scale=2; $hd_sum / $RUNS_PER_MODE" | bc)
        diff=$(echo "scale=2; $hd_avg - $hl_avg" | bc)
        if [[ "$hl_avg" != "0" && "$hl_avg" != ".00" ]]; then
            ratio=$(echo "scale=2; $hd_avg / $hl_avg" | bc)
        else
            ratio="N/A"
        fi
        echo "| $suffix | $hl_avg | $hd_avg | $diff | ${ratio}x |" >> "$f"
    done

    echo "" >> "$f"

    # ---- 5. Flakey analysis ----
    echo "## 5. Flakey testy (padające w >0 runach)" >> "$f"
    echo "" >> "$f"

    declare -A FLAKEY_COUNT
    for mode_spec in "${MODES[@]}"; do
        IFS='|' read -r mode_label headless_flag extra_args <<< "$mode_spec"
        for i in $(seq 1 $RUNS_PER_MODE); do
            local key="${mode_label}|${i}"
            local fails="${FAILURES[$key]:-}"
            if [[ -n "$fails" ]]; then
                IFS=';' read -ra fail_arr <<< "$fails"
                for ft in "${fail_arr[@]}"; do
                    ft=$(echo "$ft" | xargs)  # trim
                    if [[ -n "$ft" ]]; then
                        FLAKEY_COUNT["$ft"]=$(( ${FLAKEY_COUNT["$ft"]:-0} + 1 ))
                    fi
                done
            fi
        done
    done

    if [[ ${#FLAKEY_COUNT[@]} -eq 0 ]]; then
        echo "Brak failed testów - wszystkie przeszły!" >> "$f"
    else
        echo "| Test | Liczba padnięć (z $(( ${#MODES[@]} * RUNS_PER_MODE )) runów) |" >> "$f"
        echo "|------|--------------------------------------------------------------|" >> "$f"
        for test_name in "${!FLAKEY_COUNT[@]}"; do
            echo "| \`$test_name\` | ${FLAKEY_COUNT[$test_name]} |" >> "$f"
        done
    fi

    echo "" >> "$f"
    echo "---" >> "$f"
    echo "*Wygenerowano automatycznie przez \`tools/benchmark/run_benchmark.sh\`*" >> "$f"

    echo ""
    echo "Summary written to: $f"
}

# --- main -------------------------------------------------------------------

log "============================================================"
log "BENCHMARK E2E - Headless + Headed"
log "Plik: $TEST_FILE"
log "Tryby: ${MODES[*]}"
log "Runów per tryb: $RUNS_PER_MODE"
log "Start: $(date '+%Y-%m-%d %H:%M:%S')"
log "Env: REPORTING_ENABLED=$REPORTING_ENABLED"
log "     ALLURE_ENABLED=$ALLURE_ENABLED PYTEST_HTML_ENABLED=$PYTEST_HTML_ENABLED"
log "     RECORD_VIDEO=$RECORD_VIDEO"
log "Platform: $(uname -srm)"
log "Python: $(.venv/bin/python --version 2>&1)"
log "Pytest: $(.venv/bin/python -m pytest --version 2>&1 | head -1)"
log "============================================================"
log ""

for mode_spec in "${MODES[@]}"; do
    IFS='|' read -r mode_label headless_flag extra_args <<< "$mode_spec"
    log "########################################"
    log "# PHASE: $mode_label (HEADLESS=$headless_flag)"
    log "########################################"
    for i in $(seq 1 $RUNS_PER_MODE); do
        run_test "$i" "$mode_label" "$headless_flag" "$extra_args"
    done
done

log ""
log "============================================================"
log "BENCHMARK COMPLETED: $(date '+%Y-%m-%d %H:%M:%S')"
log "Raw results file: $RAW_FILE"
log "============================================================"

# --- generuj podsumowanie markdown -----------------------------------------
generate_summary

# --- szybki podgląd w terminalu ---------------------------------------------
echo ""
echo "=== QUICK SUMMARY ==="
echo ""
for mode_spec in "${MODES[@]}"; do
    IFS='|' read -r mode_label headless_flag extra_args <<< "$mode_spec"
    echo "--- $mode_label (HEADLESS=$headless_flag) ---"
    grep -A5 "=== Run.*($mode_label)" "$RAW_FILE" | grep -E "DURATION_S|EXIT_CODE|PASSED=|FAILED=" || true
    echo ""
done
echo ""
echo "Full summary: $SUMMARY_FILE"
echo "Raw log: $RAW_FILE"

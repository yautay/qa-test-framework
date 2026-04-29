#!/bin/bash
# =============================================================================
# Benchmark E2E: headless only, seq vs xdist -n 2/3/4/5/6
# Uruchomienie: bash tools/benchmark/run_benchmark.sh [--compare-selenium]
# Wyniki:
# - bench_raw_playwright_<timestamp>.txt
# - bench_summary_<timestamp>.md
# - (opcjonalnie) bench_raw_selenium_<timestamp>.txt
# =============================================================================

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

TEST_FILE="qa/e2e/netcorner/nuxt/pl/tests/tests_orders/test_basic_orders.py"
SELENIUM_TEST_TARGET="TestCases/NetCornerProducts/pl_komputronik_nuxt/Test/SmokeTestsNUXT/"
SELENIUM_REPO="$(cd "$REPO_ROOT/.." && pwd)/nc-functional-tests-py"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
RAW_FILE_PLAYWRIGHT="bench_raw_playwright_${TIMESTAMP}.txt"
RAW_FILE_SELENIUM="bench_raw_selenium_${TIMESTAMP}.txt"
ERROR_FILE_PLAYWRIGHT="bench_errors_playwright_${TIMESTAMP}.txt"
ERROR_FILE_SELENIUM="bench_errors_selenium_${TIMESTAMP}.txt"
SUMMARY_FILE="bench_summary_${TIMESTAMP}.md"
RUNS_PER_MODE=2
PYTEST_RERUNS=1
COMPARE_SELENIUM=0
BENCH_TMP_DIR="$REPO_ROOT/tools/benchmark/.bench_tmp_${TIMESTAMP}"
MANIFEST_FILE="$BENCH_TMP_DIR/junit_manifest.txt"

# --- konfiguracja trybów ---------------------------------------------------
# Format: "label|extra_pytest_args"
ALL_MODES=(
    "headless-seq|"
    "headless-xdist-n2|-n 2"
    "headless-xdist-n3|-n 3"
    "headless-xdist-n4|-n 4"
    "headless-xdist-n5|-n 5"
    "headless-xdist-n6|-n 6"
)

MODES=("${ALL_MODES[@]}")

# --- env vars wspólne -------------------------------------------------------
export HEADLESS=1
export REPORTING_ENABLED=0
export ALLURE_ENABLED=0
export PYTEST_HTML_ENABLED=0
export RECORD_VIDEO=0

# --- tablice na wyniki (bash 4+ assoc arrays) -------------------------------
declare -A DURATIONS   # key: "framework|mode_label|run_num"  value: duration_s
declare -A PASSED      # key: "framework|mode_label|run_num"  value: passed_count
declare -A FAILED      # key: "framework|mode_label|run_num"  value: failed_count
declare -A EXITCODES   # key: "framework|mode_label|run_num"  value: exit_code
declare -A FAILURES    # key: "framework|mode_label|run_num"  value: failed test names

# --- funkcje ----------------------------------------------------------------

log() {
    local raw_file=$1
    shift
    echo "$@" | tee -a "$raw_file"
}

run_test() {
    local framework=$1
    local repo_root=$2
    local python_bin=$3
    local test_target=$4
    local raw_file=$5
    local run_num=$6
    local mode_label=$7
    local extra_args=$8
    local error_file=$9
    local junit_file="$BENCH_TMP_DIR/junit_${framework}_${mode_label}_run${run_num}.xml"

    log "$raw_file" ""
    log "$raw_file" "=== Run $run_num ($mode_label) FRAMEWORK=$framework HEADLESS=$HEADLESS ==="
    log "$raw_file" "START_TIME=$(date '+%Y-%m-%d %H:%M:%S')"

    local start_ts
    start_ts=$(date +%s%N)

    local output
    local run_output_file="$BENCH_TMP_DIR/output_${framework}_${mode_label}_run${run_num}.log"
    : > "$run_output_file"

    (
        while true; do
            sleep 30
            now_ts=""
            elapsed_s=""
            now_ts=$(date +%s)
            elapsed_s=$(( now_ts - (start_ts / 1000000000) ))
            log "$raw_file" "[heartbeat] FRAMEWORK=$framework MODE=$mode_label RUN=$run_num still running... elapsed=${elapsed_s}s"
        done
    ) &
    local heartbeat_pid=$!

    set +e
    (
        cd "$repo_root" && "$python_bin" -m pytest "$test_target" -v --tb=line --reruns "$PYTEST_RERUNS" --junitxml "$junit_file" $extra_args
    ) 2>&1 | tee "$run_output_file" | tee -a "$raw_file"
    local exit_code=${PIPESTATUS[0]}
    set -e

    kill "$heartbeat_pid" 2>/dev/null || true
    wait "$heartbeat_pid" 2>/dev/null || true

    output=$(<"$run_output_file")

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

    log "$raw_file" "EXIT_CODE=$exit_code"
    log "$raw_file" "DURATION_MS=$duration_ms"
    log "$raw_file" "DURATION_S=${duration_s}s"
    log "$raw_file" "PYTEST_TIME=${pytest_time}s"
    log "$raw_file" "PASSED=$passed_count"
    log "$raw_file" "FAILED=$failed_count"
    log "$raw_file" "FAILED_TESTS=$failed_tests"
    log "$raw_file" "END_TIME=$(date '+%Y-%m-%d %H:%M:%S')"
    log "$raw_file" "JUNIT_XML=$junit_file"
    log "$raw_file" "---END_RUN---"

    # Store in arrays
    local key="${framework}|${mode_label}|${run_num}"
    DURATIONS["$key"]="$duration_s"
    PASSED["$key"]="$passed_count"
    FAILED["$key"]="$failed_count"
    EXITCODES["$key"]="$exit_code"
    FAILURES["$key"]="$failed_tests"

    if [[ "$exit_code" -ne 0 || "$failed_count" -gt 0 ]]; then
        {
            echo "============================================================"
            echo "FRAMEWORK=$framework MODE=$mode_label RUN=$run_num"
            echo "START_TIME=$(date '+%Y-%m-%d %H:%M:%S')"
            echo "EXIT_CODE=$exit_code"
            echo "FAILED=$failed_count"
            echo "FAILED_TESTS=$failed_tests"
            echo "--- PYTEST OUTPUT (FAILURE DUMP) ---"
            echo "$output"
            echo "============================================================"
            echo ""
        } >> "$error_file"
    fi

    echo "${framework}|${mode_label}|${run_num}|${junit_file}" >> "$MANIFEST_FILE"
}

generate_framework_summary() {
    local framework=$1
    local test_target=$2
    local f="$SUMMARY_FILE"

    if [[ "$framework" == "playwright" ]]; then
        echo "# Benchmark E2E - Zestawienie wyników" > "$f"
        echo "" >> "$f"
        echo "**Data:** $(date '+%Y-%m-%d %H:%M:%S')" >> "$f"
        echo "**Runów per tryb:** $RUNS_PER_MODE" >> "$f"
        echo "**Platform:** $(uname -srm)" >> "$f"
        echo "**Playwright/Python:** $(.venv/bin/python --version 2>&1)" >> "$f"
        if [[ "$COMPARE_SELENIUM" -eq 1 ]]; then
            echo "**Selenium/Python:** $($SELENIUM_REPO/.venv/bin/python --version 2>&1)" >> "$f"
            echo "**Tryb porównawczy:** seq/n2/n3/n4/n5/n6" >> "$f"
        fi
        echo "" >> "$f"
    fi

    echo "## Framework: $framework" >> "$f"
    echo "" >> "$f"
    echo "**Target testów:** \`$test_target\`" >> "$f"
    echo "**Runów per tryb:** $RUNS_PER_MODE" >> "$f"
    echo "" >> "$f"

    # ---- Tabela podsumowująca ----
    echo "### Podsumowanie" >> "$f"
    echo "" >> "$f"
    echo "| Tryb | Run 1 (s) | Run 2 (s) | Avg (s) | Min (s) | Max (s) | Avg Passed | Avg Failed | Pass Rate |" >> "$f"
    echo "|------|-----------|-----------|---------|---------|---------|------------|------------|-----------|" >> "$f"

    for mode_spec in "${MODES[@]}"; do
        IFS='|' read -r mode_label extra_args <<< "$mode_spec"

        local sum_dur=0 min_dur=999999 max_dur=0
        local sum_passed=0 sum_failed=0
        local dur1="" dur2=""

        for i in $(seq 1 $RUNS_PER_MODE); do
            local key="${framework}|${mode_label}|${i}"
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

    # ---- Tabele szczegółowe per tryb ----
    echo "### Szczegóły per tryb" >> "$f"
    echo "" >> "$f"

    for mode_spec in "${MODES[@]}"; do
        IFS='|' read -r mode_label extra_args <<< "$mode_spec"
        echo "### $mode_label" >> "$f"
        echo "" >> "$f"
        echo "| Run | Czas (s) | Passed | Failed | Exit Code | Failures |" >> "$f"
        echo "|-----|----------|--------|--------|-----------|----------|" >> "$f"

        for i in $(seq 1 $RUNS_PER_MODE); do
            local key="${framework}|${mode_label}|${i}"
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

    # ---- Speedup xdist vs sekwencyjny ----
    echo "### Speedup: xdist vs sekwencyjne" >> "$f"
    echo "" >> "$f"
    echo "| Porównanie | Avg Seq (s) | Avg xdist (s) | Speedup |" >> "$f"
    echo "|------------|-------------|---------------|---------|" >> "$f"

    # Headless baseline
    local headless_seq_avg=0
    local headless_seq_sum=0
    for i in $(seq 1 $RUNS_PER_MODE); do
        local d="${DURATIONS[${framework}|headless-seq|$i]:-0}"
        headless_seq_sum=$(echo "$headless_seq_sum + $d" | bc)
    done
    headless_seq_avg=$(echo "scale=2; $headless_seq_sum / $RUNS_PER_MODE" | bc)

    if [[ "$headless_seq_avg" == "0" || "$headless_seq_avg" == ".00" ]]; then
        echo "Brak trybu headless-seq w bieżącej konfiguracji --modes." >> "$f"
    else
        for mode_spec in "${MODES[@]}"; do
            IFS='|' read -r mode_label extra_args <<< "$mode_spec"
            if [[ "$mode_label" =~ ^headless-xdist-n[0-9]+$ ]]; then
                local xdist_sum=0
                for i in $(seq 1 $RUNS_PER_MODE); do
                    local d="${DURATIONS[${framework}|${mode_label}|$i]:-0}"
                    xdist_sum=$(echo "$xdist_sum + $d" | bc)
                done
                local xdist_avg
                xdist_avg=$(echo "scale=2; $xdist_sum / $RUNS_PER_MODE" | bc)
                local speedup="N/A"
                if [[ "$xdist_avg" != "0" && "$xdist_avg" != ".00" ]]; then
                    speedup=$(echo "scale=2; $headless_seq_avg / $xdist_avg" | bc)
                fi
                echo "| headless-seq vs ${mode_label} | $headless_seq_avg | $xdist_avg | ${speedup}x |" >> "$f"
            fi
        done
    fi

    echo "" >> "$f"

    # ---- Flakey analysis ----
    echo "### Flakey testy (padające w >0 runach)" >> "$f"
    echo "" >> "$f"

    declare -A FLAKEY_COUNT
    for mode_spec in "${MODES[@]}"; do
        IFS='|' read -r mode_label extra_args <<< "$mode_spec"
        for i in $(seq 1 $RUNS_PER_MODE); do
            local key="${framework}|${mode_label}|${i}"
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
}

generate_comparison_section() {
    local f="$SUMMARY_FILE"
    if [[ "$COMPARE_SELENIUM" -ne 1 ]]; then
        return
    fi

    python3 - "$MANIFEST_FILE" "$f" <<'PY'
import statistics
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict

manifest_path = sys.argv[1]
summary_path = sys.argv[2]

data = defaultdict(list)

with open(manifest_path, "r", encoding="utf-8") as mf:
    for line in mf:
        line = line.strip()
        if not line:
            continue
        framework, mode, run_num, junit = line.split("|", 3)
        try:
            root = ET.parse(junit).getroot()
        except Exception:
            continue
        for tc in root.iter("testcase"):
            classname = tc.attrib.get("classname", "")
            name = tc.attrib.get("name", "")
            test_id = f"{classname}::{name}".strip(":")
            t = float(tc.attrib.get("time", 0.0))
            data[(framework, mode, test_id)].append(t)

modes = [
    "headless-seq",
    "headless-xdist-n2",
    "headless-xdist-n3",
    "headless-xdist-n4",
    "headless-xdist-n5",
    "headless-xdist-n6",
]

all_test_ids = sorted({k[2] for k in data.keys()})

with open(summary_path, "a", encoding="utf-8") as out:
    out.write("\n## Porównanie Playwright vs Selenium\n\n")
    out.write("### Czas per test per tryb\n\n")
    out.write("| Test ID | Tryb | Playwright Avg (s) | Selenium Avg (s) | Delta (SEL-PW) | Ratio (SEL/PW) |\n")
    out.write("|---------|------|--------------------|------------------|----------------|----------------|\n")

    rows = 0
    for test_id in all_test_ids:
        for mode in modes:
            pw = data.get(("playwright", mode, test_id), [])
            se = data.get(("selenium", mode, test_id), [])
            if not pw and not se:
                continue
            pw_avg = statistics.mean(pw) if pw else None
            se_avg = statistics.mean(se) if se else None
            if pw_avg is None:
                delta = "N/A"
                ratio = "N/A"
            elif se_avg is None:
                delta = "N/A"
                ratio = "N/A"
            else:
                delta = f"{(se_avg - pw_avg):.2f}"
                ratio = f"{(se_avg / pw_avg):.2f}x" if pw_avg != 0 else "N/A"

            out.write(
                f"| `{test_id}` | {mode} | {pw_avg:.2f} "
                f"| {se_avg:.2f} | {delta} | {ratio} |\n"
                if (pw_avg is not None and se_avg is not None)
                else f"| `{test_id}` | {mode} | {pw_avg:.2f} "
                     f"| N/A | N/A | N/A |\n" if pw_avg is not None
                else f"| `{test_id}` | {mode} | N/A | {se_avg:.2f} | N/A | N/A |\n"
            )
            rows += 1

    if rows == 0:
        out.write("Brak danych per-test do porównania.\n")

    out.write("\n### Testy tylko w jednym frameworku\n\n")
    pw_tests = {k[2] for k in data.keys() if k[0] == "playwright"}
    se_tests = {k[2] for k in data.keys() if k[0] == "selenium"}
    only_pw = sorted(pw_tests - se_tests)
    only_se = sorted(se_tests - pw_tests)

    out.write("- Tylko Playwright:\n")
    if only_pw:
        for t in only_pw:
            out.write(f"  - `{t}`\n")
    else:
        out.write("  - brak\n")

    out.write("- Tylko Selenium:\n")
    if only_se:
        for t in only_se:
            out.write(f"  - `{t}`\n")
    else:
        out.write("  - brak\n")
PY

    echo ""
    echo "Summary written to: $f"
}

usage() {
    cat <<EOF
Usage: bash tools/benchmark/run_benchmark.sh [options]

Options:
  --compare-selenium              Włącz porównanie z Selenium.
  --selenium-repo <path>          Ścieżka do repo nc-functional-tests-py.
  --selenium-target <path>        Ścieżka testów Selenium względem repo.
  --runs <N>                      Liczba runów na tryb (domyślnie: 2).
  --modes <lista>                 Lista trybów po przecinku, np. headless-seq,headless-xdist-n2.
  --reruns <N>                    Liczba rerunów na fail (pytest --reruns), domyślnie: 1.
  --help                          Pokaż pomoc.
EOF
}

set_modes() {
    local input="$1"
    local requested=()
    local selected=()
    local found=0

    IFS=',' read -r -a requested <<< "$input"
    MODES=()

    for req in "${requested[@]}"; do
        req="$(echo "$req" | xargs)"
        [[ -z "$req" ]] && continue
        found=0
        for mode_spec in "${ALL_MODES[@]}"; do
            IFS='|' read -r mode_label extra_args <<< "$mode_spec"
            if [[ "$mode_label" == "$req" ]]; then
                selected+=("$mode_spec")
                found=1
                break
            fi
        done
        if [[ "$found" -eq 0 ]]; then
            echo "Nieznany tryb: $req"
            echo "Dozwolone tryby:"
            for mode_spec in "${ALL_MODES[@]}"; do
                IFS='|' read -r mode_label extra_args <<< "$mode_spec"
                echo "  - $mode_label"
            done
            exit 1
        fi
    done

    if [[ ${#selected[@]} -eq 0 ]]; then
        echo "Pusta lista trybów w --modes"
        exit 1
    fi

    MODES=("${selected[@]}")
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --compare-selenium)
                COMPARE_SELENIUM=1
                shift
                ;;
            --selenium-repo)
                SELENIUM_REPO="$2"
                shift 2
                ;;
            --selenium-target)
                SELENIUM_TEST_TARGET="$2"
                shift 2
                ;;
            --runs)
                RUNS_PER_MODE="$2"
                shift 2
                ;;
            --modes)
                set_modes "$2"
                shift 2
                ;;
            --reruns)
                PYTEST_RERUNS="$2"
                shift 2
                ;;
            --help)
                usage
                exit 0
                ;;
            *)
                echo "Unknown argument: $1"
                usage
                exit 1
                ;;
        esac
    done
}

# --- main -------------------------------------------------------------------

parse_args "$@"

mkdir -p "$BENCH_TMP_DIR"
touch "$MANIFEST_FILE"
touch "$ERROR_FILE_PLAYWRIGHT"
if [[ "$COMPARE_SELENIUM" -eq 1 ]]; then
    touch "$ERROR_FILE_SELENIUM"
fi

log "$RAW_FILE_PLAYWRIGHT" "============================================================"
log "$RAW_FILE_PLAYWRIGHT" "BENCHMARK E2E - Headless only"
log "$RAW_FILE_PLAYWRIGHT" "Framework: playwright"
log "$RAW_FILE_PLAYWRIGHT" "Plik: $TEST_FILE"
log "$RAW_FILE_PLAYWRIGHT" "Tryby: ${MODES[*]}"
log "$RAW_FILE_PLAYWRIGHT" "Runów per tryb: $RUNS_PER_MODE"
log "$RAW_FILE_PLAYWRIGHT" "Reruns na fail: $PYTEST_RERUNS"
log "$RAW_FILE_PLAYWRIGHT" "Start: $(date '+%Y-%m-%d %H:%M:%S')"
log "$RAW_FILE_PLAYWRIGHT" "Env: REPORTING_ENABLED=$REPORTING_ENABLED"
log "$RAW_FILE_PLAYWRIGHT" "     ALLURE_ENABLED=$ALLURE_ENABLED PYTEST_HTML_ENABLED=$PYTEST_HTML_ENABLED"
log "$RAW_FILE_PLAYWRIGHT" "     RECORD_VIDEO=$RECORD_VIDEO"
log "$RAW_FILE_PLAYWRIGHT" "Platform: $(uname -srm)"
log "$RAW_FILE_PLAYWRIGHT" "Python: $(.venv/bin/python --version 2>&1)"
log "$RAW_FILE_PLAYWRIGHT" "Pytest: $(.venv/bin/python -m pytest --version 2>&1 | head -1)"
log "$RAW_FILE_PLAYWRIGHT" "Error dump file: $ERROR_FILE_PLAYWRIGHT"
log "$RAW_FILE_PLAYWRIGHT" "============================================================"
log "$RAW_FILE_PLAYWRIGHT" ""

for mode_spec in "${MODES[@]}"; do
    IFS='|' read -r mode_label extra_args <<< "$mode_spec"
    log "$RAW_FILE_PLAYWRIGHT" "########################################"
    log "$RAW_FILE_PLAYWRIGHT" "# PHASE: $mode_label (HEADLESS=$HEADLESS)"
    log "$RAW_FILE_PLAYWRIGHT" "########################################"
    for i in $(seq 1 $RUNS_PER_MODE); do
        run_test "playwright" "$REPO_ROOT" ".venv/bin/python" "$TEST_FILE" "$RAW_FILE_PLAYWRIGHT" "$i" "$mode_label" "$extra_args" "$ERROR_FILE_PLAYWRIGHT"
    done
done

log "$RAW_FILE_PLAYWRIGHT" ""
log "$RAW_FILE_PLAYWRIGHT" "============================================================"
log "$RAW_FILE_PLAYWRIGHT" "BENCHMARK COMPLETED: $(date '+%Y-%m-%d %H:%M:%S')"
log "$RAW_FILE_PLAYWRIGHT" "Raw results file: $RAW_FILE_PLAYWRIGHT"
log "$RAW_FILE_PLAYWRIGHT" "============================================================"

if [[ "$COMPARE_SELENIUM" -eq 1 ]]; then
    log "$RAW_FILE_SELENIUM" "============================================================"
    log "$RAW_FILE_SELENIUM" "BENCHMARK E2E - Headless only"
    log "$RAW_FILE_SELENIUM" "Framework: selenium"
    log "$RAW_FILE_SELENIUM" "Plik: $SELENIUM_TEST_TARGET"
    log "$RAW_FILE_SELENIUM" "Repo: $SELENIUM_REPO"
    log "$RAW_FILE_SELENIUM" "Tryby: ${MODES[*]}"
    log "$RAW_FILE_SELENIUM" "Runów per tryb: $RUNS_PER_MODE"
    log "$RAW_FILE_SELENIUM" "Reruns na fail: $PYTEST_RERUNS"
    log "$RAW_FILE_SELENIUM" "Start: $(date '+%Y-%m-%d %H:%M:%S')"
    log "$RAW_FILE_SELENIUM" "Python: $($SELENIUM_REPO/.venv/bin/python --version 2>&1)"
    log "$RAW_FILE_SELENIUM" "Pytest: $($SELENIUM_REPO/.venv/bin/python -m pytest --version 2>&1 | head -1)"
    log "$RAW_FILE_SELENIUM" "Error dump file: $ERROR_FILE_SELENIUM"
    log "$RAW_FILE_SELENIUM" "============================================================"
    log "$RAW_FILE_SELENIUM" ""

    for mode_spec in "${MODES[@]}"; do
        IFS='|' read -r mode_label extra_args <<< "$mode_spec"
        log "$RAW_FILE_SELENIUM" "########################################"
        log "$RAW_FILE_SELENIUM" "# PHASE: $mode_label (HEADLESS=$HEADLESS)"
        log "$RAW_FILE_SELENIUM" "########################################"
        for i in $(seq 1 $RUNS_PER_MODE); do
            run_test "selenium" "$SELENIUM_REPO" ".venv/bin/python" "$SELENIUM_TEST_TARGET" "$RAW_FILE_SELENIUM" "$i" "$mode_label" "$extra_args" "$ERROR_FILE_SELENIUM"
        done
    done

    log "$RAW_FILE_SELENIUM" ""
    log "$RAW_FILE_SELENIUM" "============================================================"
    log "$RAW_FILE_SELENIUM" "BENCHMARK COMPLETED: $(date '+%Y-%m-%d %H:%M:%S')"
    log "$RAW_FILE_SELENIUM" "Raw results file: $RAW_FILE_SELENIUM"
    log "$RAW_FILE_SELENIUM" "============================================================"
fi

# --- generuj podsumowanie markdown -----------------------------------------
generate_framework_summary "playwright" "$TEST_FILE"
if [[ "$COMPARE_SELENIUM" -eq 1 ]]; then
    generate_framework_summary "selenium" "$SELENIUM_TEST_TARGET"
fi
generate_comparison_section

echo "" >> "$SUMMARY_FILE"
echo "---" >> "$SUMMARY_FILE"
echo "*Wygenerowano automatycznie przez \`tools/benchmark/run_benchmark.sh\`*" >> "$SUMMARY_FILE"

# --- szybki podgląd w terminalu ---------------------------------------------
echo ""
echo "=== QUICK SUMMARY ==="
echo ""
for mode_spec in "${MODES[@]}"; do
    IFS='|' read -r mode_label extra_args <<< "$mode_spec"
    echo "--- PLAYWRIGHT: $mode_label (HEADLESS=$HEADLESS) ---"
    grep -A8 "=== Run.*($mode_label).*FRAMEWORK=playwright" "$RAW_FILE_PLAYWRIGHT" | grep -E "DURATION_S|EXIT_CODE|PASSED=|FAILED=" || true
    if [[ "$COMPARE_SELENIUM" -eq 1 ]]; then
        echo "--- SELENIUM: $mode_label (HEADLESS=$HEADLESS) ---"
        grep -A8 "=== Run.*($mode_label).*FRAMEWORK=selenium" "$RAW_FILE_SELENIUM" | grep -E "DURATION_S|EXIT_CODE|PASSED=|FAILED=" || true
    fi
    echo ""
done
echo ""
echo "Full summary: $SUMMARY_FILE"
echo "Raw log (playwright): $RAW_FILE_PLAYWRIGHT"
echo "Error dump (playwright): $ERROR_FILE_PLAYWRIGHT"
if [[ "$COMPARE_SELENIUM" -eq 1 ]]; then
    echo "Raw log (selenium): $RAW_FILE_SELENIUM"
    echo "Error dump (selenium): $ERROR_FILE_SELENIUM"
fi

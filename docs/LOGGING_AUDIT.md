# Audyt logowania (caly repo)

Aktualizacja: 2026-03-06

## 1) Jak dziala logowanie

Punkt centralny: `framework/logger.py`.

- Loguru jest glownym loggerem aplikacyjnym.
- Stdlib `logging` i `warnings` sa mostkowane do Loguru (`_InterceptHandler`, `logging.captureWarnings(True)`).
- Rekordy sa redagowane przed zapisem (`_redact_record`) - maskowanie tokenow/hasel w `message` i `extra`.
- Kontekst runa (`run_id`, `worker_id`, `browser`, `tester`, `run_note`, `nodeid`) jest dopinany przez `logger.configure(extra=...)`.

## 2) Sinki, poziomy i destination

W projekcie sa 4 typy sinkow. Typowo aktywne sa 2-3 naraz (zalezne od trybu i konfiguracji reportingu).

| Sink | Aktywny kiedy | Poziom | Format | Destination |
|---|---|---|---|---|
| `sys.stdout` (test runtime) | `configure_logging(...)` | `CONSOLE_LOG_LEVEL` / `settings.console_log_level` (domyslnie `WARNING`) | human-readable | konsola lokalna/CI |
| `artifacts/<run_id>/logs/run_<run_id>_<worker>.log` | `configure_logging(...)` | stale `DEBUG` | JSON (`serialize=True`) | artefakty runa |
| `tools/logs/<script>.log` (`settings.tools_logs_dir`) | `configure_tools_logging(...)` | `TOOLS_FILE_LOG_LEVEL` / `settings.tools_file_log_level` (domyslnie `DEBUG`) | tekst | logi narzedzi `tools/*` |
| Reporting API sink (`add_reporting_api_sink`) | gdy `reporting_enabled=True` i endpoint logow skonfigurowany | `REPORTING_API_LOG_LEVEL` / `settings.reporting_api_log_level` (domyslnie `WARNING`) | payload JSON `event_type=log` | `REPORTING_API_LOG_ENDPOINT` (domyslnie `/test-run/log`) |

Uwagi:
- Wysylka do Reporting API jest zabezpieczona przed petla (`_skip_remote_log=True` w logach transportu HTTP).
- Dla testow `bind_test_context(nodeid)` dopina `nodeid` do `extra` (widoczne w konsoli, pliku JSON i sinku API).

## 3) Rozklad poziomow logowania w repo

Zliczenie wywolan `logger.*` w kodzie Python:

- `debug`: 37
- `info`: 23
- `warning`: 43
- `error`: 8
- `critical`: 2
- `exception`: 1
- `trace/success`: 0

## 4) Co, kiedy, gdzie logujemy (zestawienie pelne)

Legenda destination:
- `STDOUT` = sink konsolowy,
- `RUN_JSON` = `artifacts/.../run_<run_id>_<worker>.log`,
- `TOOLS_FILE` = `tools/logs/<script>.log`,
- `REPORTING_API_LOG` = `POST {REPORTING_API_LOG_ENDPOINT}` (po filtrze poziomu).

### A) Runtime pytest i lifecycle runa

| Plik | Co logujemy | Kiedy | Poziomy | Destination |
|---|---|---|---|---|
| `qa/conftest.py` | `runtime_target_resolved`, `runtime_reference_resolved` | podczas rozwiazywania targetu/ref przed runem | `INFO` | `STDOUT`, `RUN_JSON`, opcj. `REPORTING_API_LOG` |
| `qa/conftest.py` | `reporting_run_start`, `reporting_run_finish` | start/koniec sesji pytest | `INFO` | j.w. |
| `qa/conftest.py` | `test_case_slow_regression` | wykryta regresja czasu testu | `WARNING` | j.w. |
| `qa/e2e/conftest.py` | `allure_attach_skipped`, `context_timing`, `raw_screenshot_capture_failed`, `screenshot_highlight_failed` | attach/screenshot/context timing | `DEBUG/INFO/WARNING` | `STDOUT`, `RUN_JSON`, opcj. `REPORTING_API_LOG` |
| `qa/visual/conftest.py` | `perceptual_postprocess_failed` (`logger.exception`) | wyjatek przy postprocessingu perceptual | `EXCEPTION` | `STDOUT`, `RUN_JSON`, opcj. `REPORTING_API_LOG` |
| `framework/plugins/xdist_report_finalize.py` | `visual_worker_results_missing`, `visual_report_finalize_failed`, `perceptual_postprocess_failed` | finalizacja raportu xdist | `WARNING` | `STDOUT`, `RUN_JSON`, opcj. `REPORTING_API_LOG` |

### B) Reporting API i report server

| Plik | Co logujemy | Kiedy | Poziomy | Destination |
|---|---|---|---|---|
| `framework/reporting_client.py` | `reporting_api_post_attempt`, `reporting_api_post_files_attempt` | proba POST (JSON / multipart) | `DEBUG` | runtime sinki; oznaczone `_skip_remote_log` |
| `framework/reporting_client.py` | `reporting_api_call_success` | odpowiedz `2xx` | `INFO` | runtime sinki; oznaczone `_skip_remote_log` |
| `framework/reporting_client.py` | `reporting_api_non_2xx`, `reporting_api_request_exception`, `reporting_api_files_upload_exception` | bledy przejsciowe/retry | `WARNING` | runtime sinki; oznaczone `_skip_remote_log` |
| `framework/reporting_client.py` | `reporting_api_call_failed` | blad koncowy dla requestu | `ERROR` | runtime sinki; oznaczone `_skip_remote_log` |
| `framework/reporting_client.py` | `reporting_api_call_final_failure` | wyczerpane wszystkie retry | `CRITICAL` | runtime sinki; oznaczone `_skip_remote_log` |
| `framework/reporting/report_server/cli.py` | `tools_log_file`, `reporting_config_missing_url` | startup report-server / bledna konfiguracja | `DEBUG/ERROR` | `STDOUT`, `TOOLS_FILE`, opcj. `REPORTING_API_LOG` |
| `framework/reporting/report_server/routes/handler.py` | `reporting_client_disconnected_before_response`, `reporting_api_disabled_skipping_sync`, `reporting_sync_executor_unavailable`, `report server GET failed`, `report server POST failed` | obsluga HTTP i sync | `DEBUG/WARNING` | `STDOUT`, `TOOLS_FILE`, opcj. `REPORTING_API_LOG` |
| `framework/reporting/report_server/services/sync.py` | `reporting_sync_skipped_reporting_disabled`, `reporting_outbox_worker_failed` | sync outbox eventow | `DEBUG/WARNING` | `STDOUT`, `TOOLS_FILE`, opcj. `REPORTING_API_LOG` |
| `framework/reporting/report_server/services/pdf.py` | `bug_pdf_generated` + warningi dot. obrazow/ReportLab/config | generacja PDF BUG | `INFO/WARNING` | `STDOUT`, `TOOLS_FILE`, opcj. `REPORTING_API_LOG` |

### C) Visual pipeline, PMS, baseline storage, video

| Plik | Co logujemy | Kiedy | Poziomy | Destination |
|---|---|---|---|---|
| `framework/visual/perceptual/postprocess.py` | `perceptual_postprocess_started/finished/skipped`, `perceptual_postprocess_coverage` | lifecycle postprocessingu | `INFO` | `STDOUT`, `RUN_JSON`, opcj. `REPORTING_API_LOG` |
| `framework/visual/perceptual/postprocess.py` | `perceptual_pair_queued`, `perceptual_server_queue_snapshot`, `perceptual_job_waiting`, `perceptual_job_error_details_requested/loaded` | kroki techniczne kolejkowania/pollingu | `DEBUG` | `RUN_JSON` (i `STDOUT` przy nizszym progu), opcj. `REPORTING_API_LOG` |
| `framework/visual/perceptual/postprocess.py` | `perceptual_incremental_results_flush_failed`, `perceptual_server_queue_snapshot_failed`, `perceptual_job_poll_failed`, `perceptual_job_error_details_failed`, `perceptual_postprocess_unavailable` | degradacja/fallback/retry | `WARNING` | `STDOUT`, `RUN_JSON`, opcj. `REPORTING_API_LOG` |
| `framework/visual/perceptual/postprocess.py` | `perceptual_job_submit_failed`, `perceptual_job_timeout`, `perceptual_job_failed` | blad operacji joba | `ERROR` | `STDOUT`, `RUN_JSON`, opcj. `REPORTING_API_LOG` |
| `framework/reporting/clients/pms/pms_client.py` | `pms_healthcheck`, `pms_submit_duplicate`, `pms_heatmap_unavailable`, `pms_healthcheck_failed`, `pms_retry` | klient PMS (submit/poll/retry/health) | `DEBUG/INFO/WARNING` | runtime sinki |
| `framework/visual/baseline_store.py` | warningi MinIO: brak biblioteki, brak obiektu, download/upload fail | operacje baseline MinIO | `WARNING` | runtime sinki |
| `framework/video_utils.py` | warningi fallback ffmpeg/video trim | postprocess video failow | `WARNING` | runtime sinki |
| `qa/visual/netcorner/nuxt/pl/visual_suite.py` | `visual_dual_pass_*`, `runtime_reference_resolved`, `visual_reference_pass_*`, `visual_target_pass_*`, `visual_reference_resolve_failed` | przebieg dual-pass visual | `INFO/ERROR` | `STDOUT`, `RUN_JSON`, opcj. `REPORTING_API_LOG` |

### D) Narzedzia `tools/*`

| Plik | Co logujemy | Kiedy | Poziomy | Destination |
|---|---|---|---|---|
| `tools/artifacts/cleanup.py` | `tools_log_file` | startup skryptu | `DEBUG` | `STDOUT`, `TOOLS_FILE` |
| `tools/visual/debug.py` | `tools_log_file` | startup skryptu | `DEBUG` | `STDOUT`, `TOOLS_FILE` |
| `tools/visual/generate_tree.py` | `tools_log_file` | startup skryptu | `DEBUG` | `STDOUT`, `TOOLS_FILE` |
| `tools/visual/promote_candidates_local.py` | `tools_log_file` | startup skryptu | `DEBUG` | `STDOUT`, `TOOLS_FILE` |
| `tools/visual/retention_baselines.py` | `tools_log_file` | startup skryptu | `DEBUG` | `STDOUT`, `TOOLS_FILE` |
| `tools/visual/version_baselines.py` | `tools_log_file` | startup skryptu | `DEBUG` | `STDOUT`, `TOOLS_FILE` |
| `tools/visual/baseline_ops/executor.py` | `baseline_copy_*`, `baseline_remove_*` | plan/execution copy-remove lokalnie | `DEBUG/WARNING` | `STDOUT`, `TOOLS_FILE` |
| `tools/visual/baseline_ops/lifecycle_ops.py` | `baseline_minio_remove_*`, `baseline_sync_*` | sync/prune lokal+MinIO | `DEBUG/WARNING` | `STDOUT`, `TOOLS_FILE` |
| `tools/visual/baseline_ops/version_copy.py` | `baseline_minio_copy_*`, `baseline_minio_upload_*`, `baseline_minio_remove_*` | kopiowanie wersji baseline w MinIO | `DEBUG/WARNING` | `STDOUT`, `TOOLS_FILE` |

## 5) Szybkie wnioski operacyjne

- Domyslny `console_log_level=WARNING` ogranicza szum, ale ukrywa wiekszosc flow `INFO` (np. start/finish etapow).
- Najwiekszy wolumen eventow jest w warningach i debugach (transport API, perceptual polling, operacje tools).
- `REPORTING_API_LOG_LEVEL` kontroluje ile logow trafia na endpoint `/test-run/log`.
- Logi transportowe `reporting_client.py` sa celowo oznaczane `_skip_remote_log`, wiec nie robia petli zwrotnej przez sink API.

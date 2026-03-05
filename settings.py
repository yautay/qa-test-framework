# console_log_level:
# - Poziom logowania Loguru dla konsoli.
# - Dozwolone: TRACE, DEBUG, INFO, SUCCESS, WARNING, ERROR, CRITICAL
# - Przyklad: "DEBUG" da wiecej szczegolow podczas diagnozy.
# Skutek: nizszy poziom (np. TRACE) = wiecej logow i latwiejszy debug, ale wiekszy szum.
console_log_level = "WARNING"

# ignore_https_errors:
# - True: ignoruje bledy certyfikatow TLS/HTTPS (np. self-signed lokalnie).
# - False: wymaga poprawnego certyfikatu.
# - Przyklad: True w dev, False w prod.
# Skutek: True zwieksza kompatybilnosc, ale obniza bezpieczenstwo polaczenia.
ignore_https_errors = True

# General runtime defaults (CI moze nadpisac przez env).

# artifacts_dir:
# - Katalog na raporty, screenshoty, filmy i artefakty testow.
# - Przyklad: "artifacts" albo "out/test-artifacts".
# Skutek: zmiana porzadkuje output i moze ulatwic archiwizacje w CI.
artifacts_dir = "artifacts"

# allure_enabled:
# - True: wlacza automatyczne generowanie raportu Allure (allure-results).
# - False: nie ustawia katalogu Allure i pomija attach'e Allure.
# Skutek: False przyspiesza lokalny run i ogranicza artefakty, True daje bogatsze raportowanie.
allure_enabled = False

# pytest_html_enabled:
# - True: wlacza automatyczne generowanie raportu pytest-html.
# - False: nie ustawia htmlpath, wiec raport HTML nie jest tworzony automatycznie.
# Skutek: True ulatwia szybki podglad wynikow po runie.
pytest_html_enabled = True

# record_video:
# - True: nagrywa wideo z przebiegu testow.
# - False: bez nagran.
# Skutek: True pomaga analizowac flaky/test fail, ale zwieksza czas i zajete miejsce.
record_video = True

# video_min_seconds:
# - Minimalna dlugosc klipu w sekundach.
# - Przyklad: 30 = krotsze testy dostana dopelnione nagranie.
# Skutek: wyzsza wartosc = wieksze pliki, ale latwiejsza analiza kontekstu przed/po bledzie.
video_min_seconds = 30

# highlight_on_fail:
# - True: podkresla elementy/obszary przy failu (jesli wspierane).
# - False: standardowy output bez podswietlen.
# Skutek: True ulatwia szybkie wskazanie miejsca problemu w raporcie.
highlight_on_fail = False

# min_expected_tests:
# - Minimalna liczba testow, ktora ma sie uruchomic.
# - Przyklad: 1 zabezpiecza przed "zielonym" runem bez testow.
# Skutek: zbyt niska wartosc moze przepuscic bledna konfiguracje selekcji testow.
min_expected_tests = 1

# Remote Playwright grid compatibility defaults.

# grid_ws_endpoint:
# - WebSocket endpoint do zdalnego grida Playwright.
# - Przyklad: "ws://127.0.0.1:9323/" lub "wss://grid.example.com/playwright".
# Skutek: bledny adres = brak sesji browsera.
grid_ws_endpoint = "ws://127.0.0.1:9323/"

# grid_connect_timeout_ms:
# - Timeout nawiazania polaczenia do grida (ms).
# - Przyklad: 30000 = 30 sekund.
# Skutek: nizsza wartosc szybciej failuje przy problemach sieciowych.
grid_connect_timeout_ms = 30000

# Visual regression defaults.

# visual_enabled:
# - True: wlacza porownania wizualne.
# - False: pomija caly modul visual regression.
# Skutek: False przyspiesza run, ale traci kontrole regresji UI.
visual_enabled = True

# visual_compare_mode:
# - "pixel": dokladne porownanie piksel-do-piksela.
# - "perceptual": metryki percepcyjne (bardziej odporne na drobny noise).
# - "hybrid": laczy oba podejscia.
# Skutek: tryb wpływa na czulosc, szybkosc i liczbe false positive.
visual_compare_mode = "hybrid"  # pixel|perceptual|hybrid

# visual_baseline_provider:
# - "local": baseline na dysku lokalnym.
# - "minio": baseline w obiekcie MinIO/S3-compatible.
# Skutek: wybor determinuje skad pobierane i gdzie zapisywane sa baseline'y.
visual_baseline_provider = "minio"  # minio|local

# visual_baseline_profile:
# - Nazwa profilu baseline (np. per branch/per env).
# - Przyklad: "test-ref", "main", "staging".
# Skutek: rozdziela zestawy baseline miedzy srodowiskami.
visual_baseline_profile = "test-ref"

# visual_baseline_version:
# - Wersja baseline, np. tag/build/hash.
# - Przyklad: "latest", "build-124", "commit-a1b2c3".
# Skutek: pozwala pinowac porownania do konkretnej wersji referencyjnej.
visual_baseline_version = "latest"

# visual_cache_dir:
# - Katalog cache dla danych visual.
# - Przyklad: ".visual_cache".
# Skutek: cache przyspiesza kolejne runy, ale trzeba go czyscic przy niezgodnosciach.
visual_cache_dir = ".visual_cache"

# visual_fail_on_missing_baseline:
# - True: brak baseline = FAIL testu.
# - False: brak baseline nie zatrzymuje runa (zalezne od logiki projektu).
# Skutek: True wymusza dyscypline danych referencyjnych.
visual_fail_on_missing_baseline = False

# Uncertain zone - strefa niepewnosci (score blisko progu).

# visual_uncertain_enabled:
# - True: wlacza strefe niepewnosci.
# - False: tylko twardy pass/fail.
# Skutek: True redukuje ostre decyzje na granicy progu.
visual_uncertain_enabled = True

# visual_uncertain_pixel_delta:
# - Delta dla metryki pixel dodawana do progu niepewnosci.
# - Przyklad: 0.05.
# Skutek: wyzsza wartosc = szersza strefa "do recznej weryfikacji".
visual_uncertain_pixel_delta = 0.05  # absolutna wartosc dodana do progu

# visual_uncertain_lpips_delta:
# - Delta dla LPIPS przy klasyfikacji uncertain.
# Skutek: wyzsza wartosc zmniejsza ryzyko falszywych faili granicznych.
visual_uncertain_lpips_delta = 0.05

# visual_uncertain_dists_delta:
# - Delta dla DISTS przy klasyfikacji uncertain.
# Skutek: analogicznie reguluje szerokosc strefy granicznej.
visual_uncertain_dists_delta = 0.05

# visual_viewport_presets:
# - Presety viewportow (nazwa -> (szerokosc, wysokosc)).
# - Przyklad: "mobile": (390, 844), "fhd": (1920, 1080).
# Skutek: standaryzuje rozdzielczosci i poprawia porownywalnosc screenshotow.
visual_viewport_presets = {
    "mobile": (390, 844),
    "tablet": (1024, 1366),
    "fhd": (1920, 1080),
    "2k": (2560, 1440),
    "4k": (3840, 2160),
}

# MinIO baseline storage.

# visual_minio_endpoint:
# - Endpoint MinIO/S3 dla baseline'ow.
# - Przyklad: "minio.local:9000" lub "s3.cpt-sztos.com" (bez sciezki URL).
# Skutek: wymagany przy providerze "minio".
visual_minio_endpoint = "https://s3.cpt-sztos.com"

# visual_minio_access_key:
# - Access key uzytkownika MinIO.
# Skutek: brak lub bledna wartosc = brak dostepu do bucketu.
visual_minio_access_key = "user"

# visual_minio_secret_key:
# - Secret key uzytkownika MinIO.
# Skutek: trzymaj poza repo (env/secret manager), bo to dana wrazliwa.
visual_minio_secret_key = "nc12345678"

# visual_minio_bucket:
# - Nazwa bucketu na baseline.
# - Przyklad: "visual-baselines".
# Skutek: zmiana bucketu separuje dane miedzy projektami/srodowiskami.
visual_minio_bucket = "visual-baselines"

# visual_minio_secure:
# - True: HTTPS do MinIO.
# - False: HTTP (np. lokalny dev).
# Skutek: False tylko w zaufanym srodowisku lokalnym.
visual_minio_secure = True

# Perceptual Metrics Service (PMS) post-process.

# pms_enabled:
# - True: wlacza integracje z PMS.
# - False: brak zapytan do PMS.
# Skutek: True daje dodatkowe metryki percepcyjne kosztem czasu i zaleznosci sieciowej.
pms_enabled = True

# pms_base_url:
# - Bazowy URL uslugi PMS.
# - Przyklad: "http://pms:8080".
# Skutek: pusty URL przy wlaczonym PMS spowoduje bledy polaczenia.
pms_base_url = "https://pms.cpt-sztos.com"

# pms_metric:
# - "lpips", "dists" albo "both".
# Skutek: wybor metryki wpływa na czulosc i czas obliczen.
pms_metric = "both"  # lpips|dists|both

# pms_model:
# - Model dla metryk percepcyjnych.
# - Przyklad: "alex".
# Skutek: model wpływa na charakterystyke score i koszt obliczen.
pms_model = "alex"

# pms_normalize:
# - True: normalizuje dane wejsciowe pod metryki.
# - False: bez normalizacji.
# Skutek: moze poprawic porownywalnosc wynikow miedzy roznymi obrazami.
pms_normalize = True

# pms_submit_rps:
# - Limit request/sec dla wysylania zadan do PMS.
# Skutek: zbyt wysoki moze przeciazyc serwis, zbyt niski wydluzy kolejke.
pms_submit_rps = 4.0

# pms_poll_rps:
# - Limit request/sec dla odpytywania statusu.
# Skutek: balansuje obciazenie PMS i czas oczekiwania na wynik.
pms_poll_rps = 4.0

# pms_max_inflight:
# - Maksymalna liczba jednoczesnych zadan lokalnie.
# Skutek: wyzsza wartosc = szybszy throughput, ale wieksze zuzycie zasobow.
pms_max_inflight = 10

# pms_server_active_limit:
# - Limit aktywnych zadan po stronie serwera.
# Skutek: pozwala uniknac odrzucen przy przeciążonym PMS.
pms_server_active_limit = 40

# pms_timeout_sec:
# - Timeout pojedynczego zadania PMS (sekundy).
# Skutek: za niski timeout powoduje przedwczesne fail'e przy duzych obrazach.
pms_timeout_sec = 360

# pms_retry_max:
# - Maksymalna liczba ponowien po bledzie.
# Skutek: wiecej retry zwieksza odpornosc na chwilowe problemy, ale wydluza run.
pms_retry_max = 3

# pms_health_timeout_seconds:
# - Timeout sprawdzenia health endpoint PMS.
# Skutek: niski timeout szybciej wykrywa niedostepnosc, ale moze byc zbyt agresywny.
pms_health_timeout_seconds = 5

# pms_poll_interval_ms:
# - Odstep miedzy kolejnymi pollami statusu (ms).
# Skutek: nizszy interval = szybsza reakcja, ale wiecej zapytan.
pms_poll_interval_ms = 2500

# pms_poll_idle_multiplier:
# - Mnoznik interwalu pollingu PMS, gdy brak aktywnych zadan.
# - Przyklad: 3.0 => polling idle co 3x dluzej niz bazowy interwal.
# Skutek: zmniejsza obciazenie przy bezczynnosci kosztem wolniejszej reakcji po starcie nowych zadan.
pms_poll_idle_multiplier = 10.0

# Reporting API (optional).

# reporting_enabled:
# - True: wysyla wyniki do zewnetrznego Reporting API.
# - False: brak wysylek.
# Skutek: True pozwala centralizowac raporty miedzy pipeline'ami.
reporting_enabled = True

# reporting_schema_version:
# - Wersja schematu payloadu raportowania.
# - Przyklad: "2.0".
# Skutek: musi byc zgodna z oczekiwaniem backendu raportowego.
reporting_schema_version = "2.0"

# reporting_source_project:
# - Nazwa projektu zrodlowego wysylana do API.
# Skutek: uzywana do filtrowania i grupowania raportow.
reporting_source_project = "netQArner"

# reporting_api_url:
# - Bazowy URL Reporting API.
# - Przyklad: "http://127.0.0.1:3001" lub "https://reporting.example.com".
# Skutek: bledny URL = brak raportowania mimo poprawnych testow.
reporting_api_url = "https://toc.cpt-sztos.com"

# reporting_api_token:
# - Token autoryzacyjny do Reporting API.
# Skutek: trzymaj poza repo; brak tokena moze skutkowac 401/403.
reporting_api_token = ""

# reporting_api_run_start_endpoint:
# - Endpoint startu runa.
# - Przyklad: "/test-run/start".
reporting_api_run_start_endpoint = "/test-run/start"

# reporting_api_test_result_endpoint:
# - Endpoint wysylki pojedynczego wyniku testu.
# - Przyklad: "/test-run/test-result".
reporting_api_test_result_endpoint = "/test-run/test-result"

# reporting_api_run_finish_endpoint:
# - Endpoint zakonczenia runa.
# - Przyklad: "/test-run/finish".
reporting_api_run_finish_endpoint = "/test-run/finish"

# reporting_api_bug_endpoint:
# - Endpoint raportowania buga/incydentu.
# - Przyklad: "/test-run/bug-report".
reporting_api_bug_endpoint = "/test-run/bug-report"

# reporting_api_aso_endpoint:
# - Endpoint raportu ASO (jezeli wykorzystywany w projekcie).
# - Przyklad: "/test-run/aso-report".
reporting_api_aso_endpoint = "/test-run/aso-report"

# reporting_api_note_endpoint:
# - Endpoint notatek/adnotacji.
# - Przyklad: "/test-run/note".
reporting_api_note_endpoint = "/test-run/note"

# reporting_api_timeout_seconds:
# - Timeout requestu do Reporting API.
# Skutek: wyzsza wartosc zmniejsza ryzyko timeoutow, ale wolniej wykrywa problemy sieciowe.
reporting_api_timeout_seconds = 5

# reporting_api_retries:
# - Liczba ponowien requestu po bledzie.
# Skutek: wiecej retry poprawia odpornosc na chwilowe bledy 5xx/network.
reporting_api_retries = 3

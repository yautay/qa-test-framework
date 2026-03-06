# Remote Playwright grid defaults.
is_grid_available = False
is_session_headless = True

# Browser runtime
# Supported: chromium, firefox, webkit, chrome
browser = "chromium"

# Target selector used by URL resolvers.
# Supported: demo, prod, local, or test DNS token (hostname label).
server_name = "weryfikacja.alfa"

# Optional reference environment selector for visual dual-pass.
# - demo|prod|local: selects fixed environment URL
# - any other non-empty token: treated as test DNS hostname (server_name)
reference_host = ""
server_ssh_port = "56855"

# Legacy compatibility contacts
email_for_production_tests = "kolorowy@test.pl"
phone_for_production_tests = "123123123"

# Optional direct URL override; if set, this wins over generated values.
base_url_override = ""

# Optional run metadata defaults (CLI has priority).
tester = "Michal Pielaszkiewicz"
run_note = "testy pms"
nn_ticket = "54654"

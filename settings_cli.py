# Remote Playwright grid defaults.
is_grid_available = False
is_session_headless = True

# Browser runtime
# Supported: chromium, firefox, webkit, chrome
browser = "chromium"

# Supported: test, demo, prod, local
# Suite URL mapping uses this value directly (no env override).
server_type = "test"

# Example legacy-compatible server name: "koncerz.test"
# Suite URL mapping uses this value directly (no env override).
server_name = "koncerz.test"
server_ssh_port = "56855"

# Legacy compatibility contacts
email_for_production_tests = "kolorowy@test.pl"
phone_for_production_tests = "123123123"

# Optional direct URL override; if set, this wins over generated values.
base_url_override = ""

# Optional run metadata defaults (CLI has priority).
tester = "Michał"
run_note = "NN-126533 - retesty"
nn_ticket = "54654"
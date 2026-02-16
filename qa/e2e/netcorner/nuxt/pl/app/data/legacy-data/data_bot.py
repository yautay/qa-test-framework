scenario_bot = "Scenariusz: \n" \
               "   1. Wchodzi na stronę główną'.\n" \
               "   2. Po załadowaniu CSR pobiera DOM.\n" \
               "   3. Weryfikuje widzialność skryptów.\n"

bot_test_data_google = {
    "scenario": scenario_bot,
    "headers": {
        "x-identified-src": "bot:google.com",
        "user-agent": "adsbot"
    },
}

bot_test_data_hole = {
    "scenario": scenario_bot,
    "headers": {
        "x-identified-src": "bot:dziura.pl",
        "user-agent": "adsbot"
    },
}

bot_test_data_none = {
    "scenario": scenario_bot,
}

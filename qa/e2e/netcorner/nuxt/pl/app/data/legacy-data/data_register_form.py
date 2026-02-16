from TestData.pl_komputronik_nuxt.PlCommonData import PlCommonData

pl_var = PlCommonData.variables()
pl_var_forms = PlCommonData.forms_register_data_set()

scenario = "Scenariusz: \n" \
           "   1. Wchodzi na stronę rejestracji.\n" \
           "   2. Wypełnia formularz danymi.\n" \
           "   3. Sprawdza czy pojawiły się oczekiwane błędy."

common_test_data = {
    "scenario": scenario,
}

common_forms_data = {
    "form_data": [
        pl_var_forms["forms_empty_form"],
        pl_var_forms["forms_one_character"],
    ],
    "form_errors": [
        pl_var_forms["forms_empty_form_expected_errors"],
        pl_var_forms["forms_one_character_expected_errors"],
    ],
    "form_data_same_login": [
        pl_var_forms["forms_same_login_twice"],
    ],
    "form_errors_same_login": [
        pl_var_forms["forms_same_login_twice_expected_errors"],
    ]
}

register_form_characters = {
    "register_data": common_forms_data["form_data"],
    "register_data_errors": common_forms_data["form_errors"],
}

same_login_twice = {
    "register_data": common_forms_data["form_data_same_login"],
    "register_data_errors": common_forms_data["form_errors_same_login"],
}

register_form_characters.update(common_test_data.copy())
same_login_twice.update(common_test_data.copy())

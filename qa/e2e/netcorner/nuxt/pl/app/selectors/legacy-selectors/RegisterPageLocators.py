class RegisterPageLocators:
    CONTAINER_register_page = "//h2[contains(., 'Rejestracja użytkownika')]/ancestor::div[@id='pageContent']"
    INPUT_login = "//input[@id='login']"
    INPUT_password = "//input[@id='password']"
    INPUT_password_repeated = "//input[@id='passwordRepeated']"
    CHECKBOX_customer_company_rules_terms = "//input[@id='customer_company_rules_terms']"
    CHECKBOX_customer_marketing_terms = "//input[@id='customer_marketing_terms']"
    BUTTON_register_user = "//button[contains(., 'Załóż konto')]"
    IFRAME_re_captcha = "//iframe[starts-with(@title, 'reCAPTCHA')]"
    CHECKBOX_re_captcha = "//div[@class='recaptcha-checkbox-border']"
    re_captcha_checked = "//span[contains(@class, 'recaptcha') and @aria-checked='true']"
    TOAST_negative = "//li[contains(@class, 'toast-negative')]"
    FORM_register = "//div[contains(@class, 'xl:items-center')]"
    INPUT_email = "//input[contains(@name, 'login')]"
    LABEL_company_rules = "//label[@for='customer_company_rules_terms']"
    CHECKBOX_company_rules = "//input[@id='customer_company_rules_terms']"
    LABEL_marketing_terms = "//label[@for='customer_marketing_terms']"
    CHECKBOX_marketing_terms = "//input[@id='customer_marketing_terms']"
    SECTION_password = "//ol[contains(@class, 'indent')]"
    SECTION_banners = "//div[contains(@class, 'lg:grid')]"
    BUTTON_open_login_layer = "//button[contains(., 'Zaloguj się')]"
    BUTTON_register = "//button[contains(., 'Załóż konto')]"

    ELEMENTS_register_form_combined = {
        "container": CONTAINER_register_page,
        "form_register": FORM_register,
        "email": INPUT_email,
        "login": INPUT_login,
        "password": INPUT_password,
        "re_captcha": IFRAME_re_captcha,
        "company_rules": LABEL_company_rules,
        "company_rules_checkbox": CHECKBOX_company_rules,
        "marketing_terms": LABEL_marketing_terms,
        "marketing_terms_checkbox": CHECKBOX_marketing_terms,
        "password_section": SECTION_password,
        "login_layer": BUTTON_open_login_layer,
        "register_button": BUTTON_register,
    }

    @staticmethod
    def forms_error_messages():
        return {
            "email": RegisterPageLocators.INPUT_email + "/../span",
            "password": RegisterPageLocators.INPUT_password + "/../span"
        }

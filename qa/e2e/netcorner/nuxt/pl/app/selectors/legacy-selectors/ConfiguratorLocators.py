class ConfiguratorLocators:
    CONTAINER_configurator = "//div[@id='pageContent']"
    CONTAINER_summary = "//section[contains(@data-role,'configuratorSummary')]"
    CONTAINER_footer = "//div[contains(@class,'container lg:space-y')]"

    SECTION_mandatory_elements = "//span[contains(text(), 'wymagane')]//..//..//div[contains(@class,'sm:grid-cols')]"
    SECTION_optional_elements = "//span[contains(text(), 'opcjonalne')]//..//..//div[contains(@class,'sm:grid-cols')]"

    LIST_mandatory_elements = SECTION_mandatory_elements + "//a[contains(text(),'{}')]"
    LIST_optional_elements = SECTION_optional_elements + "//a[contains(text(),'{}')]"
    LIST_selected_set_items = "//div[contains(@class,'grid-cols')]//div[contains(@class,'space-y')]"

    BUTTON_expand_section_optional = "//span[contains(text(),'Wybierz opcjonalne elementy zestawu')]"
    BUTTON_section_optional_expanded = BUTTON_expand_section_optional + "//..//i[contains(@class, 'rotate-180')]"
    BUTTON_go_to_summary = "//a[contains(@href,'summary')]"
    BUTTON_order_as_set = "//div//button[contains(@class,'order-last')]"
    BUTTON_order_as_parts = "//a[contains(@href,'cart')]/button"

    ELEMENT_selected_set_items = LIST_selected_set_items + "//a[contains(text(), '{}')]"

    SECTION_error = "//div[contains(@data-name,'ncAlert')]"

    ERROR_text = "//p[contains(text(), 'konfiguracja')]"

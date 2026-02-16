from TestCases.NetCornerProducts.Common.PageLocators.CommonAdminLocators import CommonAdminLocators


class AdminPageLocators(CommonAdminLocators):
    SELECT_manager = "//div[@class='form-row']//select[@id='ktr_storehouse_storehouse_manager_id']"
    SELECT_manager_name = SELECT_manager + "//option[contains(text(),'testy automatyczne')]"

    CHECKBOX_visible = CommonAdminLocators.ELEMENT_fieldset_parameters + "//input[@id='ktr_storehouse_storehouse_personal_receive_enabled']"
    CHECKBOX_visible_checked = CommonAdminLocators.ELEMENT_fieldset_parameters + "//input[@id='ktr_storehouse_storehouse_personal_receive_enabled' and @checked='checked']"

    CHECKBOX_active = CommonAdminLocators.ELEMENT_fieldset_parameters + "//input[@id='ktr_storehouse_storehouse_active']"
    CHECKBOX_visible_active_checked = CommonAdminLocators.ELEMENT_fieldset_parameters + "//input[@id='ktr_storehouse_storehouse_active' and @checked='checked']"

    CHECKBOX_large_volume_G1 = CommonAdminLocators.ELEMENT_fieldset_large_volume + "//input[@id='ktr_storehouse_large_volume_flags_8']"
    CHECKBOX_large_volume_checked_G1 = CommonAdminLocators.ELEMENT_fieldset_large_volume + "//input[@id='ktr_storehouse_large_volume_flags_8' and @checked='checked']"
    CHECKBOX_large_volume_G2 = CommonAdminLocators.ELEMENT_fieldset_large_volume + "//input[@id='ktr_storehouse_large_volume_flags_9']"
    CHECKBOX_large_volume_checked_G2 = CommonAdminLocators.ELEMENT_fieldset_large_volume + "//input[@id='ktr_storehouse_large_volume_flags_9' and @checked='checked']"

    LIST_company_supervisor = CommonAdminLocators.ELEMENT_fieldset_company_data + "//select[@id='ktr_company_company_supervisor_id']"
    LIST_company_supervisor_choose = CommonAdminLocators.ELEMENT_fieldset_company_data + "//select[@id='ktr_company_company_supervisor_id']//option[contains(text(), 'SI_TEST')"

    BUTTON_save = CommonAdminLocators.ELEMENT_admin_actions + "//input[@class='sf_admin_action_save']"

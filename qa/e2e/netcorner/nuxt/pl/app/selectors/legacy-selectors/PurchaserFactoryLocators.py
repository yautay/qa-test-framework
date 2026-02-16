class PurchaserFactoryLocators:
    CONTAINER_purchaser = "//section[@data-picker='purchaser']"
    BUTTON_add_purchaser_tile = "//div[@data-name='orderPickerTile']"
    BUTTON_edit_purchaser_tile_by_name_dropdown = "//p[contains(text(),'{name}')]/ancestor::article//button[@title='Edytuj']"
    BUTTON_edit_purchaser_tile_by_name = "//p[contains(text(),'{name}')]/ancestor::article/following-sibling::div//span[contains(text(), 'Edytuj')]"
    BUTTON_delete_purchaser_tile_by_name = "//p[contains(text(),'{name}')]/ancestor::article/following-sibling::div//span[contains(text(), 'Usuń')]"
    ELEMENTS_purchaser_tiles = "//article[@data-name='orderPickerTile']"
    ELEMENTS_tiles_data = ".//p"

class ReceiverFactoryLocators:
    BUTTON_add_receiver_tile = "//div[@data-name='orderPickerTile']"
    BUTTON_edit_receiver_tile_by_name_dropdown = "//p[contains(text(),'{name}')]/ancestor::article//button[@title='Edytuj']"
    BUTTON_edit_receiver_tile_by_name = "//p[contains(text(),'{name}')]/ancestor::article/following-sibling::div//span[contains(text(), 'Edytuj')]"
    BUTTON_delete_receiver_tile_by_name = "//p[contains(text(),'{name}')]/ancestor::article/following-sibling::div//span[contains(text(), 'Usuń')]"
    ELEMENTS_receiver_tiles = "//article[@data-name='orderPickerTile']"
    ELEMENTS_tiles_data = ".//p"
    BOX_warning_message = "//p[contains(text(), 'Prosimy o odświeżenie strony')]"

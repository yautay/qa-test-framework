class CategoriesLocators:
    ELEMENT_category_root_from_header = "//a[contains(text(), '{}')]//parent::div[contains(@class, 'group')]"
    ELEMENT_tile_box = "//a/p[contains(text(), '{}')]"
    ELEMENT_tile_links = "//a/span[contains(text(), '{}')]/../../ul/li/a"

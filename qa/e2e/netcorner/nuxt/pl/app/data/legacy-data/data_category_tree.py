from .PlCommonData import PlCommonData

scenario = "Scenariusz: \n"\
           "   1. Nawiguje po drzewie kategorii.\n"\
           "   2. Weryfikuje widoczność i responsywność elementów.\n"\
           "   3. Weryfikuje ładowanie stron kategori względem maenu kategorii\n"

pl_data = PlCommonData

one_level_case_1 = {
    "category_traversal": pl_data.category_tree_variables(root="RTV",
                                                          first_lvl="Telewizory")}
one_level_case_2 = {
    "category_traversal": pl_data.category_tree_variables(root="Laptopy i komputery",
                                                          first_lvl="Laptopy")}
one_level_case_3 = {
    "category_traversal": pl_data.category_tree_variables(root="Telefony i Smartwatche",
                                                          first_lvl="Telefony i Smartfony")}

two_levels_case_1 = {
    "category_traversal": pl_data.category_tree_variables(root="Sprzęt PC",
                                                          first_lvl="Peryferia PC",
                                                          second_lvl="Klawiatury")}
two_levels_case_2 = {
    "category_traversal": pl_data.category_tree_variables(root="Sprzęt PC",
                                                          first_lvl="Peryferia PC",
                                                          second_lvl="Monitory")}
two_levels_case_3 = {
    "category_traversal": pl_data.category_tree_variables(root="Sprzęt PC",
                                                          first_lvl="Części PC",
                                                          second_lvl="Karty graficzne")}

three_levels_case_1 = {
    "category_traversal": pl_data.category_tree_variables(root="Sprzęt PC",
                                                          first_lvl="Sieci i komunikacja",
                                                          second_lvl="Monitoring",
                                                          third_lvl="Kamery do monitoringu")}
three_levels_case_2 = {
    "category_traversal": pl_data.category_tree_variables(root="Sprzęt PC",
                                                          first_lvl="Oprogramowanie",
                                                          second_lvl="Programy biurowe",
                                                          third_lvl="Microsoft Office")}
three_levels_case_3 = {
    "category_traversal": pl_data.category_tree_variables(root="Sprzęt PC",
                                                          first_lvl="Części PC",
                                                          second_lvl="Chłodzenie",
                                                          third_lvl="Wentylatory do komputera")}

one_level_case_1.setdefault("scenario", scenario)
one_level_case_2.setdefault("scenario", scenario)
one_level_case_3.setdefault("scenario", scenario)
two_levels_case_1.setdefault("scenario", scenario)
two_levels_case_2.setdefault("scenario", scenario)
two_levels_case_3.setdefault("scenario", scenario)
three_levels_case_1.setdefault("scenario", scenario)
three_levels_case_2.setdefault("scenario", scenario)
three_levels_case_3.setdefault("scenario", scenario)

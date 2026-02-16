from TestData.b2b.B2BCommonData import B2BCommonData
from TestData.dktr.DktrCommonData import DktrCommonData

create_account_multichannel = {
    "scenario": "Scenariusz: \n"
                 "   1. Otwiera stronę rejestracji konta klienta w różnych kanałach sprzedaży.\n"
                 "   2. Rejestruje konto klienta z tymi samymi danymi na każdym kanale sprzedaży.\n"
                 "   3. Sprawdza czy rejestracja zakończyła się sukcesem.",
    "register_data": DktrCommonData().purchaser_data()
}

create_account_multichannel["register_data"]["email"] = create_account_multichannel["register_data"]["mail"]
create_account_multichannel["register_data"]["marketing_terms"] = True
create_account_multichannel["register_data"]["country"] = B2BCommonData().purchaser_data()["country"]
create_account_multichannel["register_data"]["vat"] = B2BCommonData().purchaser_data()["vat"]

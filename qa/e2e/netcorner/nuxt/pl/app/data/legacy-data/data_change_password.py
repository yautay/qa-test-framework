import copy

from TestData.pl_komputronik_nuxt.PlCommonData import PlCommonData
from TestData.pl_komputronik_nuxt.PlCommonKeys import OrderAsKey

scenario = "Scenariusz: \n" \
           "   1. Rejestruje klienta.\n" \
           "   2. Wchodzi na stronę zmiany hasła.\n" \
           "   3. Zmienia hasło na nowe.\n" \
           "   4. Loguje się z nowym hasłem."

change_password_register_data = PlCommonData.register_data()
change_password = {
    "order_as": OrderAsKey.ORDER_AS_REGISTERED,
    "register_data": copy.deepcopy(change_password_register_data),
    "old_password": change_password_register_data["password"],
    "new_password": "nowe_haslo123!"}
login_data = {
    "login_details": {
        "email": change_password_register_data["email"],
        "password": change_password["new_password"]}}
change_password.update(login_data)
change_password.setdefault("scenario", scenario)

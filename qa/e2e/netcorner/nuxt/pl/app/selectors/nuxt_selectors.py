class LoginSelectors:
    LOGIN_BUTTON = "[data-testid='login']"


class CookieSelectors:
    ACCEPT_BUTTONS = [
        "#onetrust-accept-btn-handler",
        "button:has-text('Akceptuję')",
        "button:has-text('Zaakceptuj')",
    ]
    REJECT_BUTTONS = [
        "#onetrust-reject-all-handler",
        "button:has-text('Odrzuć')",
    ]
    OVERLAY = "#onetrust-consent-sdk"


class AuthSelectors:
    OPEN_LOGIN_LAYER_BUTTON = "button:has-text('Zaloguj')"
    LOGIN_EMAIL_INPUTS = ["input#login", "input[name='login']", "input[type='email']"]
    LOGIN_PASSWORD_INPUTS = ["input#password", "input[name='password']", "input[type='password']"]
    LOGIN_SUBMIT_BUTTONS = [
        "button:has-text('Zaloguj')",
        "button[type='submit']",
    ]
    ORDER_WITHOUT_REGISTRATION_BUTTONS = [
        "button:has-text('Zamów bez rejestracji')",
        "button:has-text('Bez rejestracji')",
    ]


class OrdersSelectors:
    ORDER_TILE = "[data-testid='order-tile']"


class CartSelectors:
    INTERACTIVE_CANDIDATES = [
        "button",
        "a[href*='checkout']",
        "input[type='number']",
        "[data-testid*='cart']",
        "a[href]",
    ]
    TEXT_CANDIDATES = ["Koszyk", "Twój koszyk", "Wróć do zakupów"]
    PROCEED_TO_CHECKOUT_BUTTONS = [
        "button:has-text('Przejdź dalej')",
        "button:has-text('Dalej')",
        "a[href*='checkout']",
    ]


class ProductListSelectors:
    SEARCH_INPUTS = [
        "input[name='search']",
        "input[type='search']",
        "input[placeholder*='Szukaj']",
    ]
    SEARCH_SUBMIT_BUTTONS = [
        "button[type='submit']",
        "button:has-text('Szukaj')",
    ]
    PRODUCT_LINKS = [
        "[data-name='listingContent'] a[href*='/product/']",
        "[data-name='listingContent'] a[href*='/p/']",
        "a[href*='/product/']",
    ]
    ADD_TO_CART_BUTTONS = [
        "//div[contains(@class, 'border-transparent')]//div[contains(@class, 'self-end')]//button",
        "button[data-name='addToCartButton']",
        "button:has-text('Do koszyka')",
        "button:has-text('Dodaj do koszyka')",
    ]
    DIGITAL_LICENSE_FILTER_TEXT = "Realizacja elektroniczna"


class ProductPageSelectors:
    ADD_TO_CART_BUTTONS = [
        "//div[@data-name='addToCartDesktop']//button[@data-name='addToCartButton']",
        "button[data-name='addToCartButton']",
        "button:has-text('Do koszyka')",
        "button:has-text('Dodaj do koszyka')",
    ]


class LayerSelectors:
    GO_TO_CART_BUTTONS = [
        "button:has-text('Przejdź do koszyka')",
        "button:has-text('Do koszyka')",
        "a[href*='/cart']",
    ]
    CLOSE_RECOMMENDATION_BUTTONS = [
        "button[aria-label='close']",
        "button:has-text('Zamknij')",
    ]


class CheckoutSelectors:
    INTERACTIVE_CANDIDATES = [
        "form input",
        "form button",
        "input[name*='email']",
        "input[name*='name']",
        "button[type='submit']",
        "button",
    ]
    TEXT_CANDIDATES = ["Dostawa", "Płatność", "Twój koszyk", "Wróć do zakupów"]
    DELIVERY_TILES = {
        "courier": "//div[@data-name='orderShippingPicker']//p[contains(text(), 'kurier')]/" "ancestor::article",
        "storehouse": "//div[@data-name='orderShippingPicker']//p[contains(text(), 'Salony')]/" "ancestor::article",
        "digital": "//div[@data-name='orderShippingPicker']//p[contains(text(), 'elektroniczna')]/" "ancestor::article",
    }
    RECEIVER_INPUTS = {
        "name": ["input[name*='name']", "input[id*='name']"],
        "surname": ["input[name*='surname']", "input[id*='surname']"],
        "phone": ["input[name*='phone']", "input[type='tel']"],
        "email": ["input[name*='mail']", "input[type='email']"],
        "postal_code": ["input[name*='postal']", "input[id*='postal']"],
        "city": ["input[name*='city']", "input[id*='city']"],
        "street_name": ["input[name*='street']", "input[id*='street']"],
        "street_number": ["input[name*='building']", "input[name*='streetNumber']", "input[id*='streetNumber']"],
    }
    PICKUP_LOCATION_INPUTS = ["input[name*='localization']", "input[placeholder*='kod']"]
    PICKUP_SEARCH_BUTTONS = [
        "//div[@data-name='orderMap']//div[@data-name='searchInput']//button",
        "//span[contains(text(), 'kod')]/ancestor::div[@data-name='searchInput']//button",
        "button:has-text('Szukaj')",
    ]
    PICKUP_POINT_OPTIONS = ["button:has-text('Poznan')", "button:has-text('Outlet')"]
    PICKUP_SCROLL_CONTAINER = "//div[@data-name='parcelList']/parent::div"
    PICKUP_POINT_TILE_BY_NAME = (
        "//div[@data-name='orderMap']//p[contains(text(), '{point_name}')]/ancestor::"
        "article[@data-name='orderPickerTile']"
    )
    PICKUP_POINT_NAMES = (
        "//div[@data-name='parcelList']/parent::div//article[@data-name='orderPickerTile']//"
        "p[contains(@class, 'font-semibold')]"
    )
    DELIVERY_WITH_LIFT_CHECKBOX = "//input[@id='deliveryBringing']"
    DELIVERY_WITH_LIFT_TILE = "//span[contains(text(), 'Bezpieczne wniesienie')]"
    PAYMENT_TILE_BY_TEXT = (
        "//div[@data-name='orderPaymentPicker']//" "p[contains(text(), '{payment}')]/ancestor::article"
    )
    TERMS_CHECKBOX_IDS = [
        "#regulation",
        "#outletTerms",
        "#electronicLicenceTerms",
        "#molpCspTerms",
    ]
    SUBMIT_ORDER_BUTTONS = [
        "section[data-name='orderSummaryCheckout'] button",
        "button:has-text('Składam zamówienie')",
        "button:has-text('Zamawiam')",
    ]


class ThankYouSelectors:
    ORDER_NUMBER = "//p[contains(.,'Numer zamówienia')]/following-sibling::p"
    ORDER_SUMMARY = "//p[contains(.,'Do zapłaty')]/following-sibling::span"

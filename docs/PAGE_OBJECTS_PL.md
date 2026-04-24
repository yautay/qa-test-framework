# Page Objects Guide

Ten dokument jest dla osób, które dobrze znają testy manualne, ale dopiero zaczynają automatyzować. Jeśli umiesz rozpisać scenariusz testowy krok po kroku, to masz już bardzo dobry fundament. Page Object to po prostu sposób zapisania takiego scenariusza w kodzie tak, żeby test był czytelny, stabilny i łatwy do utrzymania.

W tym repo page objecty są intensywnie używane w `qa/e2e/netcorner/nuxt/pl/lib/page_objects/`.

Normatywny kontrakt dla contributorów i agentów jest w `docs/E2E_PAGE_OBJECT_CONTRACT.md`.
Ten dokument pozostaje przewodnikiem edukacyjnym. Jeśli przykłady kiedyś rozjadą się z kontraktem, pierwszeństwo ma kontrakt.

## Po co nam page objecty

Bez page objectów test bardzo szybko zamienia się w listę selektorów i kliknięć:

```python
page.locator("#login").fill("user@example.com")
page.locator("#password").fill("secret")
page.get_by_role("button", name="Zaloguj się").click()
```

To działa, ale ma kilka wad:

- test wie za dużo o HTML-u,
- selektory są porozrzucane po wielu plikach,
- przy zmianie UI trzeba poprawiać wiele testów,
- trudno odróżnić logikę biznesową od technicznej obsługi przeglądarki.

Z page objectem ten sam zamiar wygląda tak:

```python
home.open_login_overlay().log_client(user.email, user.password)
```

Test mówi wtedy, co robimy biznesowo, a nie jak dokładnie wygląda DOM.

## Jak myśleć o architekturze w tym repo

Najprostszy model mentalny wygląda tak:

`Page -> Section -> Component -> Flow/Wrapper`
`Overlay -> Flow/Wrapper`

Każda warstwa ma inne zadanie.

## 1. Page

`Page` reprezentuje pełny ekran lub widok aplikacji.

Przykłady:

- `HomePage`
- `ListingPage`
- `ProductPage`
- `CartPage`
- `CheckoutPage`

Page najczęściej:

- zna swój `PATH`,
- potrafi się otworzyć i poczekać aż ekran będzie gotowy,
- udostępnia sekcje typu `header`, `content`, `footer`,
- ma metody nawigacyjne, które zwracają kolejny page object albo overlay.

Przykład z tego repo:

```python
class HomePage(BasePage):
    PATH = "/"

    def wait_loaded(self, *, state: LoadState = "domcontentloaded", timeout: int | None = None) -> HomePage:
        super().wait_loaded(state=state, timeout=timeout)
        self.header.wait_visible()
        self.navigation.wait_visible()
        self.content.wait_visible()
        self.footer.wait_visible()
        return self

    def open_register_page(self) -> RegisterPage:
        self.open_login_overlay().enter_register_form()
        return RegisterPage(self.page, self.base_url).wait_loaded()
```

To jest bardzo dobry wzorzec:

- `wait_loaded()` sprawdza, że ekran naprawdę jest gotowy,
- metoda `open_register_page()` zwraca nowy page object, bo kontekst ekranu się zmienia.

## 2. Section

`Section` grupuje większy obszar strony.

Najczęściej są to:

- `HeaderSection`
- `NavigationSection`
- `ContentSection`
- `FooterSection`

Sekcja nie powinna trzymać całej logiki biznesowej. Jej rola to porządkowanie komponentów w obrębie jednego obszaru strony.

Przykład:

```python
class HeaderSection(BaseComponent):
    def __init__(self, page: Page):
        self.__header_root = HeaderComponent(page)
        super().__init__(self.__header_root.root, name="Header Section")
        self.__search_bar: SearchBarComponent | None = None
        self.__actions: HeaderActionsComponent | None = None

    @property
    def actions(self) -> HeaderActionsComponent:
        if self.__actions is None:
            self.__actions = HeaderActionsComponent(self.root)
        return self.__actions
```

Czyli:

- sekcja ma własny root,
- wewnątrz udostępnia mniejsze komponenty,
- dzięki temu test lub page nie musi znać szczegółów DOM.

## 3. Component

`Component` to najważniejszy klocek. Reprezentuje konkretny element UI: formularz, tabelę, kafel produktu, blok ceny, filtry, panel płatności.

Dobry komponent:

- ma jeden spójny zakres odpowiedzialności,
- działa tylko we własnym rootcie,
- ukrywa selektory,
- wystawia proste metody typu `fill_...`, `click_...`, `get_...`, `set_...`.

Przykład:

```python
class RegisterClientComponent(BaseComponent):
    ROOT_SELECTOR = "form"

    def __init__(self, scope: Page | Locator) -> None:
        super().__init__(self.resolve_root(scope, self.ROOT_SELECTOR), name="Register Client Component")
        self.__input_login = self.find("#login")
        self.__input_password = self.find("#password")
        self.__button_register = self.find('button:has-text("Załóż konto")')

    @step("Wpisuję login klienta: {email}")
    def fill_login(self, email: str) -> Self:
        self.safe_type(self.__input_login, email)
        return self

    @step("Klikam przycisk 'Załóż konto'")
    def submit_registration(self) -> None:
        self.pointer_click(self.__button_register)
```

To jest styl, którego chcemy:

- selektory są prywatne,
- nazwy metod opisują intencję,
- dekorator `@step(...)` daje czytelny ślad w raportach,
- metody mutujące ten sam komponent mogą zwracać `Self`.

## 4. Overlay

`Overlay` to modal, popup, toast albo inna warstwa pojawiająca się ponad stroną.

Przykłady:

- `LoginOverlay`
- `PasswordRecoveryOverlay`
- `ToastOverlay`
- overlaye checkoutowe

Overlay powinien mieć własny obiekt, bo:

- ma inny root niż page,
- pojawia się warunkowo,
- często ma własną logikę otwierania i zamykania.

Przykład:

```python
class LoginOverlay(BaseComponent):
    def __init__(self, page: Page):
        super().__init__(page.locator('[data-name="loginForm"]:visible').first, name="Login Overlay")
        self.__input_login = self.find("#loginEmail")
        self.__button_login = self.root.get_by_role(role="button", name="Zaloguj się")

    @step("Loguję klienta loginem: {client_login} hasłem: {client_pwd}")
    def log_client(self, client_login: str, client_pwd: str) -> None:
        self.safe_type(self.__input_login, client_login)
        self.safe_type(self.__input_password, client_pwd)
        self.pointer_click(self.__button_login)
```

## 5. Flow / Wrapper

`Flow` albo `Wrapper` to wyższy poziom niż page object. Używamy go wtedy, kiedy scenariusz przechodzi przez kilka ekranów i zależy nam na biznesowym opisie procesu.

Przykłady z repo:

- `ClientWrappers`
- `SelectProductWrappers`
- `CartAndCheckoutWrappers`

Wrapper jest dobry wtedy, gdy:

- scenariusz jest długi,
- powtarza się w wielu testach,
- obejmuje kilka page objectów,
- chcesz uprościć test do kilku czytelnych kroków.

Przykład:

```python
with step_context("Otwieram stronę główną"):
    home = HomePage(self.__page, self.__runtime_env.base_url)
    home.open().wait_loaded()

with step_context("Otwieram panel logowania i wybieram formularz rejestracji"):
    register_page = home.open_register_page()
```

Czyli:

- page object odpowiada za ekran,
- wrapper odpowiada za cały proces.

## Kiedy stworzyć Page, a kiedy tylko Component

Zadaj sobie proste pytanie: czy użytkowniczka trafia na osobny ekran, czy tylko obsługuje fragment istniejącego ekranu?

Twórz `Page`, gdy:

- jest osobny URL,
- zmienia się cały kontekst ekranu,
- ekran ma własne `wait_loaded()`.

Twórz `Component`, gdy:

- to fragment strony,
- działa w obrębie istniejącego ekranu,
- ma własne akcje i odczyty danych, ale nie jest osobnym widokiem.

Twórz `Overlay`, gdy:

- coś wyskakuje nad stroną,
- element nie należy logicznie do głównego layoutu strony,
- po zamknięciu wracasz do tego samego page.

## Gdzie co umieszczać w katalogach

W praktyce używamy takiego podziału:

- `page_objects/pages/` - pełne ekrany
- `page_objects/sections/` - większe obszary ekranu
- `page_objects/components/` - mniejsze, konkretne elementy UI
- `page_objects/overlays/` - modale, popupy, toast-y
- `lib/flows/` - większe procesy biznesowe oparte o page objecty

Jeśli nie wiesz, gdzie dodać klasę, najpierw odpowiedz: czy to jest ekran, obszar, widget czy popup?

## Bazowe klasy, z których korzystamy

### `BasePage`

Lokalny `BasePage` rozszerza bazę frameworkową i dodaje dostęp do `overlays`.

```python
class BasePage(FrameworkBasePage):
    @property
    def overlays(self):
        if self._overlays is None:
            self._overlays = Overlays(self.page)
        return self._overlays
```

To oznacza, że z każdego page objectu możesz wygodnie zrobić:

```python
home.overlays.login.wait_visible()
```

### `BaseComponent`

Lokalny `BaseComponent` dodaje helper `resolve_root(...)`.

```python
class BaseComponent(FrameworkBaseComponent):
    @staticmethod
    def resolve_root(scope: Page | Locator, root_selector: str) -> Locator:
        if isinstance(scope, Page):
            return scope.locator(root_selector)
        if scope.evaluate("(node, selector) => node instanceof Element && node.matches(selector)", root_selector):
            return scope
        return scope.locator(root_selector)
```

W praktyce daje to bardzo wygodny wzorzec konstruktora:

```python
class SomeComponent(BaseComponent):
    ROOT_SELECTOR = "[data-name='someComponent']"

    def __init__(self, scope: Page | Locator) -> None:
        super().__init__(self.resolve_root(scope, self.ROOT_SELECTOR), name="Some Component")
```

Dzięki temu komponent działa zarówno wtedy, gdy dostanie `Page`, jak i wtedy, gdy dostanie root sekcji lub innego komponentu.

Nowa zasada dla locatorów w konstruktorze:

- `self.find(...)` dla pierwszego poziomu w obrębie `self.root`,
- `self.root.get_by_*` dla semantycznych locatorów Playwrighta,
- `parent.locator(...)` lub `parent.get_by_*` tylko dla świadomie zagnieżdżonych struktur,
- bez cichego fallbacku `A -> B -> C`, jeśli UI nie ma jawnie wspieranego wariantu.

## Najważniejsze zasady pisania metod

### 1. Nazwa ma opisywać intencję biznesową

Dobre nazwy:

- `open_login_overlay()`
- `open_register_page()`
- `fill_password()`
- `choose_payment_method()`
- `get_available_payment_methods()`
- `set_electronic_invoice(True)`

Słabsze nazwy:

- `click_button1()`
- `do_action()`
- `handle_form()`
- `process()`

Po nazwie metody ma być jasne, co robi użytkowniczka.

### 2. Metoda powinna robić jedną rzecz

Nie mieszaj w jednej metodzie:

- wpisywania danych,
- kliknięcia submit,
- weryfikacji całego biznesowego rezultatu.

Lepszy podział:

```python
form.fill_login(user.email)
form.fill_password(user.password)
form.submit_registration()
```

niż:

```python
form.register_user(user)
```

Wyjątek: jeśli wyższy poziom naprawdę opisuje proces biznesowy, przenieś to do wrappera, nie do komponentu.

### 3. Akcje in-place zwracają `Self`

Jeśli metoda zostawia Cię dalej na tym samym komponencie, zwracaj `Self`.

Przykład:

```python
@step("Akceptuję obowiązkowe regulaminy")
def accept_required_terms(self) -> Self:
    self.pointer_click(self.__checkbox_terms)
    return self
```

To pozwala pisać czytelnie:

```python
register_page.content.register_form.fill_login(email).fill_password(password).accept_required_terms()
```

### 4. Zmiana kontekstu zwraca nowy obiekt

Jeśli po akcji przechodzisz na inny ekran, zwracaj nowy `Page` lub `Overlay`.

Przykład:

```python
def open_register_page(self) -> RegisterPage:
    self.open_login_overlay().enter_register_form()
    return RegisterPage(self.page, self.base_url).wait_loaded()
```

### 5. Odczyt danych zwraca dane, nie locator

Test nie powinien znać locatorów. Test ma dostać prostą informację.

Dobre przykłady zwrotów:

- `bool`
- `str`
- `Decimal`
- `dataclass`
- `tuple[...]`, jeśli naprawdę ma sens

W repo często używamy `dataclass`, np. do danych produktu czy metod płatności.

## Kiedy używać `dataclass`

Jeśli ekran zwraca zestaw danych, `dataclass` jest bardzo dobrym wyborem.

Przykład:

```python
@dataclass(frozen=True, slots=True)
class PaymentMethodData:
    name: str
    surcharge: Decimal
```

Zalety:

- test dostaje czytelny obiekt,
- pola są nazwane,
- łatwiej porównać oczekiwania z tym, co widzi UI,
- kod jest bardziej samoopisowy niż np. lista albo słownik bez typu.

## Jak pisać selektory

To jest jedno z najważniejszych miejsc dla stabilności testów.

Preferowana kolejność:

- stabilne atrybuty typu `data-name`, `data-role`, `data-picker`,
- semantyczne selektory Playwrighta, np. `get_by_role(...)`,
- czytelny tekst, jeśli jest stabilny biznesowo,
- CSS/XPath tylko wtedy, gdy nie ma lepszej opcji.

Dobre przykłady z repo:

- `[data-name="orderPickerTile"]`
- `[data-picker="paymentMethod"]`
- `get_by_role("button", name="Zaloguj się")`

Staraj się:

- zawsze szukać we własnym rootcie komponentu,
- nie budować bardzo długich selektorów obejmujących pół strony,
- nie używać selektorów zależnych od przypadkowych klas CSS, jeśli są lepsze znaczniki domenowe.

## `step` i `step_context` - bardzo ważna zasada

W tym repo `step` zawsze importujemy z:

```python
from qa.e2e.netcorner.lib.step_api import step, step_context
```

Nie importujemy `allure.step` bezpośrednio.

Powód jest prosty:

- repo ma własny wrapper,
- wrapper zapisuje kroki nie tylko do Allure, ale też do wewnętrznego trace'u testu,
- dzięki temu raporty są spójne.

Używaj:

- `@step(...)` dla metod,
- `with step_context(...)` dla większych bloków w wrapperach i flow.

Przykład komponentu:

```python
@step("Wybieram metodę płatności: {payment_method}")
def choose_payment_method(self, payment_method: PaymentMethods) -> Decimal:
    ...
```

Przykład wrappera:

```python
with step_context("Otwieram stronę główną"):
    home = HomePage(self.__page, self.__runtime_env.base_url)
    home.open().wait_loaded()
```

## `wait_loaded()` i `wait_visible()`

Osoby zaczynające automatyzację często próbują walczyć z niestabilnością przez `sleep(...)`. W tym repo tego nie chcemy.

Zamiast tego:

- page powinien mieć własne `wait_loaded()`,
- komponent i sekcja powinny mieć sensowne `wait_visible()`,
- po akcji przejścia na nowy ekran dobrze od razu zwrócić obiekt po `wait_loaded()`.

Dzięki temu test nie zgaduje, kiedy UI jest gotowe.

## Page-level API - preferowany styl

Jeśli jakiś scenariusz jest naturalnie rozumiany jako przejście między ekranami, logikę przejścia trzymaj na poziomie page, a nie w teście.

Lepszy styl:

```python
register_page = home.open_register_page()
account_page = home.open_account_page()
configurator_page = home.open_configurator_from_banner()
```

Słabszy styl:

```python
home.header.actions.open_login()
home.overlays.login.enter_register_form()
register_page = RegisterPage(page, base_url).wait_loaded()
```

Druga wersja działa, ale test zna za dużo detali przejścia. Jeśli flow otwierania rejestracji się zmieni, chcesz poprawić jeden page object, nie wiele testów.

## Jak krok po kroku dodać nowy page object

### Krok 1. Rozpisz scenariusz jak w teście manualnym

Przykład myślenia:

1. Użytkowniczka otwiera stronę produktu.
2. Widzi blok ceny.
3. Klika „Dodaj do koszyka”.
4. System pokazuje popup lub zmienia stan strony.

To już podpowiada strukturę:

- `ProductPage`
- `ProductPriceComponent`
- ewentualnie overlay po dodaniu do koszyka

### Krok 2. Znajdź root komponentu

Nie zaczynaj od pojedynczego inputa. Najpierw znajdź kontener logiczny, np.:

- formularz,
- blok ceny,
- tabelę,
- sekcję płatności.

Potem w komponencie ustaw `ROOT_SELECTOR`.

### Krok 3. Zbuduj komponent

Minimalny szablon:

```python
from __future__ import annotations

from typing import Self

from playwright.sync_api import Locator, Page

from qa.e2e.netcorner.lib.step_api import step
from qa.e2e.netcorner.nuxt.pl.lib.page_objects.base_component import BaseComponent


class ExampleComponent(BaseComponent):
    ROOT_SELECTOR = "[data-name='example']"

    def __init__(self, scope: Page | Locator) -> None:
        super().__init__(self.resolve_root(scope, self.ROOT_SELECTOR), name="Example Component")
        self.__input_name = self.find("#name")
        self.__button_save = self.find("button:has-text('Zapisz')")

    @step("Wpisuję nazwę: {name}")
    def fill_name(self, name: str) -> Self:
        self.safe_type(self.__input_name, name)
        return self

    @step("Zapisuję formularz")
    def save(self) -> None:
        self.pointer_click(self.__button_save)
```

### Krok 4. Podłącz komponent do sekcji

```python
class ExampleContentSection(ContentSection):
    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.__example: ExampleComponent | None = None

    @property
    def example(self) -> ExampleComponent:
        if self.__example is None:
            self.__example = ExampleComponent(self.root)
        return self.__example
```

### Krok 5. Podłącz sekcję do page

```python
class ExamplePage(BasePage):
    PATH = "/example"

    def __init__(self, page: Page, base_url: str):
        super().__init__(page, base_url)
        self.__content: ExampleContentSection | None = None

    def wait_loaded(self, *, state: LoadState = "domcontentloaded", timeout: int | None = None) -> ExamplePage:
        super().wait_loaded(state=state, timeout=timeout)
        self.content.wait_visible()
        return self

    @property
    def content(self) -> ExampleContentSection:
        if self.__content is None:
            self.__content = ExampleContentSection(self.page)
        return self.__content
```

### Krok 6. Dodaj metodę page-level, jeśli przejście ma sens biznesowy

Jeżeli z danego page da się wejść na kolejny ekran, schowaj tę logikę do page objectu.

```python
def open_summary_page(self) -> SummaryPage:
    self.content.example.save()
    return SummaryPage(self.page, self.base_url).wait_loaded()
```

### Krok 7. Dopiero teraz użyj tego w teście lub wrapperze

```python
example_page = ExamplePage(page, runtime_env.base_url).open().wait_loaded()
example_page.content.example.fill_name("Ala")
summary_page = example_page.open_summary_page()
```

## Jak wygląda dobry test z page objectami

Test powinien opisywać scenariusz, a nie HTML.

Dobry kierunek:

```python
def test_basic_orders(page, context, runtime_env, auth_case, delivery_case):
    _prepare_client_session(page, context, runtime_env, auth_case)
    selected_product = SelectProductWrappers(page, context, runtime_env).select_test_product(
        first_aviable_laptop_case()
    )
    assert selected_product is not None
    assert selected_product.product_page_data is not None

    checkout_wrappers = CartAndCheckoutWrappers(page, context, runtime_env)
    checkout_wrappers.process_cart()
    checkout_wrappers.process_checkout(
        delivery_case.delivery_type,
        delivery_case.delivery_objects,
        delivery_case.purchaser_objects,
        delivery_case.payment_objects,
    )
```

Tu test pokazuje proces zakupowy, a nie strukturę DOM. To jest właśnie cel page objectów i wrapperów.

## Czego nie robić

### Nie wystawiaj locatorów do testów

To zły kierunek:

```python
test_page.content.form.submit_button.click()
```

Test nie powinien wiedzieć, że istnieje `submit_button`. Test powinien wołać metodę typu `submit_registration()`.

### Nie duplikuj tych samych helperów w wielu klasach

Jeśli kilka komponentów potrzebuje tej samej logiki, przenieś ją do wspólnego helpera. W tym repo mamy np. `page_objects/utils.py`.

### Nie twórz dwóch różnych API do tej samej akcji

Jeśli akcja „przejdź dalej w koszyku” jest dostępna przez footer, nie twórz równolegle osobnego bytu robiącego dokładnie to samo inną drogą. Jedna odpowiedzialność, jedno oczywiste API.

### Nie importuj `step` bezpośrednio z Allure

Używaj tylko wrappera z `qa.e2e.netcorner.lib.step_api`.

### Nie wkładaj całej logiki biznesowej do komponentu

Komponent ma obsługiwać fragment UI. Jeśli scenariusz przechodzi przez kilka ekranów, użyj wrappera.

### Nie używaj `sleep(...)`, jeśli można czekać na stan UI

Najpierw spróbuj:

- `wait_loaded()`
- `wait_visible()`
- `expect(...)`
- helperów typu `pointer_click`, `safe_fill`, `safe_type`

## Kiedy dodać asercję do page objectu

To częste pytanie.

Dobra zasada:

- page object może robić małe techniczne sprawdzenia potrzebne do stabilności,
- główne asercje biznesowe powinny zostać w teście.

Techniczne sprawdzenie jest OK, np.:

- po kliknięciu checkboxa sprawdzenie, czy pole stało się widoczne,
- sprawdzenie, czy komponent istnieje przed interakcją,
- walidacja, że da się rozpoznać layout listy metod dostawy.

Natomiast porównanie oczekiwanej ceny z rzeczywistą ceną zwykle należy do testu albo wrappera, nie do niskopoziomowego komponentu.

## Jak pisać czytelne kroki w raporcie

Tytuły kroków pisz językiem użytkowniczki, nie językiem implementacji.

Dobre przykłady:

- `Wpisuję login klienta: {email}`
- `Klikam kafelek dostawy: Wysyłka kurierem`
- `Akceptuję obowiązkowe regulaminy`

Słabsze przykłady:

- `Set login input`
- `Click submit btn`
- `Handle delivery`

Ktoś czytający raport ma rozumieć, co zostało zrobione w aplikacji.

## Styl typowania i zwracanych wartości

W tym repo warto trzymać się tych zasad:

- dodawaj typy do argumentów i zwrotów,
- jeśli metoda może zwrócić brak wyniku, zaznacz to jako `| None`,
- używaj `Self` dla metod in-place,
- używaj `dataclass(frozen=True, slots=True)` dla prostych obiektów danych,
- nie używaj `Any`, jeśli da się łatwo podać konkretny typ.

## Checklist przed oddaniem nowego page objectu

Zanim uznasz pracę za skończoną, sprawdź:

- czy klasa jest w dobrym katalogu,
- czy ma dobrze dobrany root,
- czy selektory są stabilne,
- czy metody mają sensowne nazwy,
- czy akcje in-place zwracają `Self`,
- czy przejścia między ekranami zwracają nowy page object,
- czy odczyt danych zwraca typy lub dataclass, a nie locator,
- czy używasz `step` i `step_context` z naszego wrappera,
- czy test korzysta z page objectu, a nie z surowych selektorów,
- czy nie dało się uprościć API na poziomie page,
- czy nie dodałaś duplikatu istniejącej odpowiedzialności,
- czy kod przechodzi choć minimalną walidację.

## Jak weryfikować zmiany

Po zmianach w page objectach minimum to:

```bash
python -m compileall qa/e2e/netcorner/nuxt/pl/lib qa/e2e/netcorner/nuxt/pl/tests
```

Jeśli zmiana dotyczy realnego scenariusza, uruchom też pasujący test lub suite, np.:

```bash
python -m pytest qa/e2e/netcorner/nuxt/pl/tests/tests_orders/test_basic_orders.py -q
```

Szersza walidacja backendowo-frameworkowa:

```bash
make test-aso
```

## Krótka ściąga na koniec

Jeśli masz zapamiętać tylko kilka rzeczy, zapamiętaj te:

- test ma mówić o scenariuszu, nie o selektorach,
- page object ma ukrywać techniczne szczegóły UI,
- component ma mieć jedną odpowiedzialność,
- page ma wystawiać naturalne przejścia między ekranami,
- wrapper ma obsługiwać dłuższy proces biznesowy,
- `step` bierzemy z `qa.e2e.netcorner.lib.step_api`, nie z Allure,
- dane z UI zwracamy jako typy lub `dataclass`, nie jako locator,
- stabilny root i dobre selektory są ważniejsze niż sprytny kod.

Jeśli tworzysz nowy page object i nie wiesz, od czego zacząć, zacznij jak testerka manualna: rozpisz ekran, rozpisz kroki użytkowniczki, nazwij intencje, a dopiero potem zamieniaj to na klasy i metody.

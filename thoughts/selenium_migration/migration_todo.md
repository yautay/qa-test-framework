---
date: 2026-05-12T00:00:00+02:00
git_commit: ee7e62b2ad3517ed49a183807d9a91d284a259de
branch: feature/NN-24016-ai-w-pisaniu-testow-e2e
repository: qa-test-netquarner
topic: "Lista wszystkich testów Selenium do migracji — pl_komputronik_nuxt — posortowana wg złożoności"
tags: [todo, migration, checklist, all-suites, selenium, playwright]
last_updated: 2026-05-13
---

# Lista testów do migracji: pl_komputronik_nuxt

Źródło: `nc-functional-tests-py/TestCases/NetCornerProducts/pl_komputronik_nuxt/Test/`
Cel: `qa-test-netquarner/qa/e2e/netcorner/nuxt/pl/tests/`

## Legenda

| Symbol | Znaczenie |
|---|---|
| `[x]` | Zmigrowany i gotowy |
| `[ ]` | Do zrobienia |
| `🔴 admin` | Blokowany przez brak admin panel page objects (DEBT-001) |
| `🟡 mailhog` | Blokowany przez brakujące metody w MailInboxService (Sprint 4) |
| `🔵 new-po` | Wymaga nowych page objects (nie admin) |
| `🟣 alpha` | Przeniesione do Fazy 2-alfa (brak stabilnych danych/scenariusza na env) |
| `⚪ covered` | Funkcjonalność pokryta przez inny istniejący test |
| `🚫 infra` | Skrypt infrastrukturalny, nie test e2e |

**Łącznie: 103 testy Selenium** (bez SetUpNUXT, BotTestsNUXT, ProdTestsNUXT)

---

## ✅ Faza 0 — Już zmigrowane (baseline)

Istniejące testy Playwright pokrywające poniższe scenariusze:

- [x] `FormsTestsNUXT/TestRegisterForm.py` — rejestracja klienta ⚪ covered → `tests_account/test_create_account.py`
- [x] `ConfiguratorTestsNUXT/TestConfiguratorFunctionality.py` → `tests_configurator/test_configurator_basic_flow.py`
- [x] `ConfiguratorTestsNUXT/TestConfiguratorWithPromoCodeFunctionality.py` → `tests_configurator/test_configurator_entry.py`
- [x] `OrdersTestsNUXT/TestOrderWithInpost.py` — ⚪ covered → `tests_orders/test_basic_orders.py[inpost]`
- [x] `OrdersTestsNUXT/TestOrderWithDhlPop.py` — ⚪ covered → `tests_orders/test_basic_orders.py[dhl_pop]`
- [x] `SmokeTestsNUXT/TestOrders.py` — podstawowe zamówienie ⚪ covered → `tests_orders/test_basic_orders.py`

---

## 🟢 Faza 1 — Proste testy UI / brak admina / infrastruktura w większości gotowa

**Nakład:** ~3–5 dni | **Cel:** `tests_layout/`, `tests_search/`, `tests_navigation/`
**Zależności:** brak nowych page objects poza drobnymi komponentami (header, footer, search bar — już istnieją)

### LayoutElementsTestsNUXT → `tests/tests_layout/`

- [x] `TestHeaderElements.py` → `test_header_elements.py`
  - Weryfikacja widoczności elementów nagłówka, linków, kategorii zero-level, wyszukiwarki
- [x] `TestHomePageElements.py` → `test_homepage_elements.py`
  - Bannery, kontenery produktów na stronie głównej
- [x] `TestRegisterPageElements.py` → `test_register_page_elements.py`
  - 🔵 new-po: weryfikacja elementów formularza rejestracji (pola, przyciski, błędy)
- [x] `TestFooterElements.py` → `test_footer_elements.py`
  - Linki i sekcje stopki (FooterSection już istnieje)

### SortingTestsNUXT → `tests/tests_listing/`

- [x] `TestSortingProductList.py` → `test_sorting_product_list.py`
  - Sortowanie listingu: 4 warianty sortowania z asercją kolejności
- [x] `TestSortingProductSearch.py` → `test_sorting_product_search.py`
  - Sortowanie wyników wyszukiwania

### SearchTestsNUXT → `tests/tests_search/`

- [x] `TestSimpleSearch.py` → `test_simple_search.py`
  - Wyszukiwanie frazy → niepusta lista wyników
- [x] `TestSearchSuggestions.py` → `test_search_suggestions.py`
  - 🔵 new-po: weryfikacja podpowiedzi wyszukiwarki (suggester) — SearchBarComponent istnieje
- [x] `TestSearchListings.py` → `test_search_listings.py`
  - Wyszukiwanie → nawigacja na listing wyników

### CategoryTreeTestsNUXT → `tests/tests_navigation/`

- [x] `TestCategoryTree.py` → `test_category_tree.py`
  - 🔵 new-po: traversal 1/2/3 poziomów drzewa kategorii przez NavigationSection

---

## 🟡 Faza 2 — Produkty i konto / brak admina / potrzeba nowych page objects

**Nakład:** ~5–8 dni | **Cel:** `tests/tests_products/`, `tests/tests_account/`
**Zależności:** Nowe komponenty: labels, comparison, opinion, omnibus price, CRUD MyAccount

### ProductTestsNUXT → `tests/tests_products/`

- [x] `TestAddProductToCart.py` → `test_add_product_to_cart.py`
  - Dodanie produktu z różnych miejsc: listing, wyszukiwarka, strona produktu
- [x] `TestProductAvailability.py` → `test_product_availability.py`
  - Status dostępności, dostępność w magazynach — ProductPage już istnieje
- [x] `TestTemporarilyUnavailableProducts.py` → `test_temporarily_unavailable_products.py`
  - Produkty tymczasowo niedostępne — AvailabilityStatus w ListingComponents już istnieje
- [x] `TestOmnibusPrices.py` → `test_omnibus_prices.py`
  - 🔵 new-po: ceny omnibus / przekreślone na karcie produktu (OmnibusPriceComponent)
- [x] `TestProductLabels.py` → `test_product_labels.py`
  - 🔵 new-po: etykiety produktów (np. "Bestseller", "Nowość") — ProductLabelsComponent
- [x] `TestProductComparison.py` → `test_product_comparison.py`
  - 🔵 new-po: dodanie produktów do porównania + widok porównania — ComparisonComponent
- [x] `TestAddProductOpinion.py` → `test_add_product_opinion.py`
  - 🔵 new-po: dodanie opinii do produktu — ProductOpinionComponent
- [x] `TestProductsListFiltering.py` → `test_products_list_filtering.py`
  - Filtrowanie listingu — FiltersComponent (expand_all_filters już istnieje)
- [x] `TestProductsListSezamFilter.py` → `test_products_list_sezam_filter.py`
  - 🟣 alpha: test zaimplementowany, warunkowy `skip` przy braku filtra Sezam na env
- [x] `TestAdhocProduct.py` → `test_adhoc_product.py`
  - 🟣 alpha: test zaimplementowany, warunkowy `skip` przy braku produktu ad-hoc na env
- [x] `TestProductOzo.py` → `test_product_ozo.py`
  - Widget OZO na homepage + kluczowe dane komponentu

### FormsTestsNUXT → `tests/tests_forms/`

- [x] `TestReceiverPurchaserFormCheckout.py` → `test_forms_checkout.py`
  - 🟣 alpha: test zaimplementowany, `skip` gdy checkout nie renderuje sekcji nabywcy
- [x] `TestReceiverPurchaserFormAccount.py` → `test_forms_account.py`
  - 🟣 alpha: smoke formularzy konta + warunkowy `skip` przy brakujących akcjach UI

### PurchaserReceiverTestsNUXT → `tests/tests_account/`

- [x] `TestCRUDPurchaserReceiverMyAccount.py` → `test_crud_purchaser_receiver_account.py`
  - 🟣 alpha: smoke CRUD (nawigacja + akcje dodawania)
- [x] `TestCRUDPurchaserReceiverCheckout.py` → `test_crud_purchaser_receiver_checkout.py`
  - 🟣 alpha: smoke CRUD overlay checkout (wypełnienie + zamknięcie overlay)

### 🟣 Faza 2-alfa — odłożone elementy Fazy 2

- [x] `TestReceiverPurchaserFormCheckout.py` → `test_forms_checkout.py`
  - Powód alfa: zależny od wariantu renderowania sekcji nabywcy na checkout; wariant docelowy: kurier + BLIK.
- [x] `TestReceiverPurchaserFormAccount.py` → `test_forms_account.py`
  - Powód alfa: obecnie smoke, do rozszerzenia do pełnej walidacji formularzy.
- [x] `TestCRUDPurchaserReceiverMyAccount.py` → `test_crud_purchaser_receiver_account.py`
  - Powód alfa: obecnie smoke, do rozszerzenia do pełnego cyklu create/update/delete.
- [x] `TestCRUDPurchaserReceiverCheckout.py` → `test_crud_purchaser_receiver_checkout.py`
  - Powód alfa: obecnie smoke, do rozszerzenia o update/delete i asercje danych; wariant docelowy: kurier + BLIK.

### 🟪 Faza 2-beta — hardening danych i scenariuszy produktowych

- [ ] `TestProductsListSezamFilter.py` → `test_products_list_sezam_filter.py`
  - Beta scope: podpiąć stabilny produkt/listing Sezam i usunąć warunkowy `skip`.
- [ ] `TestAdhocProduct.py` → `test_adhoc_product.py`
  - Beta scope: podpiąć stabilny produkt ad-hoc i doprecyzować pełny kontrakt asercji.

---

## 🔵 Faza 3 — Zamówienia / brak admina / nowe page objects

**Nakład:** ~3–5 dni | **Cel:** `tests/tests_orders/`
**Zależności:** OrderDetailPage (konto klienta), min_qty detekcja

### OrdersTestsNUXT (bez admina) → `tests/tests_orders/`

- [ ] `TestOrderCompanyData.py` → `test_orders_company_data.py`
  - Zamówienie z nabywcą firmowym + NIP — checkout OK, asercja NIP bez admina
  - Infrastruktura: `company_checkout_purchaser()` — gotowa ✅
- [ ] `TestOrderPrices.py` → `test_orders_prices.py`
  - Weryfikacja numeru zamówienia — checkout OK, asercja ceny bez admina (TODO admin)
- [ ] `TestOrderCancel.py` → `test_orders_cancel.py`
  - 🔵 new-po: `OrderDetailPage` (konto klienta) + przycisk anulowania + odczyt statusu
- [ ] `TestOrderWithMinQtyProduct.py` → `test_orders_min_qty.py`
  - 🔵 new-po: detekcja `min_qty` z `ProductComponents.get_min_qty_for_order()`
- [ ] `TestOrderMatrixVsList.py` → `test_orders_matrix_vs_list.py`
  - Checkout z różnymi kodami pocztowymi (matrix/list path) — bez admin konfiguracji

### MonitoringTestsNUXT → `tests/tests_monitoring/`

- [ ] `TestMonitoring.py` → `test_monitoring_checkout.py`
  - Wiele kombinacji dostawy/płatności bez finalizacji zamówienia (`submit_order=False`)
  - Infrastruktura: `CartAndCheckoutWrappers` — gotowa ✅

---

## 🔴 Faza 4 — Wymaga admin panel page objects (DEBT-001)

**Nakład:** ~8–12 dni (po zbudowaniu admina) | **Cel:** Uzupełnienie TODO + nowe testy
**Zależności:** Admin panel page objects — patrz `admin_panel_ticket.md`

### OrdersTestsNUXT (z adminem) → `tests/tests_orders/`

- [ ] `TestOrderBigSizeWithLift.py` → `test_orders_big_size_with_lift.py`
  - 🔴 admin: weryfikacja zamówienia + 🔵 new-po: `DeliveryTypes.BIG_SIZE_WITH_LIFT` + overlay
- [ ] `TestOrderBigSizeWithoutLift.py` → `test_orders_big_size_without_lift.py`
  - 🔴 admin: weryfikacja zamówienia + 🔵 new-po: `DeliveryTypes.BIG_SIZE_WITHOUT_LIFT`
- [ ] `TestOrderDimensionModule.py` → `test_orders_dimension_module.py`
  - 🔴 admin + 🔵 new-po: cart restriction assertions (28 kombinacji produktów gabarytowych)
- [ ] `TestOrderCompanyData.py` — domknięcie TODO
  - 🔴 admin: weryfikacja NIP w danych nabywcy w adminie
- [ ] `TestOrderPrices.py` — domknięcie TODO
  - 🔴 admin: porównanie cen TYP vs admin

### SplitPaymentTestsNUXT → `tests/tests_orders/`

- [ ] `TestSplitPayment.py` → `test_split_payment.py`
  - 🔴 admin: weryfikacja zamówienia z płatnością split (zwiększona ilość w koszyku)

### AggregatorTestsNUXT → `tests/tests_aggregator/`

- [ ] `TestAggregator.py` → `test_aggregator.py`
  - 🔴 admin: tworzenie ofert agregatora → weryfikacja widoczności na froncie
- [ ] `TestAggregatorPromoCode.py` → `test_aggregator_promo_code.py`
  - 🔴 admin: tworzenie kodów promo agregatora

### CartRestrictionTestsNUXT → `tests/tests_cart_restrictions/`

*BasicTests (13 testów):*
- [ ] `TestOwnStoreProduct1.py` → `test_cart_restriction_own_store_1.py` 🔴 admin
- [ ] `TestOwnStoreProduct2.py` → `test_cart_restriction_own_store_2.py` 🔴 admin
- [ ] `TestOwnStoreProduct3.py` → `test_cart_restriction_own_store_3.py` 🔴 admin
- [ ] `TestOwnStoreProduct8.py` → `test_cart_restriction_own_store_8.py` 🔴 admin
- [ ] `TestOwnStoreProduct9.py` → `test_cart_restriction_own_store_9.py` 🔴 admin
- [ ] `TestShippingWarehouseProduct10.py` → `test_cart_restriction_shipping_warehouse_10.py` 🔴 admin
- [ ] `TestShippingWarehouseProduct11_1.py` → `test_cart_restriction_shipping_warehouse_11_1.py` 🔴 admin
- [ ] `TestShippingWarehouseProduct12_1.py` → `test_cart_restriction_shipping_warehouse_12_1.py` 🔴 admin
- [ ] `TestShippingWarehouseProduct16_1.py` → `test_cart_restriction_shipping_warehouse_16_1.py` 🔴 admin
- [ ] `TestShippingWarehouseProduct17.py` → `test_cart_restriction_shipping_warehouse_17.py` 🔴 admin
- [ ] `TestShippingWarehouseProduct18.py` → `test_cart_restriction_shipping_warehouse_18.py` 🔴 admin
- [ ] `TestWcrProduct.py` → `test_cart_restriction_wcr.py` 🔴 admin
- [ ] `TestDeliveryPendingProducts.py` → `test_cart_restriction_delivery_pending.py` 🔵 new-po (bez admina)

*AdditionalTests (14 testów):*
- [ ] `TestOwnStoreProduct4.py` → `test_cart_restriction_own_store_4.py` 🔴 admin
- [ ] `TestOwnStoreProduct5.py` → `test_cart_restriction_own_store_5.py` 🔴 admin
- [ ] `TestOwnStoreProduct6.py` → `test_cart_restriction_own_store_6.py` 🔴 admin
- [ ] `TestOwnStoreProduct7.py` → `test_cart_restriction_own_store_7.py` 🔴 admin
- [ ] `TestShippingWarehouseProduct11_2.py` → `test_cart_restriction_shipping_warehouse_11_2.py` 🔴 admin
- [ ] `TestShippingWarehouseProduct12_2.py` → `test_cart_restriction_shipping_warehouse_12_2.py` 🔴 admin
- [ ] `TestShippingWarehouseProduct13.py` → `test_cart_restriction_shipping_warehouse_13.py` 🔴 admin
- [ ] `TestShippingWarehouseProduct14.py` → `test_cart_restriction_shipping_warehouse_14.py` 🔴 admin
- [ ] `TestShippingWarehouseProduct15.py` → `test_cart_restriction_shipping_warehouse_15.py` 🔴 admin
- [ ] `TestShippingWarehouseProduct16_2.py` → `test_cart_restriction_shipping_warehouse_16_2.py` 🔴 admin
- [ ] `TestCrossProductsProduct1.py` → `test_cart_restriction_cross_1.py` 🔴 admin
- [ ] `TestCrossProductsProduct2.py` → `test_cart_restriction_cross_2.py` 🔴 admin
- [ ] `TestCrossProductsProduct16.py` → `test_cart_restriction_cross_16.py` 🔴 admin
- [ ] `TestCrossProductsProduct17.py` → `test_cart_restriction_cross_17.py` 🔴 admin

*Dropshipping (2 testy):*
- [ ] `TestDropshippingCartRestrictions.py` → `test_cart_restriction_dropshipping.py` 🔵 new-po
- [ ] `TestAdvancedDropshippingCartRestrictions.py` → `test_cart_restriction_dropshipping_advanced.py` 🔵 new-po

### AdminTestsNUXT → `tests/tests_admin/`

- [ ] `TestAdminReports.py` → `test_admin_reports.py`
  - 🔴 admin: scraping listy zamówień, generowanie raportu — pure admin test
- [ ] `TestErrorPages.py` → `test_error_pages.py`
  - 🔴 admin: weryfikacja stron błędów (może być realizowana bez admina częściowo)

### SearchTestsNUXT (przeniesione z Fazy 1 — wymagają admina) → `tests/tests_search/`

- [ ] `TestSimpleSearchExceptions.py` → `test_simple_search_exceptions.py`
  - 🔴 admin: czyta wyjątki kategorii z `AdminPage.AdminFunctionalObjects` (settingsExceptionList)
- [ ] `TestSearchListingsExceptions.py` → `test_search_listings_exceptions.py`
  - 🔴 admin: czyta `settingsExceptionList` z admina przed testem
- [ ] `TestSearchGroupCodes.py` → `test_search_group_codes.py`
  - 🔴 admin: tworzy kody grupowe produktów w adminie przed testem

---

## 🔴🟡 Faza 5 — Wymaga admin + Mailhog (uzupełnienia)

**Nakład:** ~5–8 dni (po Fazach 3+4 i Sprint 4) | **Cel:** Zaawansowane testy orders + promotions + employee
**Zależności:** Admin panel (DEBT-001) + brakujące metody MailInboxService

### OrdersTestsNUXT (admin + mailhog) → `tests/tests_orders/`

- [ ] `TestOrderStatuses.py` → `test_orders_statuses.py`
  - 🔴 admin: zmiana statusów zamówienia
  - 🟡 mailhog: `has_mail_with_subject_containing` + `MailSubjects.ORDER_STATUS_CHANGED`
  - 🔵 new-po: `OrderDetailPage` — odczyt statusu (jeśli nie zbudowane w Fazie 3)
- [ ] `TestOrderPartnerStorehouse.py` → `test_orders_partner_storehouse.py`
  - 🔴 admin: weryfikacja zamówienia
  - 🟡 mailhog: `count_mails_matching` + `MailSubjects.PARTNER_STOREHOUSE_ORDER`
- [ ] `TestOrderCartOffer.py` → `test_orders_cart_offer.py`
  - 🔴 admin: tworzenie oferty koszykowej + wysyłka do klienta + URL oferty
  - 🟡 mailhog: `MailSubjects.CART_OFFER` + link z maila
  - 🔵 new-po: `CartOfferPage` — strona oferty koszykowej (URL → cena → dodaj do koszyka)
- [ ] `TestOrderOzo.py` → `test_orders_ozo.py`
  - 🔴 admin: reset liczników OZO w setUp/tearDown (fixture)
  - 🔵 new-po: `OzoBoxComponent` (homepage), `LimitedSaleComponent` (karta produktu)
- [ ] `TestOrderDigitalLicense.py` → `test_orders_digital_license.py`
  - 🔴 admin: weryfikacja zamówienia
  - 🔵 new-po: obsługa produktów cyfrowych w `SelectProductWrappers` (flaga `digital=True`, filtry)

### PromotionsTestsNUXT → `tests/tests_promotions/`

- [ ] `TestPromotionsPromotionCodes.py` → `test_promotions_promo_codes.py`
  - 🔴 admin: tworzenie kodu promo → weryfikacja zastosowania w koszyku + adminie
- [ ] `TestPromotionsSezamCrossedOutPrice.py` → `test_promotions_sezam.py`
  - 🔴 admin: konfiguracja promocji Sezam + weryfikacja cen przekreślonych
- [ ] `TestPromotionsPromotionService.py` → `test_promotions_service.py`
  - 🔴 admin: usługi promocyjne (montaż, ubezpieczenie) w zamówieniu
- [ ] `TestPromotionsPromotionCodesOnProductPage.py` → `test_promotions_promo_codes_product_page.py`
  - 🔴 admin + 🔵 new-po: kody promo widoczne na karcie produktu

### EmployeeProgramTestsNUXT → `tests/tests_employee_program/`

- [ ] `TestEmployeeProgramGroupOrderSms.py` → `test_employee_program_order_sms.py`
  - 🔴 admin: tworzenie kodu SMS + 🟡 mailhog: weryfikacja maila
- [ ] `TestEmployeeProgramGroupOrderQr.py` → `test_employee_program_order_qr.py`
  - 🔴 admin: tworzenie kodu QR
- [ ] `TestEmployeeProgramGroupRegisterSms.py` → `test_employee_program_register_sms.py`
  - 🔴 admin + 🟡 mailhog
- [ ] `TestEmployeeProgramGroupRegisterQr.py` → `test_employee_program_register_qr.py`
  - 🔴 admin
- [ ] `TestEmployeeProgramGroupCrudSms.py` → `test_employee_program_crud_sms.py`
  - 🔴 admin + 🟡 mailhog: CRUD kodów SMS
- [ ] `TestEmployeeProgramGroupCrudQr.py` → `test_employee_program_crud_qr.py`
  - 🔴 admin: CRUD kodów QR

---

## 🚫 Poza zakresem migracji e2e

Poniższe nie są testami e2e w sensie scenariuszy użytkownika:

| Plik | Powód wykluczenia |
|---|---|
| `SetUpNUXT/TestSetUpTestsProducts.py` | 🚫 infra: skrypt resetujący produkty testowe w adminie |
| `SetUpNUXT/TestSetUpTestsPromotionsSezam.py` | 🚫 infra: konfiguracja promocji Sezam |
| `SetUpNUXT/TestSetUpTestsPromotionsService.py` | 🚫 infra: konfiguracja usług promocyjnych |
| `SetUpNUXT/TestSetUpTestsPromoCodes.py` | 🚫 infra: tworzenie kodów promo |
| `SetUpNUXT/TestSetUpIndexProducts.py` | 🚫 infra: re-indeksacja produktów |
| `ProdTestsNUXT/TestOrdersProd.py` | 🚫 osobny scope: testy na środowisku prod |
| `BotTestsNUXT/BotTests.py` | 🚫 nie ma prefixu Test*, bot tests |
| `BotTestsNUXT/WPRocketTest.py` | 🚫 nie ma prefixu Test*, performance |

---

## Podsumowanie

| Faza | Testy | Blokery | Szacowany nakład |
|---|---|---|---|
| ✅ Faza 0 — Już gotowe | 6 | — | — |
| ✅ Faza 1 — Pure UI | 10 | brak | ✅ DONE |
| 🟡 Faza 2 — Produkty + konto | 16 | 🔵 nowe PO | ~5–8 dni |
| 🔵 Faza 3 — Zamówienia bez admina | 6 | 🔵 nowe PO | ~3–5 dni |
| 🔴 Faza 4 — Wymaga admina | 40 | 🔴 DEBT-001 | ~8–12 dni |
| 🔴🟡 Faza 5 — Admin + Mailhog | 18 | 🔴 DEBT-001 + 🟡 Sprint 4 | ~5–8 dni |
| 🚫 Poza zakresem | 8 | — | — |
| **Łącznie do migracji** | **91** | | **~24–38 dni** |

### Status implementacji (2026-05-13)

- Zaimplementowano 16/16 testów Fazy 2 (w tym 6 testów oznaczonych jako Faza 2-alfa / smoke-warunkowe).
- Dodane pliki testów: `qa/e2e/netcorner/nuxt/pl/tests/tests_products/`.
- Dodane komponenty PO: `comparison_component.py`, `omnibus_price_component.py`, `product_opinion_component.py` + rozszerzenie `hero_component.py` o widget OZO.
- Dodane testy Faza 2-alfa: `qa/e2e/netcorner/nuxt/pl/tests/tests_forms/` oraz testy CRUD w `qa/e2e/netcorner/nuxt/pl/tests/tests_account/`.
- Weryfikacja: `python -m compileall qa/e2e/netcorner/nuxt/pl/lib qa/e2e/netcorner/nuxt/pl/tests` oraz collect nowych suit.

---

## Odwołania

- Analiza infrastruktury: `thoughts/selenium_migration/research.md`
- Plan sprintów: `thoughts/selenium_migration/plan.md`
- Prompt do AI: `thoughts/selenium_migration/migration_prompt.md`
- Ticket admin panel: `thoughts/selenium_migration/admin_panel_ticket.md`
- Wzorzec testu: `qa/e2e/netcorner/nuxt/pl/tests/tests_orders/test_basic_orders.py`
- Kontrakt PO: `docs/E2E_PAGE_OBJECT_CONTRACT.md`

# Visual Timeout Postmortem (PyCharm vs CLI)

## Objaw

- `python -m pytest -m visual` przechodzi pierwsze kilka testow (zwykle `full_page`),
  a kolejne testy `element` wpadaja w timeout Playwright (`Locator.screenshot: Timeout 30000ms exceeded`).
- Czasem screenshoty sa biale.

## Co nie bylo przyczyna

- `framework/visual/scenario_loader.py` nie byl winny.
- Loader tylko parsuje JSON scenariuszy i nie decyduje o nawigacji/URL/screenshotach.

## Faktyczna przyczyna

- Konflikt hookow `pytest_configure` miedzy suite'ami:
  - visual ustawial `base_url` na host PL,
  - ale conftesty e2e potrafily potem nadpisac `config._runtime_env.base_url` na host B2B.
- Efekt uboczny:
  - test visual ladowal zly host,
  - selektory z PL (`[data-name='DailyDealWidget']` itp.) nie istnialy,
  - `locator.screenshot()` czekal 30s i timeoutowal.

## Naprawa wdrozona w repo

1. Wymuszenie ignorowania certyfikatow globalnie (dla runtime w `qa`):
   - `qa/conftest.py` -> `env = replace(load_env(), ignore_https_errors=True)`

2. Utrwalenie rozstrzygnietego runtime env (CLI/server/base_url):
   - `qa/conftest.py` -> `_base_url_resolver(config)` wywolywany w `pytest_configure`
   - `qa/conftest.py` -> `_base_url_resolver` zawsze zapisuje finalne `config._runtime_env`

3. Zabezpieczenie przed nadpisaniem `base_url` przez e2e podczas uruchomien visual:
   - `qa/e2e/netcorner/nuxt/pl/conftest.py`
   - `qa/e2e/netcorner/nuxt/b2b/conftest.py`
   - Guard: jesli `markexpr == "visual"`, to e2e `pytest_configure` robi `return`.

## Jak szybko diagnozowac podobny problem

1. Sprawdz traceback pierwszego faila (`--maxfail=1 -vv -s`).
2. Porownaj `page.url` z oczekiwanym hostem suite.
3. Jesli timeout jest na `locator.screenshot`, sprawdz czy selector istnieje na aktualnym hostcie.
4. Zweryfikuj, czy inny `conftest.py` nie nadpisuje `config._runtime_env` po visual hooku.

## Szybka komenda kontrolna

```bash
python -m pytest -m visual -vv -s --maxfail=1
```

Oczekiwany rezultat po fixie: brak timeoutow `Locator.screenshot` wynikajacych z nieprawidlowego hosta.

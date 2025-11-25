# Uruchamianie testów wizualnych BackstopJS

## Generowanie pliku konfiguracyjnego testów 
Umożliwia wybór kanału sprzedaży, zakresu testów oraz dodatkowych opcji filtrowania scenariuszy oraz skonfigurowanie adresów testówek.

```npx lib/system/write-backstop-config.js --testHost="selenium.alfa --referenceHost="platnosci.test" --filter="product-page"```

```npx lib/system/write-backstop-config.js --filter="product-page"```

```npx lib/system/write-backstop-config.js```

```npx lib/system/write-backstop-config.js --filter="product-page" --site=komputronik-pl --outFile=my_backstop_config.json```

```npm run backstop:config -- --filter="product-page no-html-cache" --site=komputronik-pl --outFile=my_backstop_config.json```

### argumenty:

```--testHost``` - (opcjonalnie) definicja testówki np "selenium.alfa" (domyślnie)

```--referenceHost``` - (opcjonalnie) definicja testówki referencyjnej np "selenium.alfa", pominięta porównuje względem repozytorium obrazów (TO DO)

```--filter``` - (opcjonalne) filtr scenariuszy po etykietach (label). Tokeny rozdzielone spacją. Logika AND.

```--site``` - (opcjonalne) wybór kanału sprzedaży, domyślnie PL.

```--outFile``` - (opcjonalne) nazwa pliku wyjściowego z konfiguracją BackstopJS, domyślnie "backstop_config_run_timestamp.json



## Tworzenie obrazów referencyjnych
```npx backstop reference --config=<wygenerowany plik konfiguracyjny>.json```

## Uruchamianie testów wizualnych
```npx backstop test --config=<wygenerowany plik konfiguracyjny>.json```

# Filtrowanie scenariuszy
Moduł filter.js służy do filtrowania scenariuszy BackstopJS
na podstawie pola "label". Umożliwia wybór tylko tych testów,
których etykiety zawierają określone tokeny.

Tokeny są rozdzielane wyłącznie spacją. Filtr działa według
logiki AND – aby scenariusz został zwrócony, każdy z podanych
tokenów musi wystąpić w polu "label".
- Filtrowanie odbywa się wyłącznie po polu "label".
- Token = dokładny ciąg znaków rozdzielony spacją.
- NIE dzielimy tokenów po znaku "-" ani po żadnych innych
znakach (np. "html-cache" i "no-html-cache" to osobne tokeny).
- Wszystkie tokeny muszą wystąpić w label (logika AND).
- Porównania są case-insensitive.
- Jeśli filtr nie jest ustawiony – wszystkie scenariusze są
zwracane bez zmian.

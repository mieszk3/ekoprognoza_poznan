# Ekoprognoza Poznań dla Home Assistant

Nieoficjalna integracja Home Assistant, która odczytuje sekcję **EKOPROGNOZA DLA POZNANIA**
ze strony [Atmosfera dla Poznania](https://www.poznan.pl/mim/wos/atmosfera.html) i pokazuje,
czy dziś (i prognozowo jutro) obowiązuje zakaz palenia w kominkach, oraz prognozę stężenia
PM10 na 3 dni.

## Kiedy obowiązuje zakaz

Zgodnie z uchwałą antysmogową dla Poznania (Sejmik Województwa Wielkopolskiego,
nr XXXIX/942/17) osoby, które mają w domu **inne, ekologiczne źródło ciepła** (sieć
ciepłownicza, gaz, prąd, urządzenie spełniające wymagania Ekoprojektu), nie mogą palić
w kominkach, piecach kaflowych i „kozach”, gdy:

- w poprzedniej dobie średnie 24-godzinne stężenie PM10 przekroczyło 50 µg/m³, **oraz**
- prognozowane jest utrzymanie się tego przekroczenia.

Miasto sygnalizuje taki dzień na stronie ikoną przekreślonego płomienia. Integracja odczytuje
właśnie tę ikonę, więc stan „dziś” odpowiada temu, co publikuje miasto. Stan „jutro” jest
tylko prognozą, bo zależy od faktycznego pomiaru z bieżącego dnia.

> Od 1 stycznia 2026 r. kominki i piece **niespełniające wymagań Ekoprojektu** są w Poznaniu
> zakazane na stałe, niezależnie od ekoprognozy. Ta integracja ma sens tylko dla urządzeń
> spełniających te wymagania.

Integracja ma charakter informacyjny i nie stanowi porady prawnej. W razie wątpliwości
rozstrzyga komunikat na stronie miasta.

## Instalacja

### Marketplace / HACS (repozytorium niestandardowe)

1. Home Assistant 2026.11 i nowsze: **Ustawienia → Marketplace → Dodaj z linku**.
   Starsze wersje: **HACS → menu ⋮ → Niestandardowe repozytoria**.
2. Wklej `https://github.com/mieszk3/ekoprognoza_poznan`, kategoria **Integracja**.
3. Zainstaluj „Ekoprognoza Poznań” i zrestartuj Home Assistant.

### Ręcznie

Skopiuj folder `custom_components/ekoprognoza_poznan` do katalogu
`config/custom_components/` w Home Assistant i zrestartuj Home Assistant.

### Konfiguracja

**Ustawienia → Urządzenia i usługi → Dodaj integrację → Ekoprognoza Poznań.**
Integracja nie ma żadnych ustawień; można ją dodać tylko raz.

## Encje

| Encja | Opis |
| --- | --- |
| `sensor.ekoprognoza_poznan_kominek_dzis` | `allowed` („Można palić”) / `banned` („Zakaz palenia”) na dziś |
| `sensor.ekoprognoza_poznan_kominek_jutro` | to samo na jutro (prognoza) |
| `sensor.ekoprognoza_poznan_pm10_dzis` | prognozowane PM10 na dziś, µg/m³ |
| `sensor.ekoprognoza_poznan_pm10_jutro` | prognozowane PM10 na jutro, µg/m³ |
| `sensor.ekoprognoza_poznan_pm10_pojutrze` | prognozowane PM10 na pojutrze, µg/m³ |

Encje kominka mają atrybuty: `data`, `pm10`, `poziom` (kolor z legendy strony), `statusy`
(ikony: `hold`, `no-fire`, `like`), `komunikaty`, `ostrzezenia`, `prognoza`, `zrodlo`,
`pobrano`.

## Odświeżanie

Strona jest pobierana przy starcie Home Assistant oraz codziennie o **6:30** i **18:00**.
Gdy pobranie się nie uda, integracja ponawia próbę co 30 minut. Encje wybierają kartę
prognozy po dacie, więc po północy „dziś” od razu pokazuje wczorajszą kartę „jutro”. Jeśli
strona nie ma karty na dany dzień, encja jest niedostępna (zamiast pokazywać nieaktualny stan).

## Przykłady na dashboard

Wymagają kart [Mushroom](https://github.com/piitaya/lovelace-mushroom).

Badge w nagłówku widoku:

```yaml
type: custom:mushroom-template-badge
entity: sensor.ekoprognoza_poznan_kominek_dzis
label: Kominek
content: >-
  {% if is_state(entity, 'banned') %}Zakaz palenia{% elif is_state(entity, 'allowed') %}Można palić{% else %}Brak danych{% endif %}
icon: "{{ 'mdi:fireplace-off' if is_state(entity, 'banned') else 'mdi:fireplace' }}"
color: "{{ 'red' if is_state(entity, 'banned') else 'green' if is_state(entity, 'allowed') else 'grey' }}"
tap_action:
  action: more-info
```

Kafelek z dziś i jutro:

```yaml
type: custom:mushroom-template-card
entity: sensor.ekoprognoza_poznan_kominek_dzis
primary: >-
  Kominek: {% if is_state(entity, 'banned') %}zakaz palenia{% elif is_state(entity, 'allowed') %}można palić{% else %}brak danych{% endif %}
secondary: >-
  Dziś PM10 {{ states('sensor.ekoprognoza_poznan_pm10_dzis') }} µg/m³ ·
  Jutro: {% set j = states('sensor.ekoprognoza_poznan_kominek_jutro') %}{{ 'zakaz' if j == 'banned' else 'można' if j == 'allowed' else '?' }}
  ({{ states('sensor.ekoprognoza_poznan_pm10_jutro') }} µg/m³)
icon: "{{ 'mdi:fireplace-off' if is_state(entity, 'banned') else 'mdi:fireplace' }}"
color: "{{ 'red' if is_state(entity, 'banned') else 'green' if is_state(entity, 'allowed') else 'grey' }}"
multiline_secondary: true
tap_action:
  action: more-info
```

## Rozwój

Parser (`parser.py`) nie zależy od Home Assistant i ma testy na zapisanej stronie:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements_test.txt
.venv/bin/pytest -q tests
```

Ikona integracji (`brand/icon.png`, `brand/icon@2x.png`) jest generowana skryptem
`scripts/generate_icon.py` (wymaga Pillow).

Integracja odczytuje HTML strony miasta, więc zmiana jej układu może ją zepsuć. W takim
przypadku encje przechodzą w stan niedostępny, a w logach pojawia się błąd
`Unexpected page layout`. Zgłoszenia mile widziane w
[Issues](https://github.com/mieszk3/ekoprognoza_poznan/issues).

## Licencja

[MIT](LICENSE)

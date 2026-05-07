# GNSS Planning Tool

Aplikacja webowa (Streamlit) do analizy widoczności satelitów GNSS i wartości DOP
dla wybranej lokalizacji i daty.

**Obsługiwane systemy:** GPS (G) · GLONASS (R) · Galileo (E) · BeiDou (C)

---

## Funkcje

- Wykres elewacji satelitów w ciągu doby
- Skyplot dla wybranej epoki
- Wykresy GDOP / PDOP / HDOP / VDOP / TDOP
- Mapa groundtrack satelitów
- Automatyczne pobieranie pliku BRDC z serwera NASA CDDIS
- Obsługa maski odcięcia i wyboru systemów GNSS

---

## Wymagania

- Python 3.8+
- Zależności z pliku `requirements.txt`:
  - streamlit
  - plotly
  - pandas
  - numpy
  - pyproj

---

## Instalacja

```bash
# 1. Utwórz środowisko wirtualne
python -m venv venv

# 2. Aktywuj środowisko
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux / macOS

# 3. Zainstaluj zależności
pip install -r requirements.txt
```

---

## Uruchomienie

```bash
streamlit run app.py
```

Aplikacja otworzy się automatycznie w przeglądarce pod adresem `http://localhost:8501`.

---

## Plik nawigacyjny BRDC

Plik BRDC zawiera efemerydy satelitów potrzebne do obliczeń.
Można go podać na dwa sposoby:

**Opcja 1 — automatyczne pobieranie z NASA CDDIS**

Ustaw zmienną środowiskową przed uruchomieniem:

```bash
# Windows
set CDDIS_EMAIL=twoj@email.com

# Linux / macOS
export CDDIS_EMAIL=twoj@email.com
```

Następnie zaznacz checkbox *"Pobierz automatycznie"* w sidebarze.

**Opcja 2 — plik lokalny**

Pobierz plik `.rnx` ręcznie z https://cddis.nasa.gov i umieść go w folderze `brdc/`.
Podaj pełną ścieżkę w polu tekstowym w aplikacji.

---

## Parametry wejściowe

| Parametr | Opis |
|---|---|
| Data | Dzień obserwacji (tylko przeszłość) |
| φ [°N] | Szerokość geograficzna obserwatora |
| λ [°E] | Długość geograficzna obserwatora |
| h [m] | Wysokość obserwatora nad elipsoidą |
| Maska [°] | Minimalny kąt elewacji satelity |
| Systemy GNSS | GPS / GLONASS / Galileo / BeiDou |

---

## Kodowanie satelitów

| System | Zakres ID |
|---|---|
| GPS | G01 – G32 |
| GLONASS | R01 – R24 |
| Galileo | E01 – E36 |
| BeiDou | C01 – C63 |

---

## Struktura projektu

```
KM_GNSS/
├── app.py              # Interfejs użytkownika (Streamlit)
├── GNSS.py             # Obliczenia efemeryd i DOP
├── wizualizacje.py     # Wykresy Plotly
├── rinex_studenci.py   # Parser plików RINEX 3
├── requirements.txt    # Zależności Python
└── brdc/               # Folder na pliki nawigacyjne BRDC
```

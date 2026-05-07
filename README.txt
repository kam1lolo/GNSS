Aplikacja Streamlit do analizy widoczności satelitów GNSS
i wartości DOP dla wybranej lokalizacji i daty.

Obsługiwane systemy: GPS, GLONASS, Galileo, BeiDou

## Wymagania
Python 3.8+

## Instalacja
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux/Mac
pip install -r requirements.txt

## Uruchomienie
streamlit run app.py

## Plik nawigacyjny BRDC
Opcja automatyczna: ustaw zmienną środowiskową CDDIS_EMAIL=twoj@email.com
Opcja manualna: pobierz plik .rnx z https://cddis.nasa.gov i podaj ścieżkę w aplikacji
README

# 1. Utwórz środowisko wirtualne
python -m venv venv

# 2. Aktywuj środowisko wirtualne
venv\Scripts\activate

# 3. Zainstaluj zależności
pip install -r requirements.txt

# 4. Uruchom aplikację
streamlit run app.py

# Wprowadzanie danych
Należy w odpowiednich polach podać następujące dane:
- datę
- szerokość i długość geograficzną obserwatora
- wysokość położenia obserwatora
- maskę odcięcia

Jest możliwość wybrania pliku z folderu brdc lub pobrania do katalogu. Przycisk 'Oblicz' wykona wizualizacje.
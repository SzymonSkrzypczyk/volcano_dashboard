# Dashboard wulkanów z holocenu 

## Opis
Interaktywny dashboard analizujący dane o erupcjach wulkanów na przestrzeni dziejów, z uwzględnieniem indeksu eksplozywności VEI, lokalizacji geograficznej oraz kontekstu tektonicznego.

## Funkcje

- 📍 **Mapa lokalizacji wulkanów** (warstwa punktowa)
- 🔥 **Mapa cieplna intensywności erupcji**
- 📈 **Wykresy liczby erupcji w czasie**
- 🌋 **Rozkład erupcji według VEI oraz kategorii**
- 🏳️ **Porównanie erupcji między krajami i kontynentami**
- 🗺️ **Choropleta gęstości erupcji na świecie**
- 🌍 **Warstwy tektoniczne:** granice płyt, ryfty, orogeny
- 🔍 **Filtrowanie danych według roku i VEI**

---

## Jak odpalić
1. **Klonowanie repo(póki co nie jest publiczne ;))**:
```bash
git clone git@github.com:SzymonSkrzypczyk/volcano_dashboard.git
cd volcano-dashboard
```
2. **Tworzenie środowiska wirtualnego**:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate.bat  # Windows
```
3. **Instalacja zależności**:
```bash
pip install -r requirements.txt
```
4. **Uruchomienie aplikacji**:
```bash
streamlit run main.py
```

Voila! Dashboard powinien być dostępny pod adresem `http://localhost:8501`.


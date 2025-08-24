# PriceComPro

Веб-комплекс на Python для імпорту та уніфікації прайс-листів постачальників.

## Швидкий старт

### Вимоги
- Python 3.12
- Windows/Unix

### Встановлення
```bash
python -m venv .venv
# Windows
.\.venv\Scripts\activate
# Unix/macOS
source .venv/bin/activate

pip install -r requirements.txt
python db_reset.py
python seed_minimal.py
uvicorn app.main:app --reload

# Price Complex Processor (PriceComPro)

Мінімальна база (FastAPI + SQLAlchemy + Alembic-ready).

## Запуск локально

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload

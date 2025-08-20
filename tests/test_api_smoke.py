from fastapi.testclient import TestClient

from app.db.session import engine
from app.main import app
from app.models import category, manufacturer, price_list, supplier, supplier_product  # noqa: F401
from app.models.base import Base


def setup_module(module):
    # створюємо таблиці для тестової БД (CI задає DATABASE_URL=sqlite:///./test.db)
    Base.metadata.create_all(bind=engine)


def teardown_module(module):
    # після тестів прибираємо таблиці
    Base.metadata.drop_all(bind=engine)


def test_suppliers_list_empty():
    client = TestClient(app)
    r = client.get("/api/suppliers")
    assert r.status_code == 200
    assert r.json() == []


def test_create_supplier():
    client = TestClient(app)
    payload = {"name": "Test Supplier", "code": "TEST", "active": True}
    r = client.post("/api/suppliers", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["id"] > 0
    assert data["name"] == "Test Supplier"

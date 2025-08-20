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

def test_update_and_delete_supplier():
    client = TestClient(app)

    # create
    r = client.post("/api/suppliers", json={"name": "Tmp Sup", "code": "TMP", "active": True})
    assert r.status_code == 200
    sup = r.json()
    sid = sup["id"]

    # update
    r = client.put(f"/api/suppliers/{sid}", json={"name": "Tmp Sup 2", "code": "TMP2", "active": False})
    assert r.status_code == 200
    up = r.json()
    assert up["id"] == sid
    assert up["name"] == "Tmp Sup 2"
    assert up["active"] is False

    # delete
    r = client.delete(f"/api/suppliers/{sid}")
    assert r.status_code == 200
    assert r.json() == {"ok": True}


def test_price_lists_crud():
    client = TestClient(app)

    # ensure supplier exists
    r = client.post("/api/suppliers", json={"name": "ACME", "code": "ACME", "active": True})
    assert r.status_code == 200
    supplier_id = r.json()["id"]

    # create price list
    payload = {
        "supplier_id": supplier_id,
        "name": "ACME local CSV",
        "source_type": "local",
        "source_config": {"delimiter": ";"},
        "format": "csv",
        "mapping": {}  # mapping не обов'язковий для самого створення
    }
    r = client.post("/api/price-lists", json=payload)
    assert r.status_code == 200
    pl = r.json()
    pl_id = pl["id"]
    assert pl["supplier_id"] == supplier_id

    # list (filtered)
    r = client.get(f"/api/price-lists?supplier_id={supplier_id}")
    assert r.status_code == 200
    lst = r.json()
    assert any(x["id"] == pl_id for x in lst)

    # update
    r = client.put(f"/api/price-lists/{pl_id}", json={
        "name": "ACME local CSV (updated)",
        "active": True
    })
    assert r.status_code == 200
    pl_up = r.json()
    assert pl_up["id"] == pl_id
    assert pl_up["name"] == "ACME local CSV (updated)"

    # delete
    r = client.delete(f"/api/price-lists/{pl_id}")
    assert r.status_code == 200
    assert r.json() == {"ok": True}

def test_import_xlsx_basic(tmp_path):
    from openpyxl import Workbook
    client = TestClient(app)

    # supplier
    r = client.post("/api/suppliers", json={"name": "XLSX Sup", "code": "XLSX", "active": True})
    assert r.status_code == 200
    supplier_id = r.json()["id"]

    # price list with mapping (no header, by letters)
    payload = {
        "supplier_id": supplier_id,
        "name": "XLSX PL",
        "source_type": "local",
        "source_config": {"sheet": {"by":"index","value":1}, "header": False, "start_row": 1},
        "format": "xlsx",
        "mapping": {
            "supplier_sku": {"by":"col_letter","value":"A"},
            "name": {"by":"col_letter","value":"B"},
            "price_raw": {"by":"col_letter","value":"C"},
            "currency_raw": {"by":"col_letter","value":"D"},
            "qty_raw": {"by":"col_letter","value":"E"},
        },
        "active": True
    }
    r = client.post("/api/price-lists", json=payload)
    assert r.status_code == 200
    pl_id = r.json()["id"]

    # build workbook in-memory
    wb = Workbook()
    ws = wb.active
    ws.title = "Sheet1"
    ws.append(["SUP-001", "Prod 1", 9.99, "PLN", 5])
    ws.append(["SUP-002", "Prod 2", "12,50", "PLN", 7])
    p = tmp_path / "test.xlsx"
    wb.save(p)

    with p.open("rb") as fh:
        files = {"file": ("test.xlsx", fh.read(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    r = client.post(f"/api/import/{pl_id}", files=files)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["stats"]["inserted"] >= 2

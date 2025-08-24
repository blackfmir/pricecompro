from app.db.session import SessionLocal
from app.crud import supplier as supplier_crud
from app.schemas.supplier import SupplierCreate
from app.crud import currency as currency_crud
from app.schemas.currency import CurrencyCreate

if __name__ == "__main__":
    db = SessionLocal()
    try:
        # Постачальник демо
        if not supplier_crud.list_(db):
            supplier_crud.create(db, SupplierCreate(name="Demo Supplier", code="DEMO", active=True))
            print("Seeded: Demo Supplier")
        else:
            print("Suppliers already exist. Skip seeding.")

        # Валюта базова (PLN) як приклад
        if not currency_crud.list_(db):
            currency_crud.create(db, CurrencyCreate(
                code="PLN",
                name="Польський злотий",
                rate_to_base=1.0,
                manual_override=True,
                active=True,
                symbol_left="",
                symbol_right="zł",
                decimals=2,
            ))
            print("Seeded: Currency PLN")
        else:
            print("Currencies already exist. Skip seeding.")
    finally:
        db.close()

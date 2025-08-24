from urllib.parse import quote
from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.crud import currency as crud
from app.schemas.currency import CurrencyCreate, CurrencyUpdate

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/ui/currencies")
def ui_currencies(request: Request, db: Session = Depends(get_db)):
    items = crud.list_(db)
    toast_message = request.query_params.get("msg")
    return templates.TemplateResponse("currencies.html", {"request": request, "items": items, "toast_message": toast_message})


@router.get("/ui/currencies/new")
def ui_currency_new(request: Request):
    return templates.TemplateResponse("currency_form.html", {"request": request, "item": None})


@router.post("/ui/currencies/new")
def ui_currency_create(
    code: str = Form(...),
    name: str = Form(...),
    rate_to_base: float = Form(1.0),
    manual_override: bool = Form(False),
    active: bool = Form(False),
    symbol_left: str = Form(""),
    symbol_right: str = Form(""),
    decimals: int = Form(2),
    db: Session = Depends(get_db),
):
    crud.create(
        db,
        CurrencyCreate(
            code=code, name=name, rate_to_base=rate_to_base,
            manual_override=manual_override, active=active,
            symbol_left=symbol_left, symbol_right=symbol_right, decimals=decimals
        ),
    )
    return RedirectResponse(url="/ui/currencies?msg=" + quote("Створено валюту"), status_code=303)


@router.get("/ui/currencies/{currency_id}/edit")
def ui_currency_edit(currency_id: int, request: Request, db: Session = Depends(get_db)):
    item = crud.get(db, currency_id)
    if not item:
        return RedirectResponse(url="/ui/currencies?msg=" + quote("Валюту не знайдено"), status_code=303)
    return templates.TemplateResponse("currency_form.html", {"request": request, "item": item})


@router.post("/ui/currencies/{currency_id}/edit")
def ui_currency_update(
    currency_id: int,
    code: str = Form(...),
    name: str = Form(...),
    rate_to_base: float = Form(1.0),
    manual_override: bool = Form(False),
    active: bool = Form(False),
    symbol_left: str = Form(""),
    symbol_right: str = Form(""),
    decimals: int = Form(2),
    db: Session = Depends(get_db),
):
    crud.update(
        db,
        currency_id,
        CurrencyUpdate(
            code=code, name=name, rate_to_base=rate_to_base,
            manual_override=manual_override, active=active,
            symbol_left=symbol_left, symbol_right=symbol_right, decimals=decimals
        ),
    )
    return RedirectResponse(url="/ui/currencies?msg=" + quote("Зміни збережено"), status_code=303)


@router.post("/ui/currencies/{currency_id}/delete")
def ui_currency_delete(currency_id: int, db: Session = Depends(get_db)):
    crud.delete(db, currency_id)
    return RedirectResponse(url="/ui/currencies?msg=" + quote("Валюту видалено"), status_code=303)


@router.post("/ui/currencies/{currency_id}/set-base")
def ui_currency_set_base(currency_id: int, db: Session = Depends(get_db)):
    obj = crud.set_base(db, currency_id)
    msg = ("Обрано нову основну валюту: "
           f"{obj.code}. Курси не змінено.") if obj else "Валюту не знайдено"
    return RedirectResponse(url="/ui/currencies?msg=" + quote(msg), status_code=303)


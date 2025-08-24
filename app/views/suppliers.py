# app/views/suppliers.py
from urllib.parse import quote
from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.crud import supplier as crud
from app.schemas.supplier import SupplierCreate, SupplierUpdate

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/ui/suppliers")
def ui_suppliers(request: Request, db: Session = Depends(get_db)):
    items = crud.list_(db)
    toast_message = request.query_params.get("msg")
    return templates.TemplateResponse(
        "suppliers.html",
        {"request": request, "items": items, "toast_message": toast_message},
    )


@router.get("/ui/suppliers/new")
def ui_supplier_new(request: Request):
    return templates.TemplateResponse("supplier_form.html", {"request": request, "item": None})


@router.post("/ui/suppliers/new")
def ui_supplier_create(
    name: str = Form(...),
    code: str = Form(...),
    active: bool = Form(False),  # checkbox → False, якщо знятий
    db: Session = Depends(get_db),
):
    crud.create(db, SupplierCreate(name=name, code=code, active=active))
    return RedirectResponse(url=f"/ui/suppliers?msg={quote('Створено постачальника')}", status_code=303)


@router.get("/ui/suppliers/{supplier_id}/edit")
def ui_supplier_edit(supplier_id: int, request: Request, db: Session = Depends(get_db)):
    item = crud.get(db, supplier_id)
    if not item:
        return RedirectResponse(url=f"/ui/suppliers?msg={quote('Постачальника не знайдено')}", status_code=303)
    return templates.TemplateResponse("supplier_form.html", {"request": request, "item": item})


@router.post("/ui/suppliers/{supplier_id}/edit")
def ui_supplier_update(
    supplier_id: int,
    name: str = Form(...),
    code: str = Form(...),
    active: bool = Form(False),
    db: Session = Depends(get_db),
):
    crud.update(db, supplier_id, SupplierUpdate(name=name, code=code, active=active))
    return RedirectResponse(url=f"/ui/suppliers?msg={quote('Зміни збережено')}", status_code=303)


@router.post("/ui/suppliers/{supplier_id}/delete")
def ui_supplier_delete(supplier_id: int, db: Session = Depends(get_db)):
    crud.delete(db, supplier_id)
    return RedirectResponse(url=f"/ui/suppliers?msg={quote('Постачальника видалено')}", status_code=303)

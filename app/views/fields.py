from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.crud import custom_field as crud
from app.schemas.custom_field import CustomFieldCreate
import re

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

_slug_re = re.compile(r"[^a-z0-9_]+")

def _slugify(s: str) -> str:
    s = s.strip().lower().replace(" ", "_")
    s = _slug_re.sub("", s)
    return s or "field"

@router.get("/ui/fields")
def ui_fields(request: Request, db: Session = Depends(get_db)):
    items = crud.list_(db, active_only=False)
    return templates.TemplateResponse("fields.html", {"request": request, "items": items})

@router.post("/ui/fields/new")
def ui_fields_new(
    request: Request,
    name: str = Form(...),
    code: str = Form(""),
    data_type: str = Form("text"),
    active: bool = Form(True),
    db: Session = Depends(get_db),
):
    code = code.strip() or _slugify(name)
    if crud.get_by_code(db, code):
        # простий випадок: додамо суфікс
        i = 1
        base = code
        while crud.get_by_code(db, code):
            i += 1
            code = f"{base}_{i}"
    obj = crud.create(db, CustomFieldCreate(name=name, code=code, data_type=data_type, active=active))
    return RedirectResponse(url="/ui/fields", status_code=303)

@router.post("/ui/fields/{cf_id}/delete")
def ui_fields_delete(cf_id: int, db: Session = Depends(get_db)):
    crud.delete(db, cf_id)
    return RedirectResponse(url="/ui/fields", status_code=303)

# AJAX створення з модалки мапінгу:
@router.post("/ui/fields/create-ajax")
def ui_fields_create_ajax(
    name: str = Form(...),
    code: str = Form(""),
    data_type: str = Form("text"),
    db: Session = Depends(get_db),
):
    code = code.strip() or _slugify(name)
    if crud.get_by_code(db, code):
        return JSONResponse({"ok": False, "message": "Поле з таким кодом уже існує"}, status_code=400)
    obj = crud.create(db, CustomFieldCreate(name=name, code=code, data_type=data_type, active=True))
    return JSONResponse({"ok": True, "id": obj.id, "name": obj.name, "code": obj.code, "data_type": obj.data_type})

from fastapi import APIRouter, Depends, Request, Query
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.crud import import_batch as crud
from app.crud import supplier as supplier_crud
from app.crud import pricelists as pricelist_crud

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/ui/import-batches")
def ui_import_batches(
    request: Request,
    supplier_id: int | None = Query(default=None),
    pricelist_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
):
    items = crud.list_(db, supplier_id=supplier_id, pricelist_id=pricelist_id, limit=300)
    suppliers = {s.id: s.name for s in supplier_crud.list_(db)}
    pricelists = {p.id: p.name for p in pricelist_crud.list_(db)}
    return templates.TemplateResponse("import_batches.html", {
        "request": request,
        "items": items,
        "suppliers": suppliers,
        "pricelists": pricelists,
        "supplier_id": supplier_id,
        "pricelist_id": pricelist_id,
    })

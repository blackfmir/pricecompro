from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import json
import json as _json

from app.api.deps import get_db
from app.crud import scraper as crud
from app.crud import supplier as supplier_crud
from app.crud import pricelists as pricelist_crud
from app.services.scraper import preview_block, run_scraper_to_csv, stream_scraper, _sse

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/ui/scrapers")
def ui_scrapers(request: Request, db: Session = Depends(get_db)):
    items = crud.list_(db)
    suppliers = {s.id: s.name for s in supplier_crud.list_(db)}
    pricelists = {p.id: p.name for p in pricelist_crud.list_(db)}
    return templates.TemplateResponse("scrapers.html", {"request": request, "items": items, "suppliers": suppliers, "pricelists": pricelists})

@router.get("/ui/scrapers/new")
def ui_scraper_new(request: Request, db: Session = Depends(get_db)):
    suppliers = supplier_crud.list_(db)
    pricelists = pricelist_crud.list_(db)
    return templates.TemplateResponse("scraper_form.html", {"request": request, "item": None, "suppliers": suppliers, "pricelists": pricelists})

@router.post("/ui/scrapers/new")
def ui_scraper_new_post(
    request: Request,
    supplier_id: int = Form(...),
    name: str = Form(...),
    start_urls: str = Form(""),
    user_agent: str = Form(""),
    delay: float = Form(0.0),
    pricelist_id: int | None = Form(None),
    db: Session = Depends(get_db),
):
    settings = {"user_agent": user_agent, "delay": delay}
    start = [u.strip() for u in start_urls.splitlines() if u.strip()]
    obj = crud.create(db, data=crud.ScraperCreate(  # type: ignore[attr-defined]
        supplier_id=supplier_id, name=name, start_urls=start, settings=settings, rules={}, active=True, pricelist_id=pricelist_id
    ))
    return RedirectResponse(f"/ui/scrapers/{obj.id}/edit", status_code=303)

@router.get("/ui/scrapers/{sid}/edit")
def ui_scraper_edit(sid: int, request: Request, db: Session = Depends(get_db)):
    obj = crud.get(db, sid)
    if not obj:
        return RedirectResponse("/ui/scrapers", status_code=303)
    suppliers = supplier_crud.list_(db)
    pricelists = pricelist_crud.list_(db)
    start_urls = json.loads(obj.start_urls_json or "[]")
    start_urls_text = "\n".join(start_urls)
    settings = json.loads(obj.settings_json or "{}")
    rules = json.loads(obj.rules_json or "{}")
    return templates.TemplateResponse("scraper_form.html", {
        "request": request,
        "item": obj,
        "suppliers": suppliers,
        "pricelists": pricelists,
        "start_urls": start_urls,
        "start_urls_text": start_urls_text,
        "settings": settings,
        "rules": rules
    })

@router.post("/ui/scrapers/{sid}/save-rules")
def ui_scraper_save_rules(
    sid: int,
    settings_json: str | None = Form(None),
    rules_json: str | None = Form(None),
    start_urls_json: str | None = Form(None),
    db: Session = Depends(get_db),
):
    obj = crud.get(db, sid)
    if not obj:
        raise HTTPException(status_code=404, detail="Scraper not found")

    # Безпечні дефолти, якщо з фронту щось не прийшло
    settings_json = settings_json or "{}"
    rules_json = rules_json or '{"categories":{},"listing":{},"product":{"fields":[]}}'
    start_urls_json = start_urls_json or "[]"

    # Валідація: має бути хоча б 1 стартовий URL
    try:
        start_urls = json.loads(start_urls_json)
    except Exception:
        start_urls = []

    if not isinstance(start_urls, list) or len(start_urls) == 0:
        # Мʼякий UX: редиректимо назад із повідомленням
        return RedirectResponse(
            url=f"/ui/scrapers/{sid}/edit?err=Вкажіть хоча б один стартовий URL у вкладці 'Стартові URL'.",
            status_code=303
        )

    # Збереження
    obj.settings_json = settings_json
    obj.rules_json = rules_json
    obj.start_urls_json = start_urls_json
    db.commit()

    return RedirectResponse(url=f"/ui/scrapers/{sid}/edit?msg=Збережено", status_code=303)

@router.post("/ui/scrapers/{sid}/test")
def ui_scraper_test(
    sid: int,
    url: str = Form(""),
    block: str = Form(...),
    db: Session = Depends(get_db),
):
    obj = crud.get(db, sid)
    if not obj:
        return JSONResponse({"ok": False, "message": "Scraper not found"}, status_code=404)

    import json as _json
    settings = _json.loads(obj.settings_json or "{}")
    rules = _json.loads(obj.rules_json or "{}")

    # якщо користувач не передав url — беремо збережений
    if not url:
        test_urls = (settings or {}).get("test_urls") or {}
        url = test_urls.get(block) or ""

    if not url:
        return JSONResponse({"ok": False, "message": "Вкажіть URL або збережіть його у налаштуваннях (settings.test_urls)."}, status_code=400)

    rule_block = (rules.get(block) or {}) | {"kind": block}
    ua = settings.get("user_agent")
    try:
        delay = float(settings.get("delay") or 0)
    except Exception:
        delay = 0.0

    from app.services.scraper import preview_block
    data = preview_block(url, rules=rule_block, ua=ua, delay=delay)
    return JSONResponse({"ok": True, "data": data})


@router.post("/ui/scrapers/{sid}/run")
def ui_scraper_run(sid: int, db: Session = Depends(get_db)):
    obj = crud.get(db, sid)
    if not obj:
        return JSONResponse({"ok": False, "message": "Scraper not found"}, status_code=404)
    settings = json.loads(obj.settings_json or "{}")
    rules = json.loads(obj.rules_json or "{}")
    start_urls = json.loads(obj.start_urls_json or "[]")
    start_urls_text = "\n".join(start_urls)
    sc = {"settings": settings, "rules": rules, "start_urls": start_urls}
    rel, url = run_scraper_to_csv(scraper=sc, pricelist_id=obj.pricelist_id, db_settings={})
    # якщо є Pricelist — оновимо last_path і формат=csv
    if obj.pricelist_id:
        from app.crud import pricelists as pl_crud
        pl = pl_crud.get(db, obj.pricelist_id)
        if pl:
            import json as _json
            cfg = {}
            try:
                cfg = _json.loads(pl.source_config) if pl.source_config else {}
            except Exception:
                cfg = {}
            cfg["last_path"] = rel
            pl.format = "csv"
            pl.source_type = "parser"  # якщо в моделі enum — встанови відповідне значення/рядок
            pl.source_config = _json.dumps(cfg, ensure_ascii=False)
            db.commit()
    return JSONResponse({"ok": True, "file_url": url, "rel_path": rel})

@router.get("/ui/scrapers/{sid}/run-stream")
def ui_scraper_run_stream(sid: int, db: Session = Depends(get_db)):
    obj = crud.get(db, sid)
    if not obj:
        return JSONResponse({"ok": False, "message": "Scraper not found"}, status_code=404)

    # Зібрати конфіг з БД (безпечно розпарсити JSON)
    try:
        scraper = {
            "settings": _json.loads(obj.settings_json or "{}"),
            "rules": _json.loads(obj.rules_json or "{}"),
            "start_urls": _json.loads(obj.start_urls_json or "[]"),
        }
    except Exception:
        scraper = {"settings": {}, "rules": {}, "start_urls": []}

    def gen():
        # Стартовий «hello», щоб точно побачити підключення
        yield _sse({"type": "log", "message": "Підключено. Готуємо запуск..."}).encode("utf-8")
        # Далі — реальний потік подій від сервісу
        yield from stream_scraper(
            scraper=scraper,
            pricelist_id=(obj.pricelist_id or None),
            db_settings={}
        )

    # Важливі заголовки для SSE: no-cache і keep-alive
    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        # Якщо за проксі — інколи допомагає вимкнути буферизацію (NGINX):
        # "X-Accel-Buffering": "no",
    }
    return StreamingResponse(gen(), media_type="text/event-stream", headers=headers)
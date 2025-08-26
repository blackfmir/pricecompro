import json
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.scraper import scrapers as S
from app.schemas.scraper import ScraperCreate, ScraperUpdate


def list_(db: Session):
    stmt = select(S).order_by(S.id.desc())
    return list(db.scalars(stmt).all())

def get(db: Session, scraper_id: int) -> S | None:
    return db.get(S, scraper_id)

def create(db: Session, data: ScraperCreate) -> S:
    obj = S(
        supplier_id=data.supplier_id,
        name=data.name,
        start_urls=json.dumps(data.start_urls, ensure_ascii=False),
        settings_json=json.dumps(data.settings or {}, ensure_ascii=False),
        rules_json=json.dumps(data.rules or {}, ensure_ascii=False),
        active=bool(data.active),
        pricelist_id=data.pricelist_id,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def update(db: Session, scraper_id: int, data: ScraperUpdate) -> S | None:
    obj = get(db, scraper_id)
    if not obj:
        return None
    payload = data.model_dump(exclude_unset=True)
    if "start_urls" in payload:
        payload["start_urls"] = json.dumps(payload["start_urls"] or [], ensure_ascii=False)
    if "settings" in payload:
        payload["settings_json"] = json.dumps(payload["settings"] or {}, ensure_ascii=False)
        payload.pop("settings", None)
    if "rules" in payload:
        payload["rules_json"] = json.dumps(payload["rules"] or {}, ensure_ascii=False)
        payload.pop("rules", None)
    for k, v in payload.items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj

def delete(db: Session, scraper_id: int) -> bool:
    obj = get(db, scraper_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True

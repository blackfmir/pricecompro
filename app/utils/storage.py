from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from app.core.config import settings


def _ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)

_filename_safe = re.compile(r"[^A-Za-z0-9._-]+")

def sanitize_filename(name: str) -> str:
    name = name.strip().replace("\\", "/").split("/")[-1]
    name = _filename_safe.sub("-", name)
    return name or "file.bin"

def _make_url(path: Path) -> str:
    rel = path.relative_to(settings.STORAGE_DIR)
    return f"/storage/{rel.as_posix()}"

def save_price_upload(pl_id: int, filename: str, content: bytes) -> tuple[Path, str]:
    root = Path(settings.STORAGE_DIR) / "pricelists" / str(pl_id) / "uploads"
    _ensure_dir(root)
    safe = sanitize_filename(filename or "source.bin")
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = root / f"{ts}-{safe}"
    path.write_bytes(content)
    return path, _make_url(path)

def save_price_download(pl_id: int, filename: str, content: bytes) -> tuple[Path, str]:
    root = Path(settings.STORAGE_DIR) / "pricelists" / str(pl_id) / "downloads"
    _ensure_dir(root)
    safe = sanitize_filename(filename or "source.bin")
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = root / f"{ts}-{safe}"
    path.write_bytes(content)
    return path, _make_url(path)

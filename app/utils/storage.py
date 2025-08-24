from __future__ import annotations
from pathlib import Path
from typing import Tuple
import re
from app.core.config import settings

STORAGE_ROOT = Path(settings.STORAGE_DIR).resolve()
STORAGE_ROOT.mkdir(parents=True, exist_ok=True)


def storage_join(*parts: str | Path) -> Path:
    """Безпечно поєднує шляхи всередині STORAGE_DIR (без виходу назовні)."""
    path = STORAGE_ROOT.joinpath(*parts).resolve()
    if not str(path).startswith(str(STORAGE_ROOT)):
        raise ValueError("Path escapes storage root")
    return path


def to_rel(path: str | Path) -> str:
    """Відносний шлях відносно STORAGE_DIR у форматі POSIX (для URL)."""
    p = Path(path).resolve()
    rel = p.relative_to(STORAGE_ROOT)
    return rel.as_posix()


def public_url(rel_path: str) -> str:
    base = settings.STORAGE_PUBLIC_BASE.rstrip("/")
    return f"{base}/{rel_path.lstrip('/')}"


_filename_re = re.compile(r"[^A-Za-z0-9._-]+")


def _safe_filename(name: str) -> str:
    name = name.strip().replace(" ", "_")
    name = _filename_re.sub("_", name)
    # не дозволяємо приховані файли типу ".env"
    return name.lstrip(".") or "file"


def save_upload(rel_dir: str, filename: str, content: bytes) -> Tuple[str, str]:
    """Зберігає файл у storage/<rel_dir>/<safe_filename>. Повертає (rel_path, url)."""
    safe = _safe_filename(filename)
    target_dir = storage_join(rel_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    target = target_dir / safe
    # якщо існує — додамо індекс
    if target.exists():
        stem, suf = target.stem, target.suffix
        i = 1
        while True:
            cand = target_dir / f"{stem}_{i}{suf}"
            if not cand.exists():
                target = cand
                break
            i += 1

    target.write_bytes(content)
    rel = to_rel(target)
    return rel, public_url(rel)

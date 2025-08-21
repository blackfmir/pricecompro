from __future__ import annotations

import re
import unicodedata

_UA_MAP = {
    "є": "ie", "ї": "i", "і": "i", "ґ": "g",
    "й": "i", "ю": "iu", "я": "ia", "ж": "zh",
    "ч": "ch", "ш": "sh", "щ": "shch", "х": "kh",
    "ц": "ts", "ь": "", "’": "", "'": "", "ъ": "",
}
_UA_MAP.update({k.upper(): v.capitalize() for k, v in list(_UA_MAP.items())})

_PL_MAP = {
    "ą": "a", "ć": "c", "ę": "e", "ł": "l",
    "ń": "n", "ó": "o", "ś": "s", "ź": "z", "ż": "z",
}
_PL_MAP.update({k.upper(): v.upper() for k, v in list(_PL_MAP.items())})

def _basic_translit(s: str) -> str:
    # мапінг UA/PL
    out = []
    for ch in s:
        if ch in _UA_MAP:
            out.append(_UA_MAP[ch])
        elif ch in _PL_MAP:
            out.append(_PL_MAP[ch])
        else:
            out.append(ch)
    s = "".join(out)
    # NFKD + ASCII fallback
    s = unicodedata.normalize("NFKD", s)
    s = s.encode("ascii", "ignore").decode("ascii")
    return s

_slug_re1 = re.compile(r"[^a-zA-Z0-9]+")
_slug_re2 = re.compile(r"-{2,}")

def slugify_code(name: str) -> str:
    s = _basic_translit(name.strip())
    s = _slug_re1.sub("-", s).strip("-").lower()
    s = _slug_re2.sub("-", s)
    return s or "supplier"

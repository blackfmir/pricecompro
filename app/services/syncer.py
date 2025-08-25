from typing import Any, Dict
import json

def apply_rules_to_product(
    sp: dict,              # рядок supplier_products як dict (включно з extra_json)
    prod: dict,            # поточний продукт (dict: поля + extra_json)
    rules: list[dict],
    is_new: bool,
) -> dict:
    """Повертає dict з оновленими полями product (+extra_json)."""
    extra = json.loads(prod.get("extra_json") or "{}")

    def get_source_value(rule: dict) -> Any:
        src = rule["source"]
        if src.startswith("extra:"):
            key = src.split(":", 1)[1]
            sp_extra = json.loads(sp.get("extra_json") or "{}")
            return sp_extra.get(key)
        return sp.get(src)

    def transform_value(val: Any, rule: dict) -> Any:
        tf = rule.get("transform") or {}
        t = tf.get("type")
        if not t:
            return val
        if t == "template":
            # доступні як поля SP, так і SP.extra
            sp_extra = json.loads(sp.get("extra_json") or "{}")
            ctx = {**sp, **sp_extra}
            templ = tf.get("value", "")
            try:
                return templ.format(**ctx)
            except Exception:
                return templ
        if t == "concat":
            fields = tf.get("fields") or []
            sep = tf.get("sep", " ")
            parts = []
            sp_extra = json.loads(sp.get("extra_json") or "{}")
            for f in fields:
                parts.append(sp_extra.get(f) if f.startswith("extra:") else sp.get(f))
            return sep.join([str(x) for x in parts if x])
        return val

    updated = {}
    for r in rules:
        tgt = r["target_field"]
        mode = r.get("mode", "always")
        current = extra.get(tgt) if tgt not in prod else prod.get(tgt)

        # режим
        if mode == "ignore":
            continue
        if mode == "create_only" and not is_new:
            continue
        if mode == "update_if_empty":
            empty = (current is None) or (isinstance(current, str) and current.strip() == "")
            if not empty:
                continue

        val = transform_value(get_source_value(r), r)

        # куди писати
        if tgt in prod:
            updated[tgt] = val
        else:
            extra[tgt] = val

    if extra:
        updated["extra_json"] = json.dumps(extra, ensure_ascii=False)
    return updated

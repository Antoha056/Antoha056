#!/usr/bin/env python3
"""Разобрать дамп проверки КМ на кассе и структуру кода бытовой химии."""

from __future__ import annotations

import json
import re
from pathlib import Path

REF = Path(__file__).with_name("kassa-km-errors.json")

SERIAL_LEN = 6
DUMP_RE = re.compile(
    r"(?P<km>01\d{14}21\S+?)"
    r'(?:"0\s*)?Ошибок нет'
    r".*?CheckItemLocalResult\s+(?P<local_result>-?\d+)"
    r"\s*CheckItemLocalError\s+(?P<local_error>-?\d+)"
    r"\s*MarkingType2\s+(?P<marking_type>-?\d+)"
    r"\s*KMServerErrorCode\s+(?P<server_error>-?\d+)"
    r"\s*KMServerCheckingStatus\s+(?P<server_status>-?\d+)",
    re.S,
)


def load_ref(path: Path = REF) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _lookup(table: dict, value: int) -> str:
    return table.get(str(value), f"неизвестное значение {value}")


def _normalize_km(km: str) -> str:
    text = km.strip()
    text = text.replace("<GS>", "\x1d").replace("\\x1d", "\x1d").replace("\\u001d", "\x1d")
    return text


def parse_km(km: str, serial_len: int = SERIAL_LEN) -> dict:
    """Разобрать GS1 Data Matrix косметики / бытовой химии."""
    raw = _normalize_km(km)
    result = {
        "km": raw.replace("\x1d", "<GS>"),
        "ok": False,
        "kind": "unknown",
        "gtin": None,
        "serial": None,
        "serialLength": 0,
        "hasGs": False,
        "ai93": None,
        "ai91": None,
        "ai92": None,
        "reasons": [],
    }
    if not raw.startswith("01") or len(raw) < 18 or not raw[2:16].isdigit():
        result["reasons"].append("нет AI 01 и 14-значного GTIN")
        return result
    result["gtin"] = raw[2:16]
    rest = raw[16:]
    if not rest.startswith("21"):
        result["reasons"].append("после GTIN нет AI 21")
        return result
    body = rest[2:]

    gs_at = body.find("\x1d")
    if gs_at >= 0:
        serial, tail = body[:gs_at], body[gs_at + 1 :]
        result["hasGs"] = True
    else:
        serial, tail = body[:serial_len], body[serial_len:]
        result["hasGs"] = False

    result["serial"] = serial
    result["serialLength"] = len(serial)

    if tail.startswith("93") and len(tail) >= 6:
        result["ai93"] = tail[2:6]
        result["kind"] = "short"
    elif tail.startswith("91"):
        crypto = tail[2:]
        gs2 = crypto.find("\x1d")
        if gs2 >= 0:
            result["ai91"] = crypto[:gs2]
            rest92 = crypto[gs2 + 1 :]
        else:
            result["ai91"] = crypto[:4]
            rest92 = crypto[4:]
        if rest92.startswith("92"):
            result["ai92"] = rest92[2:]
        result["kind"] = "full" if result["ai91"] and result["ai92"] else "unknown"
    elif "91" in raw and "92" in raw:
        result["kind"] = "full"
        result["reasons"].append("полный КМ есть, но GS не разобран")
    elif "93" in raw[18:]:
        result["kind"] = "short"

    if result["kind"] == "unknown":
        result["reasons"].append("в тексте ошибки виден короткий фрагмент, не полный КМ")

    if len(serial) != serial_len and result["kind"] != "full":
        result["reasons"].append(f"серийник {len(serial)} символов, для этой группы нужно {serial_len}")

    result["ok"] = result["kind"] in ("short", "full") and (
        bool(result["ai93"]) or bool(result["ai91"] and result["ai92"])
    )
    return result


def diagnose_dump(text: str, actual_kind: str = "full", ref: dict | None = None) -> dict:
    """Разобрать сообщение кассы про отвергнутую маркировку.

    actual_kind — что реально пришло на ККТ. В этом инциденте полный КМ,
    а ошибка по умолчанию подписывает короткий тип.
    """
    data = ref or load_ref()
    match = DUMP_RE.search(text.replace("\n", " "))
    if not match:
        return {"ok": False, "reason": "не похоже на дамп проверки КМ"}

    local_result = int(match["local_result"])
    local_error = int(match["local_error"])
    marking_type = int(match["marking_type"])
    server_error = int(match["server_error"])
    server_status = int(match["server_status"])
    km = parse_km(match["km"], data.get("serialLength", SERIAL_LEN))

    short_types = set(data.get("driverShortTypes", [1, 3]))
    full_types = set(data.get("driverFullTypes", [2, 4]))
    defaulted_to_short = marking_type in short_types
    type_mismatch = defaulted_to_short and actual_kind == "full"
    online_missing = server_error == -1 and server_status == -1
    fn_passed = local_error == 0 and local_result == 1 and marking_type in (
        full_types if actual_kind == "full" else short_types
    )

    if type_mismatch:
        action = "send_full_km_with_full_type"
    elif fn_passed:
        action = "sale_with_km"
    elif local_error == 1:
        action = "rescan_then_hold_or_quarantine"
    else:
        action = "notify_accountant"

    return {
        "action": action,
        "sellAsRemainder": False,
        "closeWithRejectedMarking": False,
        "notifyAccountant": not fn_passed,
        "driverOk": "ошибок нет" in text.lower(),
        "defaultedToShort": defaulted_to_short,
        "actualKind": actual_kind,
        "typeMismatch": type_mismatch,
        "loggedKind": km["kind"],
        "localResult": local_result,
        "localResultText": _lookup(data["checkItemLocalResult"], local_result),
        "localError": local_error,
        "localErrorText": _lookup(data["checkItemLocalError"], local_error),
        "markingType2": marking_type,
        "markingType2Text": _lookup(data["markingType2Driver"], marking_type),
        "kmServerErrorCode": server_error,
        "kmServerCheckingStatus": server_status,
        "onlineCheck": False if online_missing else True,
        "onlineCheckText": data["serverMinusOne"] if online_missing else "онлайн-проверка вызывалась",
        "km": km,
    }


def _check():
    dump = (
        "Ошибка проверки КМ, маркировка будет отвергнута."
        "Необходимо уведомить бухгалтера"
        '0105413048311093215BTLoSntrqS?"0 Ошибок нет'
        "CheckItemLocalResult 0 CheckItemLocalError 1"
        "MarkingType2 3KMServerErrorCode -1 KMServerCheckingStatus -1"
    )
    got = diagnose_dump(dump, actual_kind="full")
    assert got["localError"] == 1, got
    assert got["localResult"] == 0, got
    assert got["markingType2"] == 3, got
    assert got["defaultedToShort"] is True, got
    assert got["actualKind"] == "full", got
    assert got["typeMismatch"] is True, got
    assert got["action"] == "send_full_km_with_full_type", got
    assert got["sellAsRemainder"] is False, got
    assert got["closeWithRejectedMarking"] is False, got
    assert got["km"]["gtin"] == "05413048311093", got
    assert got["onlineCheck"] is False, got

    short = parse_km("0105413048311093215BTLoS\x1d93Ab1/")
    assert short["ok"] is True, short
    assert short["kind"] == "short", short
    assert short["serial"] == "5BTLoS", short
    assert short["ai93"] == "Ab1/", short

    full = parse_km("0105413048311093215BTLoS\x1d91EE06\x1d92" + ("A" * 44))
    assert full["ok"] is True, full
    assert full["kind"] == "full", full
    assert full["ai91"] == "EE06", full
    assert len(full["ai92"]) == 44, full

    logged = parse_km("0105413048311093215BTLoSntrqS?")
    assert logged["kind"] == "unknown", logged
    print("OK 4 cases")


if __name__ == "__main__":
    import sys

    args = [a for a in sys.argv[1:] if a != "--full"]
    if args:
        print(json.dumps(diagnose_dump(" ".join(args), actual_kind="full"), ensure_ascii=False, indent=2))
    else:
        _check()

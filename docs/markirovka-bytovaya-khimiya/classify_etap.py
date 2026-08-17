#!/usr/bin/env python3
"""Определить этап маркировки по паре ТН ВЭД + ОКПД 2."""

from __future__ import annotations

import json
import re
from pathlib import Path

REF = Path(__file__).with_name("etapy-tnved-okpd2.json")


def _digits(code: str) -> str:
    return re.sub(r"\D", "", code or "")


def _norm_okpd(code: str) -> str:
    return re.sub(r"\s+", "", code or "")


def _tn_matches(card: str, rule_code: str, match: str) -> bool:
    card_d, rule_d = _digits(card), _digits(rule_code)
    if not card_d or not rule_d:
        return False
    if match == "exact":
        return card_d == rule_d
    return card_d.startswith(rule_d)


def _okpd_matches(card: str, rule_code: str) -> bool:
    card_n, rule_n = _norm_okpd(card), _norm_okpd(rule_code)
    return bool(card_n) and card_n.startswith(rule_n)


def load_ref(path: Path = REF) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def classify(tn_ved: str, okpd2: str, antimicrobial_hand: bool = False, ref: dict | None = None) -> dict:
    """Вернуть этап и контрольную дату или признак, что товар не маркируется."""
    data = ref or load_ref()
    tn_d = _digits(tn_ved)
    okpd_n = _norm_okpd(okpd2)

    for item in data["exclusions"]:
        if item["type"] == "tnVed" and tn_d == _digits(item["code"]):
            if item["code"] == "3304990000" and not antimicrobial_hand:
                continue
            return {"marked": False, "reason": item["note"], "stage": None, "startDate": None}
        if item["type"] == "okpd2" and okpd_n.startswith(_norm_okpd(item["code"])):
            return {"marked": False, "reason": item["note"], "stage": None, "startDate": None}

    if antimicrobial_hand and (tn_d.startswith("330499") or okpd_n.startswith("20.42.15")):
        return {
            "marked": False,
            "reason": "Антимикробная гигиена рук исключена из этапа 3",
            "stage": None,
            "startDate": None,
        }

    tn_dates, okpd_dates = [], []
    for stage in data["stages"]:
        if any(_tn_matches(tn_ved, row["code"], row["match"]) for row in stage["tnVed"]):
            tn_dates.append((stage["startDate"], stage["id"]))
        if any(_okpd_matches(okpd2, row["code"]) for row in stage["okpd2"]):
            okpd_dates.append((stage["startDate"], stage["id"]))

    if not tn_dates or not okpd_dates:
        return {"marked": False, "reason": "Пара кодов не входит в перечень", "stage": None, "startDate": None}

    start = max(min(tn_dates)[0], min(okpd_dates)[0])
    stage_id = max(s["id"] for s in data["stages"] if s["startDate"] == start)
    return {"marked": True, "reason": None, "stage": stage_id, "startDate": start}


def _check():
    cases = [
        ("3402 50 000 0", "20.41.32", False, True, 1, "2025-05-01"),
        ("3401", "20.42.19", False, True, 1, "2025-05-01"),
        ("3305", "20.42.16", False, True, 2, "2025-07-01"),
        ("3305", "20.42.19", False, True, 2, "2025-07-01"),
        ("3304", "20.42.15", False, True, 3, "2025-10-01"),
        ("3307", "20.42.15", False, True, 3, "2025-10-01"),
        ("3824 00 000 0", "20.41.3", False, False, None, None),
        ("3306 20 000 0", "20.42.18", False, False, None, None),
        ("3307 41 000 0", "20.42.19", False, False, None, None),
        ("3304 99 000 0", "20.42.15", True, False, None, None),
        ("3405 40 000 0", "20.41.44", False, True, 1, "2025-05-01"),
    ]
    for tn, okpd, anti, marked, stage, date in cases:
        got = classify(tn, okpd, anti)
        assert got["marked"] is marked, (tn, okpd, got)
        assert got["stage"] == stage, (tn, okpd, got)
        assert got["startDate"] == date, (tn, okpd, got)
    print(f"OK {len(cases)} cases")


if __name__ == "__main__":
    _check()

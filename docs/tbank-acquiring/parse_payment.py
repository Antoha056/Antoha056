#!/usr/bin/env python3
"""Parse a T-Bank EACQ dump (GetState / notification / 1C tree) and say if money is captured."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

PAID_STATUSES = {"CONFIRMED"}
HOLD_STATUSES = {"AUTHORIZED"}
FAILED_STATUSES = {
    "REJECTED",
    "AUTH_FAIL",
    "CANCELED",
    "CANCELLED",
    "DEADLINE_EXPIRED",
    "REVERSED",
}

SCALAR_KEYS = (
    "Success",
    "ErrorCode",
    "Message",
    "TerminalKey",
    "Status",
    "PaymentId",
    "OrderId",
    "Amount",
)


def _coerce(raw: str):
    quoted = raw.strip()
    if (quoted.startswith('"') and quoted.endswith('"')) or (
        quoted.startswith("'") and quoted.endswith("'")
    ):
        text = quoted[1:-1]
        if text.lower() == "true":
            return True
        if text.lower() == "false":
            return False
        return text
    text = quoted
    if text.lower() == "true":
        return True
    if text.lower() == "false":
        return False
    if re.fullmatch(r"-?\d+", text):
        return int(text)
    return text


def parse_dump(text: str) -> dict:
    """Accept JSON or a flattened Key/Value dump copied from a debugger."""
    stripped = text.strip()
    if stripped.startswith("{"):
        data = json.loads(stripped)
    else:
        data = {}
        for key in SCALAR_KEYS:
            match = re.search(
                rf"(?:^|\n)\s*{key}\s*[:：=]\s*(\"[^\"]*\"|'[^']*'|\S+)",
                text,
                flags=re.IGNORECASE,
            )
            if match:
                data[key] = _coerce(match.group(1))

        params = {}
        for match in re.finditer(
            r'Key\s*[:：=]\s*"([^"]+)"\s*Value\s*[:：=]\s*"([^"]*)"',
            text,
            flags=re.IGNORECASE,
        ):
            params[match.group(1)] = match.group(2)
        if params:
            data["Params"] = params

    amount = data.get("Amount")
    if isinstance(amount, str) and re.fullmatch(r"-?\d+", amount.strip('"')):
        amount = int(amount.strip('"'))
        data["Amount"] = amount
    if isinstance(amount, int):
        data["AmountRubles"] = amount / 100

    params = data.get("Params")
    if isinstance(params, list):
        folded = {}
        for item in params:
            if isinstance(item, dict) and "Key" in item:
                folded[str(item["Key"])] = item.get("Value")
        data["Params"] = folded

    status = str(data.get("Status") or "").upper()
    success = data.get("Success")
    if isinstance(success, str):
        success = success.lower() == "true"
        data["Success"] = success

    if status in PAID_STATUSES:
        data["Paid"] = True
        data["NextAction"] = "none"
    elif status in HOLD_STATUSES:
        data["Paid"] = False
        data["NextAction"] = "confirm_or_cancel"
    elif status in FAILED_STATUSES:
        data["Paid"] = False
        data["NextAction"] = "do_not_ship"
    else:
        data["Paid"] = False
        data["NextAction"] = "wait_or_getstate"

    data["ApiOk"] = bool(success) and str(data.get("ErrorCode", "0")) in {"0", "00", ""}
    return data


def describe(data: dict) -> str:
    status = data.get("Status")
    order_id = data.get("OrderId")
    payment_id = data.get("PaymentId")
    rubles = data.get("AmountRubles")
    amount_text = f"{rubles:.2f} ₽" if isinstance(rubles, (int, float)) else "?"

    if not data.get("ApiOk"):
        return (
            f"Ответ банка с ошибкой: ErrorCode={data.get('ErrorCode')} "
            f"Message={data.get('Message')}"
        )
    if data.get("Paid"):
        return (
            f"Заказ {order_id} оплачен ({amount_text}). "
            f"Status=CONFIRMED, PaymentId={payment_id}."
        )
    if data.get("NextAction") == "confirm_or_cancel":
        return (
            f"Заказ {order_id}: холд {amount_text}, статус AUTHORIZED. "
            f"Деньги не списаны. Confirm или Cancel по PaymentId={payment_id}."
        )
    if data.get("NextAction") == "do_not_ship":
        return (
            f"Заказ {order_id} не оплачен. Status={status}. Отгружать нельзя."
        )
    return f"Заказ {order_id}: промежуточный статус {status}. Проверить GetState."


def main(argv: list[str]) -> int:
    if len(argv) > 1:
        text = Path(argv[1]).read_text(encoding="utf-8")
    else:
        text = sys.stdin.read()
    data = parse_dump(text)
    print(describe(data))
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

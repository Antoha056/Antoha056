#!/usr/bin/env python3
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from parse_payment import describe, parse_dump

DUMP = """
Success:
true
ErrorCode:
"0"
Message:
"OK"
TerminalKey:
"1579864014451"
Status:
"AUTHORIZED"
PaymentId:
"9167107039"
OrderId:
"49332682"

Params:

0:
Key:
"Route"
Value:
"ACQ"

1:
Key:
"Source"
Value:
"cards"
Amount:
90000
"""


class ParsePaymentTest(unittest.TestCase):
    def test_user_dump_is_hold_not_paid(self):
        data = parse_dump(DUMP)
        self.assertTrue(data["Success"])
        self.assertEqual(data["ErrorCode"], "0")
        self.assertEqual(data["Status"], "AUTHORIZED")
        self.assertEqual(data["PaymentId"], "9167107039")
        self.assertEqual(data["OrderId"], "49332682")
        self.assertEqual(data["Amount"], 90000)
        self.assertEqual(data["AmountRubles"], 900.0)
        self.assertEqual(data["Params"]["Route"], "ACQ")
        self.assertEqual(data["Params"]["Source"], "cards")
        self.assertFalse(data["Paid"])
        self.assertEqual(data["NextAction"], "confirm_or_cancel")
        self.assertIn("не списаны", describe(data))

    def test_confirmed_is_paid(self):
        data = parse_dump(
            json.dumps(
                {
                    "Success": True,
                    "ErrorCode": "0",
                    "Status": "CONFIRMED",
                    "PaymentId": "1",
                    "OrderId": "2",
                    "Amount": 15050,
                }
            )
        )
        self.assertTrue(data["Paid"])
        self.assertEqual(data["AmountRubles"], 150.5)
        self.assertEqual(data["NextAction"], "none")

    def test_cli_reads_dump_file(self):
        script = Path(__file__).resolve().parent / "parse_payment.py"
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as handle:
            handle.write(DUMP)
            dump_path = handle.name
        result = subprocess.run(
            [sys.executable, str(script), dump_path],
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn("AUTHORIZED", result.stdout)
        self.assertIn('"Paid": false', result.stdout)


if __name__ == "__main__":
    unittest.main()

"""Health and pricing tests.

Signature: Mourad.Soltani
"""

from __future__ import annotations

import json
import threading
import unittest
import urllib.request
from datetime import date
from http.server import ThreadingHTTPServer

from mileband.engine import QuoteInput, build_quote
from mileband.server import Handler, quote_from_body


class EngineTests(unittest.TestCase):
    def test_local_band_has_no_travel_fee(self) -> None:
        result = build_quote(
            QuoteInput("Northside Detail", "Amina", "full", "sedan", 4),
            today=date(2026, 10, 6),
        )
        self.assertEqual(result.band, "local")
        self.assertEqual(result.travel_fee, 0.0)
        self.assertEqual(result.total, 189.0)
        self.assertEqual(result.deposit_due, 56.7)
        self.assertEqual(result.valid_until, "2026-10-13")
        self.assertIn("Deposit to hold", result.message)

    def test_far_band_after_hours_and_tax(self) -> None:
        result = build_quote(
            QuoteInput(
                "Northside Detail",
                "Jon",
                "wash",
                "truck",
                30,
                after_hours=True,
                tax_percent=8,
                deposit_percent=50,
                deposit_minimum=20,
            ),
            today=date(2026, 1, 1),
        )
        self.assertEqual(result.band, "far")
        self.assertEqual(result.travel_fee, 55.0)
        self.assertGreater(result.after_hours_fee, 0)
        self.assertEqual(result.deposit_due, round(result.total * 0.5, 2))

    def test_deposit_minimum_applies(self) -> None:
        result = build_quote(
            QuoteInput("Shop", "Pat", "wash", "compact", 1, deposit_percent=5, deposit_minimum=25)
        )
        self.assertEqual(result.deposit_due, 25.0)

    def test_rejects_outside_radius(self) -> None:
        with self.assertRaises(ValueError):
            build_quote(QuoteInput("Shop", "Pat", "wash", "compact", 41))

    def test_rejects_unknown_service(self) -> None:
        with self.assertRaises(ValueError):
            build_quote(QuoteInput("Shop", "Pat", "paint", "compact", 2))


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()

    def test_health(self) -> None:
        with urllib.request.urlopen(f"http://127.0.0.1:{self.port}/health") as response:
            body = json.loads(response.read().decode())
        self.assertEqual(response.status, 200)
        self.assertEqual(body["status"], "ok")

    def test_quote_endpoint(self) -> None:
        payload = json.dumps(
            {
                "business_name": "Paw Miles",
                "client_name": "Lea",
                "service": "groom",
                "vehicle_class": "van",
                "miles": 10,
            }
        ).encode()
        request = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/quote",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request) as response:
            body = json.loads(response.read().decode())
        self.assertEqual(body["band"], "near")
        self.assertEqual(body["travel_fee"], 15.0)

    def test_missing_fields(self) -> None:
        with self.assertRaises(ValueError):
            quote_from_body({"service": "wash"})


if __name__ == "__main__":
    unittest.main()

"""Stdlib HTTP service for mile-band quotes.

Signature: Mourad.Soltani
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from mileband.engine import QuoteInput, build_quote


def quote_from_body(body: dict[str, Any]) -> dict[str, Any]:
    required = ("business_name", "client_name", "service", "vehicle_class", "miles")
    missing = [key for key in required if key not in body]
    if missing:
        raise ValueError("missing fields: " + ", ".join(missing))
    payload = QuoteInput(
        business_name=str(body["business_name"]),
        client_name=str(body["client_name"]),
        service=str(body["service"]),
        vehicle_class=str(body["vehicle_class"]),
        miles=float(body["miles"]),
        after_hours=bool(body.get("after_hours", False)),
        deposit_percent=float(body.get("deposit_percent", 30)),
        deposit_minimum=float(body.get("deposit_minimum", 25)),
        no_show_fee=float(body.get("no_show_fee", 40)),
        tax_percent=float(body.get("tax_percent", 0)),
        quote_days_valid=int(body.get("quote_days_valid", 7)),
    )
    return build_quote(payload).to_dict()


class Handler(BaseHTTPRequestHandler):
    def _send(self, status: int, payload: dict[str, Any]) -> None:
        raw = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:  # noqa: N802
        if self.path.split("?", 1)[0] == "/health":
            self._send(200, {"status": "ok", "service": "mileband-quote"})
            return
        self._send(404, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path.split("?", 1)[0] != "/quote":
            self._send(404, {"error": "not found"})
            return
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b""
        try:
            body = json.loads(raw.decode("utf-8") or "{}")
            if not isinstance(body, dict):
                raise ValueError("JSON body must be an object")
            self._send(200, quote_from_body(body))
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            self._send(400, {"error": str(exc)})

    def log_message(self, fmt: str, *args: Any) -> None:
        return


def serve(host: str = "127.0.0.1", port: int = 8765) -> None:
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"mileband-quote listening on http://{host}:{port}")
    server.serve_forever()

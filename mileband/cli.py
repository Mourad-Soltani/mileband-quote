"""CLI for mile-band deposit quotes.

Signature: Mourad.Soltani
"""

from __future__ import annotations

import argparse
import json
import sys

from mileband.engine import QuoteInput, build_quote
from mileband.server import serve


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Mile-band deposit quotes for mobile trades")
    sub = parser.add_subparsers(dest="command", required=True)

    quote = sub.add_parser("quote", help="Print a deposit quote")
    quote.add_argument("--business", required=True)
    quote.add_argument("--client", required=True)
    quote.add_argument("--service", required=True)
    quote.add_argument("--vehicle", required=True)
    quote.add_argument("--miles", type=float, required=True)
    quote.add_argument("--after-hours", action="store_true")
    quote.add_argument("--deposit-percent", type=float, default=30)
    quote.add_argument("--deposit-minimum", type=float, default=25)
    quote.add_argument("--no-show-fee", type=float, default=40)
    quote.add_argument("--tax-percent", type=float, default=0)
    quote.add_argument("--json", action="store_true")

    run = sub.add_parser("serve", help="Run the local quote API")
    run.add_argument("--host", default="127.0.0.1")
    run.add_argument("--port", type=int, default=8765)

    args = parser.parse_args(argv)
    if args.command == "serve":
        serve(args.host, args.port)
        return 0
    try:
        result = build_quote(
            QuoteInput(
                business_name=args.business,
                client_name=args.client,
                service=args.service,
                vehicle_class=args.vehicle,
                miles=args.miles,
                after_hours=args.after_hours,
                deposit_percent=args.deposit_percent,
                deposit_minimum=args.deposit_minimum,
                no_show_fee=args.no_show_fee,
                tax_percent=args.tax_percent,
            )
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(result.message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

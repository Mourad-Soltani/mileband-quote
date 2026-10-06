"""Mile-band deposit quote engine.

Signature: Mourad.Soltani
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, timedelta
from typing import Any


VEHICLE_MULTIPLIERS = {
    "compact": 1.0,
    "sedan": 1.05,
    "suv": 1.2,
    "truck": 1.3,
    "van": 1.35,
}

SERVICE_BASES = {
    "wash": 45.0,
    "interior": 90.0,
    "exterior": 110.0,
    "full": 180.0,
    "ceramic": 320.0,
    "groom": 65.0,
    "lockout": 85.0,
}


@dataclass(frozen=True)
class QuoteInput:
    business_name: str
    client_name: str
    service: str
    vehicle_class: str
    miles: float
    after_hours: bool = False
    deposit_percent: float = 30.0
    deposit_minimum: float = 25.0
    no_show_fee: float = 40.0
    tax_percent: float = 0.0
    quote_days_valid: int = 7


@dataclass(frozen=True)
class QuoteResult:
    business_name: str
    client_name: str
    service: str
    vehicle_class: str
    miles: float
    band: str
    base: float
    vehicle_adjustment: float
    travel_fee: float
    after_hours_fee: float
    subtotal: float
    tax: float
    total: float
    deposit_due: float
    balance_due: float
    no_show_fee: float
    valid_until: str
    message: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def mileage_band(miles: float) -> tuple[str, float]:
    if miles < 0:
        raise ValueError("miles must be zero or positive")
    if miles <= 5:
        return "local", 0.0
    if miles <= 12:
        return "near", 15.0
    if miles <= 25:
        return "mid", 30.0
    if miles <= 40:
        return "far", 55.0
    raise ValueError("outside service radius (40 miles)")


def build_quote(payload: QuoteInput, today: date | None = None) -> QuoteResult:
    service = payload.service.strip().lower()
    vehicle = payload.vehicle_class.strip().lower()
    if service not in SERVICE_BASES:
        raise ValueError(f"unknown service: {payload.service}")
    if vehicle not in VEHICLE_MULTIPLIERS:
        raise ValueError(f"unknown vehicle class: {payload.vehicle_class}")
    if not payload.business_name.strip() or not payload.client_name.strip():
        raise ValueError("business_name and client_name are required")
    if not 0 <= payload.deposit_percent <= 100:
        raise ValueError("deposit_percent must be between 0 and 100")
    if payload.deposit_minimum < 0 or payload.no_show_fee < 0 or payload.tax_percent < 0:
        raise ValueError("fees and tax must be zero or positive")
    if payload.quote_days_valid < 1:
        raise ValueError("quote_days_valid must be at least 1")

    base = SERVICE_BASES[service]
    multiplier = VEHICLE_MULTIPLIERS[vehicle]
    vehicle_adjustment = round(base * (multiplier - 1.0), 2)
    band, travel_fee = mileage_band(payload.miles)
    after_hours_fee = round((base + vehicle_adjustment + travel_fee) * 0.2, 2) if payload.after_hours else 0.0
    subtotal = round(base + vehicle_adjustment + travel_fee + after_hours_fee, 2)
    tax = round(subtotal * (payload.tax_percent / 100.0), 2)
    total = round(subtotal + tax, 2)
    deposit = round(max(payload.deposit_minimum, total * (payload.deposit_percent / 100.0)), 2)
    if deposit > total:
        deposit = total
    balance = round(total - deposit, 2)
    issued = today or date.today()
    valid_until = (issued + timedelta(days=payload.quote_days_valid)).isoformat()
    message = (
        f"{payload.business_name} quote for {payload.client_name}\n"
        f"Service: {service} ({vehicle}, {band} band, {payload.miles:.1f} mi)\n"
        f"Total: ${total:.2f} | Deposit to hold the slot: ${deposit:.2f} | Balance on site: ${balance:.2f}\n"
        f"No-show fee if we are on site and cancelled: ${payload.no_show_fee:.2f}\n"
        f"Quote valid until {valid_until}."
    )
    return QuoteResult(
        business_name=payload.business_name.strip(),
        client_name=payload.client_name.strip(),
        service=service,
        vehicle_class=vehicle,
        miles=float(payload.miles),
        band=band,
        base=base,
        vehicle_adjustment=vehicle_adjustment,
        travel_fee=travel_fee,
        after_hours_fee=after_hours_fee,
        subtotal=subtotal,
        tax=tax,
        total=total,
        deposit_due=deposit,
        balance_due=balance,
        no_show_fee=payload.no_show_fee,
        valid_until=valid_until,
        message=message,
    )

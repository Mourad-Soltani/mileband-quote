# mileband-quote

Signature: Mourad.Soltani

Small local tool that turns a mobile-trade job into a mile-band deposit quote. Built for detailers, mobile groomers, and locksmiths who text a price and a hold amount before they drive.

No accounts. No maps API. The operator enters miles. The engine prices the band, vehicle class, after-hours load, tax, deposit floor, and no-show fee, then prints a client-ready message.

## Run

```bash
python3 -m mileband.cli quote --business "Northside Detail" --client Amina --service full --vehicle sedan --miles 4
python3 -m mileband.cli serve
curl http://127.0.0.1:8765/health
```

## Test

```bash
python3 -m unittest tests.test_health
```

Services: wash, interior, exterior, full, ceramic, groom, lockout.
Vehicle classes: compact, sedan, suv, truck, van.
Bands: local 0-5, near 6-12, mid 13-25, far 26-40. Beyond 40 miles is rejected.

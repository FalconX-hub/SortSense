# ♻️ SortSense
Know exactly which bin every part of a product goes in: scan the barcode, get a verdict per component
(bottle, cap, label…), tuned to your region's rules. Built for **Arbiter Hacks V1 - Theme Track: Rethinking Waste**.

## The waste problem we target
"Wishcycling": people put the wrong item in the recycling bin (or recyclables in general waste), which
contaminates whole batches. Packaging is multi-material (bottle + cap + label) and rules differ by country.

## How we'd measure whether it works
- **Mistake rate when guessing**: Challenge mode asks "where would you put it?" before revealing the answer.
  The app logs guess vs. correct bin, so the share of misplaced items is measured, not claimed.
- **Pilot** (next step): bin-contamination audits (% of non-conforming items in a sample) before/after
  a 4-week rollout in one building; target: -30% contamination.
- **Diverted mass / CO2e** (illustrative factors in `impact.py`, to be replaced by sourced values).

## Run
```bash
python -m venv .venv && .venv\Scripts\activate     # Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
python -m sortsense.app        # http://localhost:5000
pytest
```
Demo barcodes (work offline): `00000001` (bottle+cap+label), `00000002` (jar), `00000003` (crisps bag), `00000004` (carton).
Real products come from Open Food Facts (any EAN-13).

## Deploy
`Procfile` is ready for gunicorn (Render, Railway, Fly…). Set `SORTSENSE_DB=/data/sortsense.db` for persistence.

## Architecture
`rules.py` (editable regional rules + material normalisation) · `off.py` (Open Food Facts + offline demo) ·
`kb.py` (fuzzy item search) · `impact.py` (SQLite metrics) · `app.py` (Flask API) · `templates/index.html` (UI).

## Limits / next steps
Rules are simplified; add more regions via `REGIONS`. Next: photo-based item recognition, municipal rule feeds,
store-side partnerships for film/battery drop-off locations.

## Demo script (2:30)
1. 0:00 Problem (wishcycling) 2. 0:20 Challenge mode on `00000001`: guess, reveal, cap/label surprise
3. 0:60 Switch region FR → US with the crisps bag (rule changes) 4. 1:20 Item search "pizza box", "battery"
5. 1:45 Impact panel: mistake rate 6. 2:05 Architecture + tests + what's next.

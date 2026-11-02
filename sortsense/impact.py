"""Impact tracking (SQLite) and the metric the project is judged on: sorting corrections."""
from __future__ import annotations

import sqlite3
import time

# ILLUSTRATIVE factors (kg CO2e avoided per kg diverted from landfill) and typical grams per item.
# Replace with sourced values (e.g. ADEME / EPA WARM) before publishing numbers.
CO2_PER_KG = {"plastic": 1.0, "metal": 4.0, "glass": 0.3, "paper": 0.8, "carton": 0.7, "organic": 0.5}
GRAMS = {"plastic": 25, "metal": 15, "glass": 250, "paper": 40, "carton": 30, "organic": 150}
DIVERTING_BINS = {"recycle", "glass", "compost"}

SCHEMA = """CREATE TABLE IF NOT EXISTS events(
  id INTEGER PRIMARY KEY, ts REAL, region TEXT, item TEXT, material TEXT,
  correct_bin TEXT, guess_bin TEXT)"""


class Store:
    def __init__(self, path: str = ":memory:"):
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.execute(SCHEMA)

    def log(self, region: str, item: str, material: str, correct_bin: str, guess_bin: str | None):
        self.db.execute("INSERT INTO events(ts,region,item,material,correct_bin,guess_bin) VALUES(?,?,?,?,?,?)",
                        (time.time(), region, item[:120], material, correct_bin, guess_bin))
        self.db.commit()

    def stats(self) -> dict:
        rows = self.db.execute("SELECT material, correct_bin, guess_bin FROM events").fetchall()
        guessed = [r for r in rows if r[2]]
        wrong = [r for r in guessed if r[2] != r[1]]
        co2 = sum(GRAMS.get(m, 0) / 1000 * CO2_PER_KG.get(m, 0) for m, b, _ in rows if b in DIVERTING_BINS)
        by_bin: dict[str, int] = {}
        for _, b, _ in rows:
            by_bin[b] = by_bin.get(b, 0) + 1
        return {
            "items": len(rows),
            "guesses": len(guessed),
            "misplaced_avoided": len(wrong),
            "mistake_rate": round(len(wrong) / len(guessed), 3) if guessed else None,
            "co2_kg": round(co2, 3),
            "by_bin": by_bin,
        }

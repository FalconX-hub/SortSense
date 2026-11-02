import json

from hypothesis import given, strategies as st

from sortsense.app import create_app
from sortsense.off import fetch_product, parse_product
from sortsense.rules import BINS, decide, normalize_material
from sortsense import kb


def test_material_normalisation():
    assert normalize_material("en:pet-1-polyethylene-terephthalate") == "plastic"
    assert normalize_material("en:glass") == "glass"
    assert normalize_material("en:composite-carton") == "carton"
    assert normalize_material("paper") == "paper"  # 'pp' must not match 'paper'
    assert normalize_material("???") == "unknown"


def test_decisions_by_region():
    assert decide("en:plastic", "en:film", "us").bin == "dropoff"
    assert decide("en:plastic", "en:film", "fr").bin == "recycle"
    assert decide("en:glass", "en:jar", "fr").bin == "glass"
    assert decide("en:plastic", "en:cap", "fr").tip.startswith("Screw")


@given(st.text(max_size=50), st.text(max_size=50), st.text(max_size=5))
def test_decide_never_crashes(m, s, r):
    assert decide(m, s, r).bin in BINS


def test_parse_product_and_fallback_tags():
    p = parse_product("123", {"status": 1, "product": {"product_name": "X", "packagings": [
        {"shape": {"id": "en:bottle"}, "material": {"id": "en:glass"}}]}})
    assert p.components[0].material == "en:glass"
    p2 = parse_product("123", {"status": 1, "product": {"packaging_tags": ["en:bottle", "en:plastic"]}})
    assert len(p2.components) == 1
    assert parse_product("123", {"status": 0}) is None


def test_fetch_validates_and_survives_network_errors():
    import pytest
    with pytest.raises(ValueError):
        fetch_product("abc")
    def boom(*a, **k):
        raise OSError("offline")
    assert fetch_product("12345678", opener=boom) is None
    assert fetch_product("00000001").source == "demo"


def test_kb_search():
    assert kb.search("pizza box", "fr")[0]["bin"] == "compost"
    assert kb.search("batery", "us")[0]["name"] == "Battery"
    assert kb.search("", "fr") == []


class FakeResp:
    def __init__(self, data): self.data = data
    def __enter__(self): return self
    def __exit__(self, *a): pass
    def read(self): return json.dumps(self.data).encode()


def test_api_flow():
    payload = {"status": 1, "product": {"product_name": "Cola", "packagings": [
        {"shape": {"id": "en:bottle"}, "material": {"id": "en:pet-1-polyethylene-terephthalate"}}]}}
    app = create_app(opener=lambda req, timeout=0: FakeResp(payload))
    c = app.test_client()
    j = c.get("/api/barcode/3017620422003?region=fr").get_json()
    assert j["components"][0]["bin"] == "recycle"
    assert c.get("/api/barcode/abc").status_code == 400
    assert c.get("/").status_code == 200
    r = c.post("/api/log", json={"item": "Cola", "material": "plastic", "correct_bin": "recycle", "guess_bin": "trash"})
    assert r.status_code == 201
    assert c.post("/api/log", json={"correct_bin": "nope"}).status_code == 400
    s = c.get("/api/stats").get_json()
    assert s["items"] == 1 and s["misplaced_avoided"] == 1 and s["mistake_rate"] == 1.0 and s["co2_kg"] > 0

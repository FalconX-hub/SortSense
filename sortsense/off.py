"""Open Food Facts client: barcode -> packaging components (with offline demo fallback)."""
from __future__ import annotations

import json
import re
import urllib.request
from dataclasses import dataclass, field

API = "https://world.openfoodfacts.org/api/v2/product/{code}.json?fields=product_name,brands,packagings,packaging_tags,image_front_small_url"
UA = "SortSense/1.0 (hackathon project)"
BARCODE_RE = re.compile(r"^\d{8,14}$")


@dataclass
class Component:
    shape: str | None
    material: str | None


@dataclass
class Product:
    barcode: str
    name: str
    brand: str
    image: str | None
    components: list[Component] = field(default_factory=list)
    source: str = "openfoodfacts"


# Demo data (invented barcodes) so the app works offline during a live demo.
DEMO = {
    "00000001": Product("00000001", "Demo: sparkling water", "DemoBrand", None,
                        [Component("bottle", "en:pet-1-polyethylene-terephthalate"),
                         Component("cap", "en:hdpe-2-high-density-polyethylene"),
                         Component("label", "en:paper")], "demo"),
    "00000002": Product("00000002", "Demo: tomato sauce jar", "DemoBrand", None,
                        [Component("jar", "en:glass"), Component("lid", "en:steel")], "demo"),
    "00000003": Product("00000003", "Demo: crisps bag", "DemoBrand", None,
                        [Component("bag", "en:plastic")], "demo"),
    "00000004": Product("00000004", "Demo: juice carton", "DemoBrand", None,
                        [Component("box", "en:composite-carton"), Component("cap", "en:pp-5-polypropylene")], "demo"),
}


def _id(d) -> str | None:
    if isinstance(d, dict):
        return d.get("id")
    return d if isinstance(d, str) else None


def parse_product(code: str, payload: dict) -> Product | None:
    if payload.get("status") != 1 or not isinstance(payload.get("product"), dict):
        return None
    p = payload["product"]
    comps: list[Component] = []
    for pk in p.get("packagings") or []:
        if isinstance(pk, dict):
            comps.append(Component(_id(pk.get("shape")), _id(pk.get("material"))))
    if not comps:  # fallback on flat tags like ["en:bottle", "en:plastic"]
        tags = [t for t in (p.get("packaging_tags") or []) if isinstance(t, str)]
        from .rules import normalize_material, normalize_shape
        mats = [t for t in tags if normalize_material(t) != "unknown"]
        shape = next((t for t in tags if normalize_shape(t) != "unknown"), None)
        comps = [Component(shape, m) for m in mats]
    return Product(code, p.get("product_name") or "Unnamed product", p.get("brands") or "",
                   p.get("image_front_small_url"), comps)


def fetch_product(code: str, opener=urllib.request.urlopen, timeout: float = 4.0) -> Product | None:
    code = (code or "").strip()
    if not BARCODE_RE.match(code):
        raise ValueError("Barcode must be 8 to 14 digits")
    if code in DEMO:
        return DEMO[code]
    req = urllib.request.Request(API.format(code=code), headers={"User-Agent": UA})
    try:
        with opener(req, timeout=timeout) as r:
            return parse_product(code, json.loads(r.read().decode("utf-8")))
    except (OSError, ValueError):
        return None

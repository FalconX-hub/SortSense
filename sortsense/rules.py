"""Sorting rules per region + normalisation of messy packaging data."""
from __future__ import annotations

import re
from dataclasses import dataclass

BINS = {
    "recycle": {"label": "Recycling bin", "emoji": "♻️"},
    "glass": {"label": "Glass container", "emoji": "🫙"},
    "compost": {"label": "Compost / organic bin", "emoji": "🌱"},
    "dropoff": {"label": "Special drop-off point", "emoji": "📍"},
    "trash": {"label": "General waste", "emoji": "🗑️"},
    "unknown": {"label": "Not sure - check local rules", "emoji": "❓"},
}

# region -> material -> (bin, tip). Simplified, editable data (not code).
REGIONS: dict[str, dict] = {
    "fr": {
        "name": "France (yellow-bin rules)",
        "plastic": ("recycle", "All plastic packaging goes in the yellow bin. Empty it, no need to wash."),
        "metal": ("recycle", "Cans, foil and aerosols go in the yellow bin. Empty them."),
        "paper": ("recycle", "Keep it dry and clean."),
        "carton": ("recycle", "Beverage cartons go in the yellow bin. Flatten them."),
        "glass": ("glass", "Remove lids. Only bottles and jars: no drinking glasses, no ceramics."),
        "organic": ("compost", "Compost or organic bin if your town offers it."),
        "wood": ("dropoff", "Take it to the household waste centre."),
    },
    "us": {
        "name": "United States (typical single-stream)",
        "plastic": ("recycle", "Rigid containers only. Empty, rinse, keep the cap on."),
        "film": ("dropoff", "Plastic film jams sorting machines: use a store drop-off."),
        "metal": ("recycle", "Rinse cans. Crumpled foil is accepted when balled up."),
        "paper": ("recycle", "Keep it dry. Greasy paper is not recyclable."),
        "carton": ("recycle", "Empty and flatten. Caps on."),
        "glass": ("recycle", "Rules vary by city: some require a separate glass bin."),
        "organic": ("compost", "Compost if available, otherwise general waste."),
        "wood": ("trash", "Check your local yard-waste rules."),
    },
}
DEFAULT_REGION = "fr"

_MATERIAL_TOKENS = [  # order matters: first match wins
    ("carton", {"carton", "tetra", "brick", "composite"}),
    ("glass", {"glass"}),
    ("metal", {"aluminium", "aluminum", "steel", "tin", "metal", "iron"}),
    ("paper", {"paper", "cardboard", "fibre", "fiber", "corrugated", "paperboard"}),
    ("plastic", {"pet", "pete", "hdpe", "ldpe", "pp", "ps", "pvc", "pe", "plastic",
                 "polyethylene", "polypropylene", "polystyrene", "pet1", "pe2"}),
    ("organic", {"organic", "compost", "peel", "food"}),
    ("wood", {"wood", "cork"}),
]
_SHAPES = {"bottle", "cap", "lid", "closure", "film", "bag", "wrap", "pouch", "tray",
           "box", "can", "jar", "tube", "cup", "label", "sleeve", "pot"}
_CAPS = {"cap", "lid", "closure"}
_FILMS = {"film", "bag", "wrap", "pouch", "sleeve"}


def _tokens(text: str | None) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", (text or "").lower())) - {"en", "fr"}


def normalize_material(raw: str | None) -> str:
    toks = _tokens(raw)
    for name, words in _MATERIAL_TOKENS:
        if toks & words:
            return name
    return "unknown"


def normalize_shape(raw: str | None) -> str:
    toks = _tokens(raw) & _SHAPES
    return sorted(toks)[0] if toks else "unknown"


@dataclass(frozen=True)
class Decision:
    bin: str
    label: str
    emoji: str
    tip: str
    material: str
    shape: str


def decide(material_raw: str | None, shape_raw: str | None = None, region: str = DEFAULT_REGION) -> Decision:
    rules = REGIONS.get(region) or REGIONS[DEFAULT_REGION]
    material = normalize_material(material_raw)
    shape = normalize_shape(shape_raw)
    key = "film" if (material == "plastic" and shape in _FILMS and "film" in rules) else material
    bin_id, tip = rules.get(key, ("unknown", "We could not identify the material. Check local guidelines."))
    if material == "plastic" and shape in _CAPS:
        tip = "Screw the cap back on the empty bottle before recycling."
    b = BINS[bin_id]
    return Decision(bin_id, b["label"], b["emoji"], tip, material, shape)

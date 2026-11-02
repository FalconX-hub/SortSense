"""Everyday-item knowledge base + fuzzy search (for things without a barcode)."""
from __future__ import annotations

import difflib

# name: (aliases, {region or "*": (bin, tip)})
ITEMS: dict[str, tuple[list[str], dict]] = {
    "Plastic water bottle": (["pet bottle", "water bottle"], {"*": ("recycle", "Empty it and screw the cap back on.")}),
    "Glass jar": (["jam jar", "pickle jar"], {"fr": ("glass", "Remove the lid (metal lid goes in the yellow bin)."), "*": ("recycle", "Empty and rinse.")}),
    "Aluminium can": (["soda can", "beer can", "tin can"], {"*": ("recycle", "Empty it. No need to crush.")}),
    "Greasy pizza box": (["pizza box"], {"*": ("compost", "Grease contaminates paper. Compost if allowed, otherwise general waste.")}),
    "Cardboard box": (["carton box", "shipping box"], {"*": ("recycle", "Flatten it and keep it dry.")}),
    "Newspaper": (["magazine", "paper"], {"*": ("recycle", "Keep it dry.")}),
    "Receipt": (["thermal receipt"], {"*": ("trash", "Thermal paper is coated and not recyclable.")}),
    "Banana peel": (["fruit peel", "vegetable peel", "food scraps"], {"*": ("compost", "Perfect for compost.")}),
    "Coffee grounds": (["tea bag", "coffee filter"], {"*": ("compost", "Compost it (check plastic in tea bags).")}),
    "Egg shells": (["eggshell"], {"*": ("compost", "Compost, crushed if possible.")}),
    "Disposable coffee cup": (["paper cup", "takeaway cup"], {"*": ("trash", "The plastic lining makes most cups unrecyclable. Check local rules.")}),
    "Plastic bag": (["carrier bag", "bread bag", "plastic film"], {"fr": ("recycle", "Accepted in the yellow bin since 2023."), "us": ("dropoff", "Take to a store film drop-off."), "*": ("dropoff", "Use a store drop-off.")}),
    "Styrofoam": (["polystyrene", "packing foam"], {"fr": ("recycle", "Accepted in the yellow bin since 2023."), "*": ("trash", "Rarely accepted curbside.")}),
    "Empty aerosol can": (["spray can", "deodorant spray"], {"*": ("recycle", "Only when completely empty.")}),
    "Battery": (["batteries", "button cell"], {"*": ("dropoff", "Never in the bin: fire risk. Use a shop or collection point.")}),
    "LED light bulb": (["lightbulb", "lamp", "light bulb"], {"*": ("dropoff", "Take to an electronics / lighting collection point.")}),
    "Phone": (["smartphone", "charger", "cable", "electronics"], {"*": ("dropoff", "E-waste: collection point or retailer take-back.")}),
    "Old clothes": (["textile", "shoes", "t-shirt"], {"*": ("dropoff", "Textile collection bin or donation.")}),
    "Medication": (["pills", "medicine", "drugs"], {"*": ("dropoff", "Return to a pharmacy.")}),
    "Cooking oil": (["used oil", "frying oil"], {"*": ("dropoff", "Seal in a bottle and take to a waste centre.")}),
    "Broken drinking glass": (["ceramic", "mug", "plate", "mirror", "window glass"], {"*": ("trash", "Different glass: it ruins glass recycling.")}),
    "Plastic toothbrush": (["toothbrush", "razor", "pen"], {"*": ("trash", "Mixed materials, not recyclable curbside.")}),
    "Yogurt pot": (["yoghurt pot", "plastic tub", "margarine tub"], {"*": ("recycle", "Empty it, no need to wash.")}),
    "Milk carton": (["juice carton", "tetra pak", "beverage carton"], {"*": ("recycle", "Empty and flatten.")}),
    "Tissues": (["napkin", "paper towel", "kitchen roll"], {"*": ("compost", "Compost if clean of chemicals, otherwise general waste.")}),
}
_INDEX = {alias.lower(): name for name, (aliases, _) in ITEMS.items() for alias in [name, *aliases]}


def search(query: str, region: str, limit: int = 4) -> list[dict]:
    q = (query or "").lower().strip()
    if len(q) < 2:
        return []
    scored: dict[str, float] = {}
    for alias, name in _INDEX.items():
        score = 1.0 if q == alias else 0.9 if (q in alias or alias in q) else difflib.SequenceMatcher(None, q, alias).ratio()
        if score >= 0.6:
            scored[name] = max(scored.get(name, 0), score)
    out = []
    for name, _ in sorted(scored.items(), key=lambda kv: -kv[1])[:limit]:
        rules = ITEMS[name][1]
        bin_id, tip = rules.get(region) or rules["*"]
        out.append({"name": name, "bin": bin_id, "tip": tip})
    return out

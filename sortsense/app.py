"""Flask app exposing the SortSense API and the single-page UI."""
from __future__ import annotations

import os
import urllib.request

from flask import Flask, jsonify, render_template, request

from . import kb
from .impact import Store
from .off import fetch_product
from .rules import BINS, DEFAULT_REGION, REGIONS, decide


def create_app(db_path: str | None = None, opener=urllib.request.urlopen) -> Flask:
    app = Flask(__name__)
    store = Store(db_path or os.environ.get("SORTSENSE_DB", ":memory:"))

    def region_arg() -> str:
        r = request.args.get("region", DEFAULT_REGION)
        return r if r in REGIONS else DEFAULT_REGION

    @app.get("/")
    def index():
        return render_template("index.html", regions={k: v["name"] for k, v in REGIONS.items()}, bins=BINS)

    @app.get("/api/barcode/<code>")
    def barcode(code: str):
        region = region_arg()
        try:
            product = fetch_product(code, opener=opener)
        except ValueError as e:
            return jsonify(error=str(e)), 400
        if product is None:
            return jsonify(error="Product not found. Try the item search, or a demo code like 00000001."), 404
        comps = []
        for c in product.components:
            d = decide(c.material, c.shape, region)
            comps.append({"shape": d.shape, "material": d.material, "bin": d.bin, "label": d.label,
                          "emoji": d.emoji, "tip": d.tip})
        return jsonify(name=product.name, brand=product.brand, image=product.image,
                       source=product.source, components=comps)

    @app.get("/api/item")
    def item():
        return jsonify(results=kb.search(request.args.get("q", ""), region_arg()))

    @app.post("/api/log")
    def log():
        data = request.get_json(silent=True) or {}
        correct, guess = data.get("correct_bin"), data.get("guess_bin")
        if correct not in BINS or (guess is not None and guess not in BINS):
            return jsonify(error="invalid bin"), 400
        region = data.get("region") if data.get("region") in REGIONS else DEFAULT_REGION
        store.log(region, str(data.get("item", ""))[:120], str(data.get("material", "unknown")), correct, guess)
        return jsonify(ok=True), 201

    @app.get("/api/stats")
    def stats():
        return jsonify(store.stats())

    return app


def main():
    create_app().run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))


if __name__ == "__main__":
    main()

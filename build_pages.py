#!/usr/bin/env python3
"""Create static GitHub Pages assets with a hash-verified update manifest.

Usage:
    python3 build_pages.py
    python3 build_pages.py --check

Output: _site/articles.json and _site/manifest.json, suitable for Pages.
Works in this folder in Eryndor-Mods, or at the root of a separate
public Eryndor-Wiki repository (with the same articles.json).
"""
import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path

here = Path(__file__).resolve().parent
p = argparse.ArgumentParser()
p.add_argument("--check", action="store_true")
args = p.parse_args()
source = here / "articles.json"
raw = source.read_bytes()
data = json.loads(raw)
assert data.get("schema") == 1, "Unsupported schema"
revision = data.get("revision")
assert isinstance(revision, int) and revision > 0, "Revision must be positive"
items = data.get("articles")
assert isinstance(items, list) and 0 < len(items) <= 300, "Expected 1-300 articles"
ids = set()
for article in items:
    assert isinstance(article, dict)
    for key in ("id", "title", "cat", "summary", "content", "icon", "search"):
        assert isinstance(article.get(key), str), f"Invalid {key}"
    assert isinstance(article.get("tags"), list)
    assert article["id"] not in ids, f"Duplicate article: {article['id']}"
    # Cooking recipes must be discovered by players inside the Minecraft Atlas.
    # Never publish the historical spoiler article or its auto-generated slot lists.
    assert article["id"] != "cooking-recipes", "Cooking spoiler article must not be published"
    assert 'data-go="cooking-recipes"' not in article["content"], "Broken/spoiler Cooking link"
    assert not re.search(r'<li>\s*<strong>\s*(?:Miejsce|Slot)\s*\d+', article["content"], re.I), "Possible hidden Cooking ingredient list"
    if article["id"] in ("mushrooms", "fishing"):
        # Atlases must remain discovery-based: no per-species inventories,
        # rarity breakdowns or habitat-by-species hints in public articles.
        assert not re.search(r'<h3>\s*(?:Wszystkie\s+\d+\s+gatunków|Wyspa\s+[IVX]+|Tajemnicza lokalizacja|Overworld[^<]*\d+\s+gatunków|Nether[^<]*\d+\s+gatunków|End[^<]*\d+\s+gatunków)', article["content"], re.I), "Forbidden atlas spoiler heading"
        assert not re.search(r'<p>\s*<strong>\s*(?:Pospolity|Wyjątkowy|Legendarny)\s*:</strong>\s*[^<]+,\s*[^<]+', article["content"], re.I), "Forbidden rarity-based species list"
    if article["id"] == "identity":
        # Eryndor title tiers are implementation details, never player-facing.
        for key in ("content", "summary", "search"):
            assert not re.search(r'\b(?:T1|T2|T3|T4|SPEC)\b', article[key], re.I), "Internal Identity tier leaked"
    if article["id"] == "cooking":
        # Dish names, descriptions and effects are public; ingredient combinations
        # remain a discovery mechanic exclusive to the in-game Atlas.
        assert not re.search(r'<h[2-4]>[^<]*(?:przepisy na potrawy|lista składników|kombinacje składników)', article["content"], re.I), "Cooking ingredient spoiler heading"
        assert not re.search(r'data-(?:ingredients|recipe-grid)=|recipe_ingredients', article["content"], re.I), "Cooking ingredient combinations must not be published"
    if article["id"] == "mushrooms":
        assert not re.search(r'/mushroom\s+(?:alchemist|sellhand)', article["content"], re.I), "Trade is NPC-operated, not a player command"
    ids.add(article["id"])
print(f"Validated revision {revision}, {len(items)} articles")
if not args.check:
    output = here / "_site"
    output.mkdir(exist_ok=True)
    (output / "articles.json").write_bytes(raw)
    # Ship approved, self-contained recipe art together with the JSON feed.
    # SVG is textual, with authentic item/model textures embedded as PNG data.
    recipe_assets = here / "assets" / "crafting"
    if recipe_assets.is_dir():
        publish_assets = output / "assets" / "crafting"
        publish_assets.mkdir(parents=True, exist_ok=True)
        for path in recipe_assets.glob("*.svg"):
            svg = path.read_text(encoding="utf-8")
            assert svg.startswith('<?xml') or svg.startswith('<svg'), "Invalid SVG asset"
            assert len(svg) < 300_000, "Oversized recipe SVG"
            assert not re.search(r'<script\\b|\\bon\\w+\\s*=|javascript:', svg, re.I), "Unsafe recipe SVG"
            shutil.copyfile(path, publish_assets / path.name)

    manifest = {
        "schema": 1,
        "revision": revision,
        "sha256": hashlib.sha256(raw).hexdigest()
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8"
    )
    (output / ".nojekyll").write_text("", encoding="utf-8")
    (output / "index.html").write_text(
        '<!doctype html><html lang="pl"><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width">'
        '<title>Eryndor Wiki — aktualizacje</title>'
        '<body style="font:18px system-ui;padding:24px;background:#111922;color:#f5e4c2">'
        '<h1>Eryndor Wiki</h1>'
        '<p>Ta witryna publikuje aktualizacje artykułów dla aplikacji Android.</p>'
        '<p><a style="color:#e3bd77" href="./articles.json">Dane encyklopedii</a></p>'
        '</body></html>',
        encoding="utf-8"
    )
    print("Ready to publish:", output)

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
import base64
import copy
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
source_articles = copy.deepcopy(data.get("articles", []))
items = data.get("articles")
assert isinstance(items, list) and 0 < len(items) <= 300, "Expected 1-300 articles"
ids = set()
for article in items:
    assert isinstance(article, dict)
    for key in ("id", "title", "cat", "summary", "content", "icon", "search"):
        assert isinstance(article.get(key), str), f"Invalid {key}"
    assert isinstance(article.get("tags"), list)
    assert article["id"] not in ids, f"Duplicate article: {article['id']}"
    # "Eryndor" is masculine; genitive must be "Eryndoru", not "Eryndora".
    # Search title, visible text, keyword index and tags to prevent regression.
    for key in ("title", "summary", "content", "search"):
        assert not re.search(r'\bEryndora\b', article[key], re.I), "Incorrect Eryndor declension: use Eryndoru"
    for tag in article["tags"]:
        assert isinstance(tag, str) and not re.search(r'\bEryndora\b', tag, re.I), "Incorrect Eryndor declension in tags"

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
    # Render the seven approved backpack recipes using SHA-verified resources
    # from the exact Sophisticated Backpacks 3.26.12.2208 JAR. Embed images
    # into the JSON itself so Android WebView renders them fully offline.
    from render_backpacks import IDS as BACKPACK_IDS, generate_bilingual as build_backpack_cards
    backpack_images, backpack_images_en = build_backpack_cards(
        output / "assets" / "crafting" / "backpacks",
        output / "assets" / "crafting" / "backpacks-en")
    backpack = next(article for article in items if article["id"] == "backpacks")
    for key in BACKPACK_IDS:
        marker = "@@BACKPACK_CARD:" + key + "@@"
        assert backpack["content"].count(marker) == 1, "Missing or duplicated backpack image placeholder: " + key
        image = backpack_images[key]
        assert image.startswith("data:image/png;base64,"), "Backpack image is not self-contained PNG"
        replacement = ('<img class="recipe-image" src="' + image + '" '
                       'alt="Crafting plecaka: ' + key.replace("_", " ") + '." />')
        backpack["content"] = backpack["content"].replace(marker, replacement)
    assert "@@BACKPACK_CARD:" not in backpack["content"], "Unresolved backpack image"
    assert len(backpack["content"]) < 350000, "Images exceed Android article size limit"
    raw = (json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
    # Waystones 21.1.45 cards: real mod/vanilla textures, 11 verified recipes.
    # Inline WEBP data URIs are supported by Android 0.5.1 and work offline.
    from render_waystones import IDS as WAYSTONES_IDS, generate_bilingual as build_waystones_cards
    waystones_images, waystones_images_en = build_waystones_cards(
        output / "assets" / "crafting" / "waystones",
        output / "assets" / "crafting" / "waystones-en")
    waystones = next(article for article in items if article["id"] == "waystones")
    for key in WAYSTONES_IDS:
        marker = "@@WAYSTONES_CARD:" + key + "@@"
        assert waystones["content"].count(marker) == 1, "Missing or duplicated Waystones image: " + key
        image = waystones_images[key]
        assert image.startswith("data:image/webp;base64,"), "Waystones asset must be self-contained WEBP"
        replacement = ('<img class="recipe-image" src="' + image + '" '
                       'alt="Waystones 21.1.45 — crafting ' + key.replace("_", " ") + '." />')
        waystones["content"] = waystones["content"].replace(marker, replacement)
    assert "@@WAYSTONES_CARD:" not in waystones["content"], "Unresolved Waystones recipe image"
    assert len(waystones["content"]) < 1200000, "Waystones article exceeds maximum image size"
    raw = (json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
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

    # Compatibility guarantee: original articles.json and manifest.json
    # remain schema 1, byte-for-byte legacy-shaped for all older clients.
    translations_path = here / "translations" / "en.json"
    translations = json.loads(translations_path.read_text(encoding="utf-8"))
    assert translations.get("schema") == 1
    en_revision = translations.get("revision")
    assert isinstance(en_revision, int) and en_revision > 0
    translations_by_id = translations.get("articles", {})
    assert isinstance(translations_by_id, dict)
    assert set(translations_by_id).issubset(ids), "Translation for unknown article"
    source_by_id = {x["id"]: x for x in source_articles}
    en_articles = []
    en_ids = set()

    def insert_crafting_images(text, article_id):
        if article_id == "backpacks":
            for key in BACKPACK_IDS:
                marker = "@@BACKPACK_CARD:" + key + "@@"
                assert text.count(marker) == 1, "EN missing backpack image " + key
                text = text.replace(marker, '<img class="recipe-image" src="' +
                    backpack_images_en[key] + '" alt="Backpack crafting: ' + key.replace("_", " ") + '" />')
        if article_id == "waystones":
            for key in WAYSTONES_IDS:
                marker = "@@WAYSTONES_CARD:" + key + "@@"
                assert text.count(marker) == 1, "EN missing Waystones image " + key
                text = text.replace(marker, '<img class="recipe-image" src="' +
                    waystones_images_en[key] + '" alt="Waystones crafting: ' + key.replace("_", " ") + '" />')
        if article_id == "cooking":
            assert text.count("@@COOKING_IMAGE@@") == 1
            svg = (here / "assets" / "crafting" / "culinary-cauldron.svg").read_text(encoding="utf-8")
            captions = {
                "Kociołek Kulinarny": "Culinary Cauldron",
                "Pixelmon Cooking — przepis na blok": "Pixelmon Cooking — crafting recipe",
                "Składniki": "Ingredients",
                "sztabka miedzi": "Copper Ingot",
                "sztabka żelaza": "Iron Ingot",
                "blok żelaza": "Block of Iron",
                "Rząd": "Row",
                "pusty": "empty",
                "Rezultat": "Result"
            }
            for pl, en in captions.items(): svg = svg.replace(pl, en)
            image_uri = "data:image/svg+xml;base64," + base64.b64encode(svg.encode("utf-8")).decode("ascii")
            text = text.replace("@@COOKING_IMAGE@@",
                '<img class="recipe-image" src="' + image_uri + '" alt="Culinary Cauldron crafting recipe" />')
        assert "@@BACKPACK_CARD:" not in text and "@@WAYSTONES_CARD:" not in text and "@@COOKING_IMAGE@@" not in text
        return text

    for src in source_articles:
        item_id = src["id"]
        tr = translations_by_id.get(item_id)
        if tr is None:
            # Missing translation: the new client uses the current Polish article.
            continue
        assert isinstance(tr, dict)
        # If the PL source changes after translation, the EN entry is removed
        # from publication until verified. No outdated rules are displayed as EN.
        if tr.get("sourceUpdatedAt") != src.get("updatedAt"):
            print(f"Translation needs review: {item_id}")
            continue
        for key in ("title", "summary", "search", "content"):
            assert isinstance(tr.get(key), str) and tr[key], "Missing EN " + key + " in " + item_id
        assert isinstance(tr.get("tags"), list) and all(isinstance(x, str) for x in tr["tags"])
        en_content = insert_crafting_images(tr["content"], item_id)
        assert len(en_content) < 1200000, "English article exceeds WebView size limit: " + item_id
        en_article = {key: copy.deepcopy(src[key]) for key in ("id", "cat", "icon", "updatedAt")}
        en_article.update({key: tr[key] for key in ("title", "summary", "search", "tags")})
        en_article["content"] = en_content
        en_articles.append(en_article)
        en_ids.add(item_id)
    assert en_articles, "At least one reviewed English article required"
    en_downloads = []
    en_download_overrides = translations.get("downloads", {})
    assert isinstance(en_download_overrides, dict)
    for download in data.get("downloads", []):
        row = dict(download)
        replacement = en_download_overrides.get(row["id"])
        if replacement:
            assert isinstance(replacement.get("title"), str) and isinstance(replacement.get("description"), str)
            row.update(title=replacement["title"], description=replacement["description"])
        en_downloads.append(row)
    en_packet = {"schema": 2, "revision": en_revision, "articles": en_articles, "downloads": en_downloads}
    en_bytes = (json.dumps(en_packet, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
    (output / "articles.en.json").write_bytes(en_bytes)
    v2_manifest = {
        "schema": 2,
        "languages": {
            "pl": {"file": "articles.json", "revision": revision, "sha256": hashlib.sha256(raw).hexdigest()},
            "en": {"file": "articles.en.json", "revision": en_revision, "sha256": hashlib.sha256(en_bytes).hexdigest()}
        }
    }
    (output / "manifest-v2.json").write_text(json.dumps(v2_manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Bilingual feed: {len(en_articles)}/{len(items)} English translations, PL {revision}, EN {en_revision}")
    print("Ready to publish:", output)

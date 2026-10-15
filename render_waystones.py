#!/usr/bin/env python3
"""Generate Waystones 21.1.45 crafting pictures for the Eryndor Android Wiki.

Art and recipes are loaded from the official Waystones 1.21.1 source branch.
The recipe patterns below are independently checked against the exact
waystones-neoforge-1.21.1-21.1.45.jar supplied for Eryndor. Minecraft icons
are loaded from the pinned Minecraft Java 1.21.1 asset extraction.

No client GUI change or new APK is required: WEBP images are embedded in
the article JSON as data URIs for offline reading. Block-result icons are
texture-based illustrative previews, NOT captures of in-game 3-D models.
"""
import base64
import collections
import io
import json
import math
from pathlib import Path
from urllib.request import urlopen

from PIL import Image, ImageDraw, ImageFont

WAYSTONES_REV = "1.21.1"
MOD_ROOT = f"https://raw.githubusercontent.com/TwelveIterations/Waystones/{WAYSTONES_REV}/common/"
RECIPE_ROOT = MOD_ROOT + "src/generated/resources/data/waystones/recipe/"
MOD_ITEM_ROOT = MOD_ROOT + "src/main/resources/assets/waystones/textures/item/"
MOD_BLOCK_ROOT = MOD_ROOT + "src/main/resources/assets/waystones/textures/block/"
MC_ROOT = ("https://raw.githubusercontent.com/InventivetalentDev/minecraft-assets/"
           "aef047f783f44424a591eeecf6b230d5bb0c8095/assets/minecraft/textures/")
IDS = ("warp_dust", "warp_stone", "waystone", "dormant_shard",
       "warp_plate", "blank_scroll", "return_scroll", "warp_scroll",
       "portal_scroll", "white_portstone", "black_sharestone")
TITLE = {
    "warp_dust": "Warp Dust", "warp_stone": "Warp Stone",
    "waystone": "Waystone", "dormant_shard": "Dormant Shard",
    "warp_plate": "Warp Plate", "blank_scroll": "Blank Scroll",
    "return_scroll": "Return Scroll", "warp_scroll": "Warp Scroll",
    "portal_scroll": "Portal Scroll", "white_portstone": "Biały Portstone",
    "black_sharestone": "Czarny Sharestone",
}
TITLE_EN = dict(TITLE, white_portstone="White Portstone", black_sharestone="Black Sharestone")
LABEL_EN = {
 "minecraft:ender_pearl":"Ender Pearl","minecraft:amethyst_shard":"Amethyst Shard",
 "minecraft:emerald":"Emerald","minecraft:flint":"Flint","minecraft:gold_nugget":"Gold Nugget",
 "minecraft:paper":"Paper","minecraft:ink_sac":"Ink Sac","minecraft:feather":"Feather",
 "minecraft:white_dye":"White Dye","minecraft:black_dye":"Black Dye",
 "minecraft:stone_bricks":"Stone Bricks","minecraft:obsidian":"Obsidian",
 "minecraft:polished_andesite":"Polished Andesite",
 "waystones:warp_stone":"Warp Stone","waystones:warp_dust":"Warp Dust",
 "waystones:dormant_shard":"Dormant Shard"
}
# Tested by reading the original JAR recipe JSON in this project's conversation.
EXPECTED = {
    "warp_dust": ("shapeless", ["minecraft:ender_pearl", "minecraft:amethyst_shard"], 4),
    "warp_stone": ("DED/EGE/DED", None, 1),
    "waystone": (" S /SWS/OOO", None, 1),
    "dormant_shard": ("shapeless", ["waystones:warp_dust","waystones:warp_dust","minecraft:flint"], 1),
    "warp_plate": ("SWS/WFW/SWS", None, 1),
    "blank_scroll": ("GFG/PPP", None, 3),
    "return_scroll": ("GEG/PPP", None, 3),
    "warp_scroll": ("GDG/GEG/PPP", None, 3),
    "portal_scroll": ("SIS/SES/PPP", None, 3),
    "white_portstone": ("DSD/SWS/BBB", None, 1),
    "black_sharestone": ("SSS/DWD/OOO", None, 1),
}
VANILLA_ITEM = {
    "minecraft:ender_pearl": "ender_pearl",
    "minecraft:amethyst_shard": "amethyst_shard",
    "minecraft:emerald": "emerald",
    "minecraft:flint": "flint",
    "minecraft:gold_nugget": "gold_nugget",
    "minecraft:paper": "paper",
    "minecraft:ink_sac": "ink_sac",
    "minecraft:feather": "feather",
    "minecraft:white_dye": "white_dye",
    "minecraft:black_dye": "black_dye",
}
VANILLA_BLOCK = {
    "minecraft:stone_bricks": "stone_bricks",
    "minecraft:obsidian": "obsidian",
    "minecraft:polished_andesite": "polished_andesite",
}
ITEM_TAG = {
    "c:gems/emerald":"minecraft:emerald",
    "c:nuggets/gold":"minecraft:gold_nugget",
    "c:dyes/white":"minecraft:white_dye",
    "c:dyes/black":"minecraft:black_dye",
}
LABEL = {
    "minecraft:ender_pearl":"Perła Endu", "minecraft:amethyst_shard":"Odłamek ametystu",
    "minecraft:emerald":"Szmaragd", "minecraft:flint":"Krzemień",
    "minecraft:gold_nugget":"Samorodek złota", "minecraft:paper":"Papier",
    "minecraft:ink_sac":"Worek z atramentem", "minecraft:feather":"Pióro",
    "minecraft:white_dye":"Biały barwnik","minecraft:black_dye":"Czarny barwnik",
    "minecraft:stone_bricks":"Kamienne cegły","minecraft:obsidian":"Obsydian",
    "minecraft:polished_andesite":"Polerowany andezyt",
    "waystones:warp_stone":"Warp Stone", "waystones:warp_dust":"Warp Dust",
    "waystones:dormant_shard":"Dormant Shard"
}
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

def font(size, bold=False):
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size)

def download(url):
    with urlopen(url, timeout=40) as response:
        return response.read()

def read_png(url):
    img=Image.open(io.BytesIO(download(url)))
    img.load()
    return img.convert("RGBA")

def normalize(item):
    if "item" in item:
        return item["item"]
    if "tag" in item:
        return ITEM_TAG[item["tag"]]
    raise ValueError(f"Unexpected ingredient {item}")

def get_recipes():
    recipes={}
    for key in IDS:
        r=json.loads(download(RECIPE_ROOT+key+".json"))
        expected, ingredients, count=EXPECTED[key]
        assert r["result"]=={"count":count,"id":"waystones:"+key}, key
        if expected=="shapeless":
            assert r["type"]=="minecraft:crafting_shapeless", key
            got=[normalize(t) for t in r["ingredients"]]
            assert got==ingredients, (key,got)
        else:
            assert r["type"]=="minecraft:crafting_shaped", key
            assert "/".join(r["pattern"])==expected, key
        recipes[key]=r
    return recipes

def slots(recipe):
    if recipe["type"].endswith("crafting_shapeless"):
        return [normalize(x) for x in recipe["ingredients"]] + [None]*(9-len(recipe["ingredients"]))
    parts=[]
    for row in recipe["pattern"]:
        parts.extend(normalize(recipe["key"][letter]) if letter!=" " else None for letter in row)
        parts.extend([None]*(3-len(row)))
    while len(parts)<9: parts.append(None)
    return parts

def shadowed_cube(texture):
    # Actual vanilla block PNG, displayed as an isometric icon rather than a
    # flat "item" square. Darken the two visible sides for dimension.
    tex=texture.resize((64,64),Image.Resampling.NEAREST)
    tile=Image.new("RGBA",(128,128))
    left=tex.copy();right=tex.copy()
    def shade(pic,amount):
        rgb=Image.new("RGBA",pic.size)
        return Image.blend(Image.new("RGBA",pic.size,"#10151a"),pic,amount)
    left=shade(left,.77);right=shade(right,.61)
    poly=[[(11,43),(64,69),(64,115),(11,89)],
          [(64,69),(117,43),(117,89),(64,115)],
          [(11,43),(64,16),(117,43),(64,69)]]
    color=(left,right,tex)
    for pts,texture in zip(poly,color):
        mask=Image.new("L",(128,128))
        ImageDraw.Draw(mask).polygon(pts,fill=255)
        # Tiny textures are genuine; shape is a schematic cube projection.
        tile.paste(texture.resize((128,128),Image.Resampling.NEAREST),(0,0),mask)
    d=ImageDraw.Draw(tile)
    for pts in poly:d.line(pts+[pts[0]],fill="#353239",width=3)
    return tile

def block_preview(key):
    # The following are illustrative previews made of actual 1.21.1 Waystones
    # textures, not screenshots of the mod's item renderers.
    if key=="warp_plate":
        tex=read_png(MOD_BLOCK_ROOT+"warp_plate.png")
        border=read_png(MOD_BLOCK_ROOT+"warp_plate_base.png")
        canvas=Image.new("RGBA",(160,160))
        d=ImageDraw.Draw(canvas)
        d.ellipse((17,104,143,142),fill=(4,3,5,35))
        d.polygon([(17,93),(80,65),(143,93),(80,121)],fill="#74736d",outline="#363b36",width=3)
        resized=tex.resize((92,92),Image.Resampling.NEAREST)
        canvas.alpha_composite(resized,(34,48))
        d.polygon([(17,93),(80,121),(80,134),(17,108)],fill="#454646")
        d.polygon([(80,121),(143,93),(143,108),(80,134)],fill="#303437")
        d.polygon([(17,93),(80,65),(143,93),(80,121)],outline="#151916",width=3)
        return canvas
    texfile="andesite_waystone.png"
    runes="waystone_runes.png"
    if key=="white_portstone":runes="portstone_runes.png"
    if key=="black_sharestone":runes="sharestone_runes.png"
    surface=read_png(MOD_BLOCK_ROOT+texfile).resize((128,128),Image.Resampling.NEAREST)
    symbol=read_png(MOD_BLOCK_ROOT+runes)
    canvas=Image.new("RGBA",(160,160))
    d=ImageDraw.Draw(canvas)
    d.ellipse((31,139,133,153),fill=(9,8,10,30))
    d.polygon([(44,26),(84,7),(124,26),(84,47)],fill="#90958e",outline="#35373c")
    d.polygon([(44,26),(84,47),(84,134),(44,112)],fill="#5f6666",outline="#373a3c")
    d.polygon([(84,47),(124,26),(124,112),(84,134)],fill="#41494c",outline="#2a3337")
    # Tiny, actual rune texture overlay evokes the right Waystones family.
    symbol=symbol.resize((48,72),Image.Resampling.NEAREST)
    canvas.alpha_composite(symbol,(58,53))
    d.line([(44,26),(84,47),(124,26)],fill="#222629",width=3)
    if key=="black_sharestone":
        d.line([(44,109),(84,132),(124,109)],fill="#3c4143",width=5)
    return canvas

def load_icons():
    icons={}
    for key,name in VANILLA_ITEM.items():
        icons[key]=read_png(MC_ROOT+"item/"+name+".png")
    for key,name in VANILLA_BLOCK.items():
        icons[key]=shadowed_cube(read_png(MC_ROOT+"block/"+name+".png"))
    for name in ("warp_stone","warp_dust","dormant_shard",
                 "blank_scroll","return_scroll","warp_scroll","portal_scroll"):
        icons["waystones:"+name]=read_png(MOD_ITEM_ROOT+name+".png")
    for name in ("waystone","warp_plate","white_portstone","black_sharestone"):
        icons["waystones:"+name]=block_preview(name)
    return icons

def scaled_icon(canvas,raw,x,y,size=78):
    raw=raw.convert("RGBA")
    ratio=(size-6)/max(raw.size)
    res=Image.Resampling.NEAREST
    tile=raw.resize((max(1,round(raw.width*ratio)),max(1,round(raw.height*ratio))),res)
    canvas.alpha_composite(tile,(round(x+(size-tile.width)/2),round(y+(size-tile.height)/2)))

def generate_card(key,recipe,icons,lang='pl'):
    W,H=1200,720
    canvas=Image.new("RGBA",(W,H),"#242025")
    d=ImageDraw.Draw(canvas)
    d.rounded_rectangle((19,18,1180,702),radius=30,fill="#ac8852")
    d.rounded_rectangle((35,34,1165,683),radius=19,fill="#e4d0a0")
    title=(TITLE_EN if lang=='en' else TITLE)[key]
    title_f=font(43,True)
    d.text((600,64),title,font=title_f,fill="#382b1f",anchor="ma")
    shapeless=recipe["type"].endswith("crafting_shapeless")
    d.text((600,119),("Shapeless — any arrangement" if shapeless else "Crafting Table — 3 × 3") if lang=="en" else ("Bezkształtny — dowolny układ" if shapeless else "Stół craftingowy — 3 × 3"),
           font=font(22),fill="#4c3d2b",anchor="ma")
    d.line((75,157,1125,157),fill="#92724c",width=2)
    recipe_slots=slots(recipe)
    def draw_slot(x,y,size=106):
        d.rounded_rectangle((x,y,x+size,y+size),radius=9,fill="#efe3c6",outline="#947851",width=3)
    for i,item in enumerate(recipe_slots):
        x=126+(i%3)*112;y=183+(i//3)*112
        draw_slot(x,y)
        if item: scaled_icon(canvas,icons[item],x+11,y+11,84)
    d.polygon([(558,326),(654,326),(654,295),(733,352),(654,409),(654,383),(558,383)],fill="#6c4e34")
    draw_slot(828,244,184)
    result=recipe["result"]["id"]
    scaled_icon(canvas,icons[result],860,277,122)
    d.text((920,458),(TITLE_EN if lang=="en" else TITLE)[key],anchor="ma",fill="#382b1f",font=font(19,True))
    count=recipe["result"]["count"]
    if count>1:d.text((1005,405),f"×{count}",fill="#2e2420",font=font(24,True))
    d.line((75,548,1125,548),fill="#92724c",width=2)
    d.text((86,566),"Ingredients" if lang=="en" else "Składniki",font=font(27,True),fill="#382b1f")
    needed=collections.OrderedDict()
    for item in recipe_slots:
        if item:needed[item]=needed.get(item,0)+1
    for i,(item,count) in enumerate(needed.items()):
        x=88+(i%3)*350;y=611+(i//3)*39
        scaled_icon(canvas,icons[item],x,y-3,34)
        label=(LABEL_EN if lang=="en" else LABEL).get(item,(TITLE_EN if lang=="en" else TITLE).get(item.split(":")[-1],item))
        if len(label)>24:label=label[:23]+"…"
        d.text((x+47,y),f"{count} × {label}",font=font(18),fill="#382b1f")
    return canvas.convert("RGB")

def generate_bilingual(outdir_pl,outdir_en):
    destinations=[Path(outdir_pl),Path(outdir_en)]
    for dest in destinations: dest.mkdir(parents=True,exist_ok=True)
    recipes=get_recipes()
    icons=load_icons()
    outputs=[{},{}]
    for key in IDS:
        for i,lang in enumerate(("pl","en")):
            image=generate_card(key,recipes[key],icons,lang)
            buffer=io.BytesIO()
            image.save(buffer,format="WEBP",quality=76,method=6)
            raw=buffer.getvalue()
            outputs[i][key]="data:image/webp;base64,"+base64.b64encode(raw).decode("ascii")
            assert len(outputs[i][key])<240000, ("Data URI too large",key)
            (destinations[i]/(key+".webp")).write_bytes(raw)
            print("Waystones card:",key,lang,len(raw),"bytes")
    return tuple(outputs)

def generate(outdir):
    return generate_bilingual(outdir,Path(outdir).parent/"_en")[0]

if __name__=="__main__":
    import sys
    generate(Path(sys.argv[1]) if len(sys.argv)>1 else Path("_site/assets/crafting/waystones"))

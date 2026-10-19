#!/usr/bin/env python3
"""Rebuild seven Eryndor Wiki backpack cards from SHA-verified Minecraft 1.21.1
and SophisticatedBackpacks 3.26.12.2208 resources. No hidden recipes.
The upstream resource hashes were checked against the user's exact JAR.
"""
import base64
import collections
import hashlib
import io
import json
import math
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

MOD_REV = "974d5e1d74fdac91b20b026407b8ea5ba0e7ebc4"
MC_REV = "aef047f783f44424a591eeecf6b230d5bb0c8095"
MOD_URL = f"https://raw.githubusercontent.com/P3pp3rF1y/SophisticatedBackpacks/{MOD_REV}/"
MC_URL = f"https://raw.githubusercontent.com/InventivetalentDev/minecraft-assets/{MC_REV}/assets/minecraft/textures/"
BASE = "src/main/resources/assets/sophisticatedbackpacks/"
DATA = "src/generated/resources/data/sophisticatedbackpacks/recipe/"
CHECKSUMS = {
    "backpack_base": "e7af7012c5c8c3784f00ed80ed7f4d3d2c333523",
    "backpack_front_pouch": "777069316bc6bef042198620c58c98923462b3ff",
    "backpack_straps": "b99e3e5a338003474efdbb5fc36e8165a3af005d",
    "backpack_cloth": "a449298a06b5283af80ec5a4a2b945970d0a40e6",
    "backpack_border": "50d776d905ec343fc4799f42a4c552508a703a16",
    "leather_clips": "b0538fa38044329b2e3ed1e3f613017ca1f5760a",
    "copper_clips": "a43bc978face784ff1e7f1fb2763703b1c77bef9",
    "iron_clips": "dea1b5d5e90dc2d725d4784fdac38da72e6d694e",
    "gold_clips": "98f471ec73866ad738f112b75f98c85a2d312d88",
    "diamond_clips": "ab501a32faed19c1840999f49fcd1c9102b0ad8f",
    "netherite_clips": "1a1983846cb7c542994984c09bf1098de3263638",
    "recipe/backpack": "9e2fc9b4827586e72995fe4c54aeb7494355033a",
    "recipe/copper_backpack": "f67b6dcd8fa779af4e4ba33bde7abee58f571f88",
    "recipe/iron_backpack": "7e7bc7ed29f1013ff933d30c2e7860728c39c88e",
    "recipe/iron_backpack_from_copper": "45b07f26a3e496ad0d795855723270d06f5a2319",
    "recipe/gold_backpack": "309d67f942599a6f055f56f2ca2a1e42d5579968",
    "recipe/diamond_backpack": "8ecde44a1a08f7aac34cb162d3979c5d4cbce1e3",
    "recipe/netherite_backpack": "53e275368c5417498cce46477844d6121e7c763a",
}
IDS = ["backpack", "copper_backpack", "iron_backpack",
       "iron_backpack_from_copper", "gold_backpack", "diamond_backpack", "netherite_backpack"]
NAMES = {
    "backpack": "Podstawowy plecak",
    "copper_backpack": "Plecak miedziany",
    "iron_backpack": "Plecak żelazny",
    "iron_backpack_from_copper": "Żelazny z miedzianego",
    "gold_backpack": "Plecak złoty",
    "diamond_backpack": "Plecak diamentowy",
    "netherite_backpack": "Plecak netherytowy",
}
MATERIALS = {
    "c:strings": ("Nić", "string"),
    "c:leathers": ("Skóra", "leather"),
    "c:chests/wooden": ("Skrzynia", "chest"),
    "c:ingots/copper": ("Sztabka miedzi", "copper_ingot"),
    "c:ingots/iron": ("Sztabka żelaza", "iron_ingot"),
    "c:ingots/gold": ("Sztabka złota", "gold_ingot"),
    "c:gems/diamond": ("Diament", "diamond"),
    "minecraft:netherite_ingot": ("Sztabka netherytu", "netherite_ingot"),
    "minecraft:netherite_upgrade_smithing_template": ("Szablon netherytowy", "netherite_upgrade_smithing_template"),
}
NAMES_EN = {"backpack":"Basic Backpack","copper_backpack":"Copper Backpack","iron_backpack":"Iron Backpack","iron_backpack_from_copper":"Iron from Copper Backpack","gold_backpack":"Gold Backpack","diamond_backpack":"Diamond Backpack","netherite_backpack":"Netherite Backpack"}
MATERIALS_EN = {
 "c:strings":"String","c:leathers":"Leather","c:chests/wooden":"Chest",
 "c:ingots/copper":"Copper Ingot","c:ingots/iron":"Iron Ingot","c:ingots/gold":"Gold Ingot",
 "c:gems/diamond":"Diamond","minecraft:netherite_ingot":"Netherite Ingot",
 "minecraft:netherite_upgrade_smithing_template":"Netherite Upgrade",
 "sophisticatedbackpacks:backpack":"Basic Backpack",
 "sophisticatedbackpacks:copper_backpack":"Copper Backpack",
 "sophisticatedbackpacks:iron_backpack":"Iron Backpack",
 "sophisticatedbackpacks:gold_backpack":"Gold Backpack",
 "sophisticatedbackpacks:diamond_backpack":"Diamond Backpack",
 "sophisticatedbackpacks:netherite_backpack":"Netherite Backpack"
}
def label(item, lang):
    return MATERIALS_EN.get(item, MATERIALS[item][0]) if lang=="en" else MATERIALS[item][0]

for tier in ("backpack", "copper", "iron", "gold", "diamond", "netherite"):
    MATERIALS["sophisticatedbackpacks:" + ("backpack" if tier == "backpack" else tier + "_backpack")] = (
        {"backpack":"Podstawowy plecak", "copper":"Miedziany plecak", "iron":"Żelazny plecak",
         "gold":"Złoty plecak", "diamond":"Diamentowy plecak", "netherite":"Netherytowy plecak"}[tier],
        "model_" + tier
    )

def git_blob_sha(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\x00" + raw).hexdigest()

def fetch(url, digest=None):
    with urllib.request.urlopen(url, timeout=50) as resp:
        raw = resp.read()
    if digest and git_blob_sha(raw) != digest:
        raise ValueError(f"Resource changed from verified SophisticatedBackpacks JAR: {url}")
    return raw

def load_assets():
    models = [json.loads(fetch(MOD_URL + BASE + f"models/block/{n}.json", CHECKSUMS[n]))
              for n in ("backpack_base","backpack_front_pouch","backpack_straps")]
    textures = {
        n: np.asarray(Image.open(io.BytesIO(fetch(MOD_URL + BASE + f"textures/block/{n}.png", CHECKSUMS[n]))).convert("RGBA"))
        for n in ("backpack_cloth", "backpack_border", "leather_clips", "copper_clips",
                  "iron_clips", "gold_clips", "diamond_clips", "netherite_clips")
    }
    recipes = {
        name: json.loads(fetch(MOD_URL + DATA + name + ".json", CHECKSUMS["recipe/" + name]))
        for name in IDS
    }
    return models, textures, recipes

def render_backpack(tier, models, textures):
    # Minecraft block-model geometry and authentic textures, projected into an
    # isometric preview. Same renderer and palette as the approved preview cards.
    G = 260
    buffer = np.zeros((G, G, 4), np.uint8)
    depth = np.full((G, G), 1e7, np.float32)
    ca, sa = math.cos(math.radians(-27)), math.sin(math.radians(-27))
    ct, st = math.cos(math.radians(24)), math.sin(math.radians(24))
    tint = {0: np.array([.64,.39,.23]), 1: np.array([.38,.27,.19])}
    clips = ("leather" if tier == "backpack" else tier) + "_clips"

    def proj(pts):
        a = np.array(pts, dtype=float) - [8,8,8]
        x = a[:,0]*ca + a[:,2]*sa
        z = -a[:,0]*sa + a[:,2]*ca
        y = a[:,1]*ct + z*st
        dep = z*ct - a[:,1]*st
        return np.stack([130+x*17, 130-y*17, dep],axis=1)

    def faces(ini,end):
        x,y,z=ini; X,Y,Z=end
        return {"north":[(x,y,z),(X,y,z),(X,Y,z),(x,Y,z)],
                "south":[(X,y,Z),(x,y,Z),(x,Y,Z),(X,Y,Z)],
                "west":[(x,y,Z),(x,y,z),(x,Y,z),(x,Y,Z)],
                "east":[(X,y,z),(X,y,Z),(X,Y,Z),(X,Y,z)],
                "up":[(x,Y,z),(X,Y,z),(X,Y,Z),(x,Y,Z)],
                "down":[(x,y,Z),(X,y,Z),(X,y,z),(x,y,z)]}

    for model in models:
        for element in model["elements"]:
            geom = faces(element["from"], element["to"])
            for side, face in element["faces"].items():
                uv=face.get("uv")
                if not uv or uv[0]==uv[2] or uv[1]==uv[3]: continue
                name={"cloth":"backpack_cloth","border":"backpack_border","clips":clips}.get(face["texture"].removeprefix("#"))
                if name is None: continue
                tex=textures[name]
                pts=proj(geom[side])
                e1=pts[1,:2]-pts[0,:2];e2=pts[3,:2]-pts[0,:2]
                det=e1[0]*e2[1]-e1[1]*e2[0]
                if abs(det)<1: continue
                minx=max(0,int(np.floor(min(pts[:,0])))); maxx=min(G-1,int(np.ceil(max(pts[:,0]))))
                miny=max(0,int(np.floor(min(pts[:,1])))); maxy=min(G-1,int(np.ceil(max(pts[:,1]))))
                if minx>maxx or miny>maxy: continue
                xx,yy=np.meshgrid(np.arange(minx,maxx+1),np.arange(miny,maxy+1))
                dx=xx-pts[0,0];dy=yy-pts[0,1]
                s=(dx*e2[1]-dy*e2[0])/det
                t=(e1[0]*dy-e1[1]*dx)/det
                z=pts[0,2]+s*(pts[1,2]-pts[0,2])+t*(pts[3,2]-pts[0,2])
                dd=depth[miny:maxy+1,minx:maxx+1]
                valid=(s>=0)&(s<=1)&(t>=0)&(t<=1)&(z<dd)
                if not np.any(valid): continue
                u0,v0,u1,v1=uv
                u=np.clip(((u0+s*(u1-u0))/16*tex.shape[1]).astype(int),0,tex.shape[1]-1)
                v=np.clip(((v0+t*(v1-v0))/16*tex.shape[0]).astype(int),0,tex.shape[0]-1)
                color=tex[v,u].copy()
                if face.get("tintindex") in tint:
                    color[:,:,:3]=np.clip(color[:,:,:3].astype(float)*tint[face["tintindex"]],0,255).astype(np.uint8)
                light={"north":.97,"south":.72,"east":.81,"west":.90,"up":1.06,"down":.65}[side]
                color[:,:,:3]=np.minimum(255,color[:,:,:3].astype(float)*light).astype(np.uint8)
                valid &= color[:,:,3]>8
                bb=buffer[miny:maxy+1,minx:maxx+1]
                bb[valid]=color[valid];dd[valid]=z[valid]
    im=Image.fromarray(buffer,"RGBA")
    bbox=im.getbbox()
    if not bbox: raise ValueError(f"Empty backpack icon {tier}")
    im=im.crop(bbox)
    ratio=min(115/im.width,115/im.height)
    im=im.resize((round(im.width*ratio),round(im.height*ratio)),Image.Resampling.NEAREST)
    out=Image.new("RGBA",(128,128))
    out.alpha_composite(im,((128-im.width)//2,(128-im.height)//2))
    return out

def get_icons(models, textures):
    icons={}
    for tier in ("backpack","copper","iron","gold","diamond","netherite"):
        icons["model_"+tier]=render_backpack(tier, models, textures)
    for item in ("string","leather","copper_ingot","iron_ingot","gold_ingot","diamond",
                 "netherite_ingot","netherite_upgrade_smithing_template"):
        icons[item]=Image.open(io.BytesIO(fetch(MC_URL+f"item/{item}.png"))).convert("RGBA")
    atlas=Image.open(io.BytesIO(fetch(MC_URL+"entity/chest/normal.png"))).convert("RGBA")
    # Extract recognizable chest front/lid from Minecraft's original chest atlas.
    chest=Image.new("RGBA",(16,16))
    chest.paste(atlas.crop((14,29,28,39)).resize((14,10),Image.Resampling.NEAREST),(1,5))
    chest.paste(atlas.crop((14,14,28,19)).resize((14,4),Image.Resampling.NEAREST),(1,1))
    d=ImageDraw.Draw(chest)
    d.rectangle((1,0,14,15),outline="#392412",width=1)
    d.line((1,5,14,5),fill="#3d2a1d")
    d.rectangle((7,4,9,8),fill="#b7b4aa",outline="#514a3e")
    icons["chest"]=chest
    return icons

FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
COL={"bg":"#201d21","edge":"#ad8750","paper":"#e4d0a0","slot":"#eae0c6","shadow":"#755f47","ink":"#37281f","arrow":"#694e36"}
def font(sz, bold=False):
    return ImageFont.truetype(BOLD if bold else FONT,sz)

def icon(im, icons, item, x, y, w=80):
    key=MATERIALS[item][1]
    raw=icons[key]
    factor=(w-10)/max(raw.width,raw.height)
    scaled=raw.resize((round(raw.width*factor),round(raw.height*factor)),Image.Resampling.NEAREST)
    im.alpha_composite(scaled,(round(x+(w-scaled.width)/2),round(y+(w-scaled.height)/2)))

def recipe_items(name, recipe):
    if name=="netherite_backpack":
        assert recipe["type"]=="sophisticatedbackpacks:smithing_backpack_upgrade"
        return [recipe[k].get("item",recipe[k].get("tag")) for k in ("template","base","addition")]
    assert recipe["type"] in ("sophisticatedbackpacks:backpack_upgrade","sophisticatedbackpacks:basic_backpack")
    pattern=recipe["pattern"]; assert len(pattern)==3 and all(len(x)==3 for x in pattern)
    return [None if c==" " else recipe["key"][c].get("item",recipe["key"][c].get("tag"))
            for row in pattern for c in row]

def card(name, recipe, items, icons, lang='pl'):
    img=Image.new("RGBA",(1200,720),COL["bg"]);d=ImageDraw.Draw(img)
    d.rounded_rectangle((19,18,1180,702),radius=30,fill=COL["edge"])
    d.rounded_rectangle((34,33,1165,687),radius=20,fill=COL["paper"])
    def centered(text,y,size,bold=False):
        f=font(size,bold)
        bb=d.textbbox((0,0),text,font=f)
        d.text(((1200-(bb[2]-bb[0]))//2,y),text,font=f,fill=COL["ink"])
    centered((NAMES_EN if lang=='en' else NAMES)[name],65,43,True)
    is_smith=name=="netherite_backpack"
    centered(("Smithing Table — Upgrade" if is_smith else "Crafting Table — 3 × 3") if lang=="en" else ("Stół kowalski — ulepszenie" if is_smith else "Stół craftingowy — 3 × 3"),122,22)
    d.line((73,158,1127,158),fill=COL["shadow"],width=3)
    def panel(x,y,size):
        d.rounded_rectangle((x,y,x+size-8,y+size-8),radius=8,fill=COL["slot"],outline=COL["shadow"],width=3)
    if is_smith:
        for k,item in enumerate(items):
            x=106+k*126; panel(x,295,111); icon(img,icons,item,x+10,305,82)
        for x,text in (((104,"Template"),(238,"Backpack"),(357,"Material")) if lang=="en" else ((104,"Szablon"),(238,"Plecak"),(357,"Materiał"))):
            d.text((x,254),text,font=font(16),fill=COL["ink"])
    else:
        for k,item in enumerate(items):
            x=126+(k%3)*112;y=184+(k//3)*112
            panel(x,y,112)
            if item:icon(img,icons,item,x+12,y+12)
    d.polygon([(574,323),(655,323),(655,296),(730,351),(655,407),(655,380),(574,380)],fill=COL["arrow"])
    x,y=820,263;panel(x,y,184)
    result=recipe["result"]["id"];icon(img,icons,result,x+28,y+28,120)
    result_label=label(result,lang)
    bb=d.textbbox((0,0),result_label,font=font(21))
    d.text((x+92-(bb[2]-bb[0])//2,y+188),result_label,font=font(21),fill=COL["ink"])
    d.line((75,548,1125,548),fill=COL["shadow"],width=3)
    d.text((85,567),"Ingredients" if lang=="en" else "Składniki",font=font(27,True),fill=COL["ink"])
    counts=collections.OrderedDict()
    for item in items:
        if item:counts[item]=counts.get(item,0)+1
    for k,(item,count) in enumerate(counts.items()):
        x,y=96+(k%3)*359,614+(k//3)*41
        icon(img,icons,item,x,y-4,33)
        t=label(item,lang)
        d.text((x+45,y-1),f"{count} × {t}" if count>1 else t,font=font(19),fill=COL["ink"])
    return img.convert("RGB")

def generate_bilingual(destination_pl, destination_en):
    models,textures,recipes=load_assets()
    icons=get_icons(models,textures)
    destinations=[Path(destination_pl),Path(destination_en)]
    for destination in destinations: destination.mkdir(parents=True,exist_ok=True)
    outputs=[{},{}]
    for name in IDS:
        items=recipe_items(name,recipes[name])
        for i,lang in enumerate(("pl","en")):
            result=card(name,recipes[name],items,icons,lang)
            filename=destinations[i]/(name+".png")
            result.save(filename,optimize=True)
            raw=filename.read_bytes()
            outputs[i][name]="data:image/png;base64,"+base64.b64encode(raw).decode("ascii")
            print(f"Rendered {name} {lang}: {len(raw)} bytes")
    return tuple(outputs)

def generate(destination):
    return generate_bilingual(destination,Path(destination).parent/"_en")[0]

if __name__=="__main__":
    import sys
    generate(Path(sys.argv[1]) if len(sys.argv)>1 else Path("_site/assets/crafting/backpacks"))

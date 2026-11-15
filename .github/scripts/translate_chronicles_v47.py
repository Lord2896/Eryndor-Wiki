#!/usr/bin/env python3
"""Prepare a REVIEWABLE English draft of eight Eryndor Chronicles.
Never touches Polish articles or publishes automatically.
Uses public Google Translate endpoint for a first-pass draft only.
Maintains HTML structure, links and lore artwork markers.
"""
import json
import re
import sys
import time
import random
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString
import requests

HERE=Path(__file__).resolve().parents[2]
PL=HERE/"articles.json"
EN=HERE/"translations"/"en.json"
IDS=[
 "chronicles-story-1","chronicles-story-2","chronicles-story-3",
 "chronicles-story-4","chronicles-story-5","chronicles-story-6",
 "chronicles-peoples","chronicles-introduction"
]
TITLES={
 "chronicles-story-1":"Chronicle I — The Three Guardians",
 "chronicles-story-2":"Chronicle II — A Century Beneath a Foreign Banner",
 "chronicles-story-3":"Chronicle III — When the Forge Burns Again",
 "chronicles-story-4":"Chronicle IV — The Uprising of Khar-Durim",
 "chronicles-story-5":"Chronicle V — Haldrek's Three Blows",
 "chronicles-story-6":"Chronicle VI — The Fall of the Empire",
 "chronicles-peoples":"Peoples of Eryndor",
 "chronicles-introduction":"Introduction to Eryndor",
 "chronicles-trials":"The Trial Path of Eryndor"
}
SUMMARIES={
 "chronicles-story-1":"The full legend of Groudon, Xerneas and Zamazenta and Eryndor's beginnings.",
 "chronicles-story-2":"Vaelthar's conquest of Khar-Durim and nearly a century of elven occupation.",
 "chronicles-story-3":"Thorgrim unites the clans, and the fire of the First Forge ignites an uprising.",
 "chronicles-story-4":"The great uprising, the liberation of Khar-Durim and the final clash with the occupiers.",
 "chronicles-story-5":"The expedition to Sah'Rava, the siege of the Citadel and Haldrek's duel with Vaelthar.",
 "chronicles-story-6":"The end of the elven empire and the war's consequences for Eryndor's three islands.",
 "chronicles-peoples":"The four clans of Khar-Durim, the human kingdom of Valoria and the peoples of Sah'Rava.",
 "chronicles-introduction":"The beginning of a journey through three islands, their history and their people's memories."
}
SEARCH={
 "chronicles-story-1":"three guardians groudon xerneas zamazenta prophecy legend origins Eryndor",
 "chronicles-story-2":"century foreign banner occupation enslavement Khar-Durim elves Vaelthar",
 "chronicles-story-3":"forge burns again Thorgrim Entei First Forge four clans",
 "chronicles-story-4":"uprising Khar-Durim Thorgrim Borgrim Haldrek Varkun gate liberation",
 "chronicles-story-5":"Haldrek three blows Citadel Sah'Rava Vaelthar Thorgrim war",
 "chronicles-story-6":"fall of the empire Sah'Rava Vaelthar dwarves war Thorgrim Valoria",
 "chronicles-peoples":"peoples of Eryndor four clans dwarves humans Valoria elves Nekhari Zashara goblins",
 "chronicles-introduction":"introduction Eryndor archipelago three islands Khar-Durim Valoria Sah'Rava newcomer legend"
}
TAGS={
 "chronicles-story-1":["Chronicle I","Legend","Guardians"],
 "chronicles-story-2":["Chronicle II","Vaelthar","Occupation"],
 "chronicles-story-3":["Chronicle III","Thorgrim","Entei"],
 "chronicles-story-4":["Chronicle IV","Uprising","Khar-Durim"],
 "chronicles-story-5":["Chronicle V","Haldrek","Vaelthar"],
 "chronicles-story-6":["Chronicle VI","Empire","Sah'Rava"],
 "chronicles-peoples":["Peoples","Clans","Kingdoms"],
 "chronicles-introduction":["World","History","Travel"]
}
session=requests.Session()
session.headers.update({"User-Agent":"Mozilla/5.0 (compatible; EryndorWiki-TranslationDraft/1.0)"})
CACHE=HERE/"translations"/".v47_cache.json"
cache=json.loads(CACHE.read_text(encoding="utf8")) if CACHE.exists() else {}
request_count=0
def translate_api(text):
    global request_count
    if not text.strip(): return text
    if text in cache: return cache[text]
    params={"client":"gtx","sl":"pl","tl":"en","dt":"t","q":text}
    err=None
    for attempt in range(7):
        try:
            response=session.get("https://translate.googleapis.com/translate_a/single",params=params,timeout=45)
            response.raise_for_status()
            result=response.json()
            translation="".join(row[0] or "" for row in result[0])
            if not translation.strip():raise ValueError("Empty translation")
            cache[text]=translation
            request_count+=1
            if request_count%20==0:
                CACHE.write_text(json.dumps(cache,ensure_ascii=False),encoding="utf8")
                print(f"Translated {request_count} new batches; cache entries {len(cache)}",flush=True)
            time.sleep(0.15)
            return translation
        except Exception as exc:
            err=exc
            time.sleep(min(16,1.5*(2**attempt)))
    raise RuntimeError(f"Translation endpoint failed: {str(err)[:200]}")
# A simple separator usually survives Google Translate intact.
SEP="\n\n###\n\n"
def translated_nodes(texts):
    if not texts: return []
    if len(texts)==1:
        return [translate_api(texts[0])]
    joined=SEP.join(texts)
    try:
        translated=translate_api(joined)
        parts=re.split(r"\s*#{3}\s*",translated)
        if len(parts)==len(texts) and all(x.strip() for x in parts):
            return [x.strip() for x in parts]
    except Exception:
        pass
    mid=len(texts)//2
    return translated_nodes(texts[:mid])+translated_nodes(texts[mid:])
def convert_content(src):
    soup=BeautifulSoup(src,"html.parser")
    nodes=[]
    for node in soup.descendants:
        if not isinstance(node,NavigableString):continue
        if not node.strip() or "@@LORE_IMAGE:" in str(node):continue
        if node.parent.name in ("script","style"):continue
        nodes.append(node)
    print("Text nodes",len(nodes),flush=True)
    k=0
    while k<len(nodes):
        batch=[];j=k;total=0
        while j<len(nodes) and len(batch)<10:
            s=str(nodes[j])
            if batch and total+len(s)>1400:break
            batch.append(s);total+=len(s);j+=1
        result=translated_nodes(batch)
        assert len(result)==len(batch)
        for node,txt in zip(nodes[k:j],result):
            node.replace_with(NavigableString(txt))
        k=j
    for btn in soup.find_all("button"):
        target=btn.get("data-go")
        if target in TITLES:
            original_btn=re.search(r'<button[^>]*data-go="'+re.escape(target)+r'"[^>]*>(.*?)</button>',src)
            original_txt=original_btn.group(1) if original_btn else ""
            prefix="← " if ("←" in original_txt or original_txt.strip().startswith("←")) else ""
            suffix=" →" if ("→" in original_txt or "↗" in original_txt) and not prefix else ""
            btn.string=prefix+TITLES[target]+suffix
    result=str(soup)
    assert len(re.findall(r"<p(?:\s|>)",result))==len(re.findall(r"<p(?:\s|>)",src))
    assert len(re.findall(r"<h3>",result))==len(re.findall(r"<h3>",src))
    assert len(re.findall(r"<h4>",result))==len(re.findall(r"<h4>",src))
    assert len(re.findall(r"<button\b",result))==len(re.findall(r"<button\b",src))
    assert sorted(re.findall(r'data-go="([^"]+)"',result))==sorted(re.findall(r'data-go="([^"]+)"',src))
    assert sorted(re.findall(r"@@LORE_IMAGE:[^@]+@@",result))==sorted(re.findall(r"@@LORE_IMAGE:[^@]+@@",src))
    assert '<script' not in result and len(result)<350000
    return result
def main():
    pl=json.loads(PL.read_text(encoding="utf8"))
    en=json.loads(EN.read_text(encoding="utf8"))
    assert pl["revision"]==46 and en["revision"]==15
    originals={a["id"]:a for a in pl["articles"]}
    for id in IDS:
        assert id not in en["articles"],f"Won't overwrite existing EN: {id}"
        article=originals[id]
        print("TRANSLATING",id,len(article["content"]),"PL chars",flush=True)
        translated=convert_content(article["content"])
        en["articles"][id]={
           "sourceUpdatedAt":article["updatedAt"],
           "title":TITLES[id],
           "summary":SUMMARIES[id],
           "tags":TAGS[id],
           "search":SEARCH[id],
           "content":translated
        }
        print("DONE",id,len(translated),"EN chars",flush=True)
        EN.write_text(json.dumps(en,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
        CACHE.write_text(json.dumps(cache,ensure_ascii=False),encoding="utf8")
    en["revision"]=16
    EN.write_text(json.dumps(en,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print("SUCCESS: 8 translations added; EN revision 16; 29 EN entries.",flush=True)
if __name__=="__main__":
    main()

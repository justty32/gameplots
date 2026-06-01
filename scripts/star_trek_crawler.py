# -*- coding: utf-8 -*-
"""
Specialized Memory Alpha (Star Trek) narrative crawler for GamePlots.
Based on fandom_crawler.py.
"""
import os
import re
import sys
import time
import json
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "GamePlots-research-bot/1.0 (contact: guanyu.lu@teco.com.tw) python-requests"
}
DELAY = 0.05  # Increased slightly for stability

CONFIG = {
    "domain": "memory-alpha.fandom.com",
    "work": "Star_Trek",
    "buckets": [
        ("productions",         ["Series", "Films", "Television series"]),
        ("characters_main",     ["Main characters", "Commanding officers"]),
        ("characters_recurring", ["Recurring characters"]),
        ("species",             ["Species", "Sentient species", "Humanoids"]),
        ("factions",            ["Organizations", "Governments", "Military organizations"]),
        ("technology",          ["Technology", "Starship classes", "Starships", "Weapons"]),
        ("geography",           ["Planets", "Quadrants", "Space stations", "Locations"]),
        ("lore_history",        ["History", "Timeline", "Conflicts", "Wars"]),
        ("science",             ["Science", "Medical science", "Physics"]),
    ],
}

def api_get(api_url, params, retries=3):
    p = dict(params)
    p["format"] = "json"
    last = None
    for attempt in range(retries):
        try:
            r = requests.get(api_url, params=p, headers=HEADERS, timeout=30)
            if r.status_code in (502, 503, 504, 429):
                raise requests.HTTPError("%s transient" % r.status_code)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            last = e
            time.sleep(2 * (attempt + 1))
    raise last

def category_members(api_url, cat):
    titles = []
    cont = {}
    while True:
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": "Category:" + cat,
            "cmlimit": "500",
            "cmnamespace": "0",
        }
        params.update(cont)
        data = api_get(api_url, params)
        for m in data.get("query", {}).get("categorymembers", []):
            titles.append(m["title"])
        if "continue" in data:
            cont = data["continue"]
            time.sleep(0.5)
        else:
            break
    return titles

def page_plaintext(api_url, title):
    data = api_get(api_url, {
        "action": "parse",
        "page": title,
        "prop": "text",
        "redirects": "1",
    })
    if "error" in data:
        return None
    html = data.get("parse", {}).get("text", {}).get("*", "")
    if not html:
        return None
    soup = BeautifulSoup(html, "html.parser")
    drop_selectors = [
        "script", "style", "table.navbox", ".navbox", ".toc", ".mw-editsection",
        ".printfooter", ".noprint", ".mw-references-wrap", "#toc",
        ".portable-infobox .pi-image", ".reference", ".gallery", ".asbox"
    ]
    for sel in drop_selectors:
        for el in soup.select(sel):
            el.decompose()
    text = soup.get_text(separator="\n", strip=True)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def crawl():
    domain = CONFIG["domain"]
    api_url = "https://%s/api.php" % domain
    out_dir = os.path.join("working", CONFIG["work"], "raw")
    buckets = CONFIG["buckets"]
    os.makedirs(out_dir, exist_ok=True)

    all_cats = []
    for _b, cats in buckets:
        all_cats.extend(cats)

    print(f"Listing category members from {domain} ...")
    title_to_cats = {}
    for cat in all_cats:
        try:
            members = category_members(api_url, cat)
        except Exception as e:
            print(f"  ! category '{cat}' failed: {e}")
            continue
        print(f"  [{len(members):3d}] {cat}")
        for t in members:
            title_to_cats.setdefault(t, set()).add(cat)

    title_to_bucket = {}
    for title, cats in title_to_cats.items():
        for bucket_name, bucket_cats in buckets:
            if cats.intersection(bucket_cats):
                title_to_bucket[title] = bucket_name
                break

    total = len(title_to_bucket)
    print(f"\nSelected {total} unique pages across {len(set(title_to_bucket.values()))} buckets.\n")

    # Limit for safety during first run if needed, but here we go for it.
    # To avoid huge downloads, we could cap it, but let's try to be selective with categories.
    
    bucket_order = {name: i for i, (name, _c) in enumerate(buckets)}
    ordered = sorted(title_to_bucket.items(),
                     key=lambda kv: (bucket_order[kv[1]], kv[0]))

    bucket_files = {}
    manifest = []
    fetched = 0
    failed = []
    
    # Safety: do not exceed 500 pages in one go to stay under 50MB roughly
    MAX_PAGES = 500 
    
    for title, bucket in ordered:
        if fetched >= MAX_PAGES:
            print(f"\nReached MAX_PAGES limit ({MAX_PAGES}). Stopping.")
            break
            
        try:
            text = page_plaintext(api_url, title)
        except Exception as e:
            print(f"  ! fetch failed '{title}': {e}")
            failed.append(title)
            time.sleep(DELAY)
            continue
        if not text:
            failed.append(title)
            time.sleep(DELAY)
            continue
            
        fh = bucket_files.get(bucket)
        if fh is None:
            fh = open(os.path.join(out_dir, bucket + ".txt"), "w",
                      encoding="utf-8")
            bucket_files[bucket] = fh
        fh.write("\n" + "=" * 70 + "\n")
        fh.write(f"PAGE: {title}\n")
        fh.write(f"CATEGORIES: {', '.join(sorted(title_to_cats[title]))}\n")
        fh.write(f"URL: https://{domain}/wiki/{title.replace(' ', '_')}\n")
        fh.write("=" * 70 + "\n\n")
        fh.write(text + "\n")
        manifest.append({"title": title, "bucket": bucket,
                         "categories": sorted(title_to_cats[title]),
                         "chars": len(text)})
        fetched += 1
        if fetched % 25 == 0:
            print(f"  ... {fetched}/{min(total, MAX_PAGES)} fetched")
        time.sleep(DELAY)

    for fh in bucket_files.values():
        fh.close()

    with open(os.path.join(out_dir, "_manifest.json"), "w",
              encoding="utf-8") as f:
        json.dump({"fetched": fetched, "failed": failed, "pages": manifest},
                  f, ensure_ascii=False, indent=2)

    print(f"\nDONE. {fetched} pages fetched, {len(failed)} failed.")
    total_bytes = 0
    for name in sorted(bucket_files):
        p = os.path.join(out_dir, name + ".txt")
        sz = os.path.getsize(p)
        total_bytes += sz
        print(f"  {name + '.txt':-22s} {sz / 1024.0:8.1f} KB")
    print(f"  TOTAL {total_bytes / 1048576.0:.2f} MB")

if __name__ == "__main__":
    crawl()

# -*- coding: utf-8 -*-
"""
Fall from Heaven (fallfromheaven.fandom.com) crawler.

Scope: 敘事 + 陣營機制 (narrative + faction mechanics) — selected via category
membership, NOT the whole 1341-article wiki (pure-stat pages are skipped).

Strategy:
  1. For each INCLUDE category, list its ns=0 members via MediaWiki API.
  2. Union titles; assign each to ONE semantic bucket (priority order below).
  3. Fetch rendered HTML per page (action=parse&prop=text), strip to plain text.
  4. Append into working/Fall_from_Heaven/raw/<bucket>.txt with a header per page.

Polite: custom UA, 0.4s between requests. Output is plain prose only.
"""
import os
import re
import time
import json
import requests
from bs4 import BeautifulSoup

API = "https://fallfromheaven.fandom.com/api.php"
HEADERS = {
    "User-Agent": "GamePlots-research-bot/1.0 (contact: guanyu.lu@teco.com.tw) python-requests"
}
OUT_DIR = os.path.join("working", "Fall_from_Heaven", "raw")
DELAY = 0.4  # seconds between content fetches

# Bucket priority: a page lands in the FIRST bucket whose category list it matches.
# Narrative-heavy buckets come first so e.g. a Leader who is also an Elven Unit
# is filed under leaders, not units.
BUCKETS = [
    ("lore",            ["Lore", "On the Nature of Magic"]),
    ("gods",            ["Gods"]),
    ("religion",        ["Religion", "Religious Shrines", "Religious Techs",
                         "Religious Hero Units"]),
    ("races",           ["Races"]),
    ("civilizations",   ["Civilizations", "Sides", "Civilization Trait"]),
    ("leaders",         ["Leaders"]),
    ("heroes",          ["Hero Units"]),
    ("scenarios",       ["Scenarios", "Age of Ice (scenario)",
                         "Age of Ice scenario"]),
    ("events",          ["Armageddon Events"]),
    ("items",           ["Items"]),
    ("wonders",         ["World Wonders", "National Wonders", "Unique Features"]),
    ("world_spells",    ["World Spells", "Rituals"]),
    ("alignment_traits",["Alignment", "Traits", "Victory"]),
    ("units_angel",     ["Angel Units"]),
    ("units_demon",     ["Demon Units"]),
    ("units_infernal",  ["Infernal"]),
    ("units_undead",    ["Undead Units"]),
    ("units_vampire",   ["Vampire Units"]),
    ("units_werewolf",  ["Werewolf Units"]),
    ("units_dwarven",   ["Dwarven Units"]),
    ("units_elven",     ["Elven Units"]),
    ("units_orc",       ["Orc Units"]),
    ("units_golem",     ["Golem Units"]),
    ("units_dragon",    ["Dragon Units"]),
    ("units_elemental", ["Elemental Units"]),
    ("units_beast",     ["Beast Units", "Animal Units"]),
    ("units_summoned",  ["Summoned Units", "Summons"]),
    ("units_immortal",  ["Immortal"]),
    ("units_disciple",  ["Disciple Units"]),
]

ALL_INCLUDE_CATS = []
for _b, _cats in BUCKETS:
    ALL_INCLUDE_CATS.extend(_cats)


def api_get(params):
    p = dict(params)
    p["format"] = "json"
    r = requests.get(API, params=p, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()


def category_members(cat):
    """All ns=0 page titles in a category (handles continuation)."""
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
        data = api_get(params)
        for m in data.get("query", {}).get("categorymembers", []):
            titles.append(m["title"])
        if "continue" in data:
            cont = data["continue"]
            time.sleep(0.3)
        else:
            break
    return titles


def page_plaintext(title):
    """Fetch rendered HTML for a page and reduce to plain narrative text."""
    data = api_get({
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
    # Drop non-narrative chrome
    drop_selectors = [
        "script", "style", "table.navbox", ".navbox", ".toc", ".mw-editsection",
        ".printfooter", ".noprint", ".mw-references-wrap", "#toc",
        ".portable-infobox .pi-image", ".reference",
    ]
    for sel in drop_selectors:
        for el in soup.select(sel):
            el.decompose()
    text = soup.get_text(separator="\n", strip=True)
    # Collapse 3+ blank lines to one
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def sanitize_anchor(title):
    return title


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    # 1. Gather titles per category
    print("Listing category members...")
    title_to_cats = {}
    for cat in ALL_INCLUDE_CATS:
        try:
            members = category_members(cat)
        except Exception as e:
            print("  ! category '%s' failed: %s" % (cat, e))
            continue
        print("  [%3d] %s" % (len(members), cat))
        for t in members:
            title_to_cats.setdefault(t, set()).add(cat)

    # 2. Assign each title to one bucket by priority
    title_to_bucket = {}
    for title, cats in title_to_cats.items():
        for bucket_name, bucket_cats in BUCKETS:
            if cats.intersection(bucket_cats):
                title_to_bucket[title] = bucket_name
                break

    total = len(title_to_bucket)
    print("\nSelected %d unique pages across %d buckets.\n" % (
        total, len(set(title_to_bucket.values()))))

    # 3. Fetch + bucket
    bucket_files = {}
    manifest = []
    fetched = 0
    failed = []
    # Stable order: bucket priority, then title
    bucket_order = {name: i for i, (name, _c) in enumerate(BUCKETS)}
    ordered = sorted(title_to_bucket.items(),
                     key=lambda kv: (bucket_order[kv[1]], kv[0]))

    for title, bucket in ordered:
        try:
            text = page_plaintext(title)
        except Exception as e:
            print("  ! fetch failed '%s': %s" % (title, e))
            failed.append(title)
            time.sleep(DELAY)
            continue
        if not text:
            failed.append(title)
            time.sleep(DELAY)
            continue
        fh = bucket_files.get(bucket)
        if fh is None:
            fh = open(os.path.join(OUT_DIR, bucket + ".txt"), "w",
                      encoding="utf-8")
            bucket_files[bucket] = fh
        fh.write("\n" + "=" * 70 + "\n")
        fh.write("PAGE: %s\n" % title)
        fh.write("CATEGORIES: %s\n" % ", ".join(sorted(title_to_cats[title])))
        fh.write("URL: https://fallfromheaven.fandom.com/wiki/%s\n"
                 % title.replace(" ", "_"))
        fh.write("=" * 70 + "\n\n")
        fh.write(text + "\n")
        manifest.append({"title": title, "bucket": bucket,
                         "categories": sorted(title_to_cats[title]),
                         "chars": len(text)})
        fetched += 1
        if fetched % 25 == 0:
            print("  ... %d/%d fetched" % (fetched, total))
        time.sleep(DELAY)

    for fh in bucket_files.values():
        fh.close()

    with open(os.path.join(OUT_DIR, "_manifest.json"), "w",
              encoding="utf-8") as f:
        json.dump({"fetched": fetched, "failed": failed,
                   "pages": manifest}, f, ensure_ascii=False, indent=2)

    print("\nDONE. %d pages fetched, %d failed." % (fetched, len(failed)))
    if failed:
        print("Failed: %s" % ", ".join(failed[:30]))
    # report sizes
    total_bytes = 0
    for name in sorted(bucket_files):
        p = os.path.join(OUT_DIR, name + ".txt")
        sz = os.path.getsize(p)
        total_bytes += sz
        print("  %-20s %8.1f KB" % (name + ".txt", sz / 1024.0))
    print("  TOTAL %.2f MB" % (total_bytes / 1048576.0))


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
Generic Fandom (MediaWiki) narrative crawler for GamePlots.

Scope philosophy: 敘事 + 陣營機制 — select pages by category membership, skip
pure-stat / image / template pages. Each page is reduced to plain narrative
text and appended to a semantic bucket .txt under working/<work>/raw/.

Usage:
    python scripts/fandom_crawler.py <config_name>

Add new wikis by appending to CONFIGS. Each config:
    domain  : fandom subdomain host
    work    : working/<work>/raw output folder name
    buckets : ordered [(bucket_name, [category, ...]), ...]
              a page lands in the FIRST bucket whose categories it matches.
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
DELAY = 0.15  # seconds between content fetches (single serial crawl)


CONFIGS = {
    "endless_legend": {
        "domain": "endlesslegend.fandom.com",
        "work": "Endless_Legend",
        "buckets": [
            # cross-cutting narrative pulled out first
            ("lore",                ["Lore"]),
            ("heroes",              ["Heroes"]),
            ("guardians",           ["Guardians"]),
            ("urkans",              ["Urkans"]),
            ("factions_overview",   ["Factions", "Major Factions",
                                     "Minor Factions"]),
            # per-faction sweep (units / buildings / faction page)
            ("faction_allayi",        ["Allayi"]),
            ("faction_ardent_mages",  ["Ardent Mages"]),
            ("faction_broken_lords",  ["Broken Lords"]),
            ("faction_cultists",      ["Cultists"]),
            ("faction_drakken",       ["Drakken"]),
            ("faction_forgotten",     ["Forgotten"]),
            ("faction_kapaku",        ["Kapaku"]),
            ("faction_mezari",        ["Mezari"]),
            ("faction_morgawr",       ["Morgawr"]),
            ("faction_mykara",        ["Mykara"]),
            ("faction_necrophages",   ["Necrophages"]),
            ("faction_roving_clans",  ["Roving Clans"]),
            ("faction_vaulters",      ["Vaulters"]),
            ("faction_wild_walkers",  ["Wild Walkers"]),
            ("traits",              ["Traits"]),
            ("units_other",         ["Units", "Cavalry Units", "Flying Units",
                                     "Infantry Units", "Naval Units",
                                     "Ranged Units", "Support Units"]),
        ],
    },
    "age_of_wonders": {
        # Classic trilogy wiki: AoW1, AoW II: The Wizard's Throne, Shadow Magic.
        "domain": "ageofwonders.fandom.com",
        "work": "Age_of_Wonders",
        "buckets": [
            ("lore",            ["Lore", "Out-of-game lore texts",
                                 "Game Concepts", "Terminology"]),
            ("story_characters",["Story characters"]),
            ("heroes",          ["Heroes"]),
            ("races",           ["Races", "Age of Wonders races",
                                 "Age of Wonders II races",
                                 "Age of Wonders: Shadow Magic races"]),
            ("factions",        ["Factions and organizations",
                                 "Kingdoms and sovereign states",
                                 "Organization"]),
            ("locations",       ["Locations"]),
            ("campaigns",       ["Campaign scenarios",
                                 "Age of Wonders campaign",
                                 "Age of Wonders campaign scenarios",
                                 "Age of Wonders II campaign scenarios",
                                 "Age of Wonders: Shadow Magic campaign",
                                 "Age of Wonders: Shadow Magic campaign scenarios",
                                 "Campaign heroes"]),
            ("creatures",       ["Dragons", "Elementals", "Creatures",
                                 "Machines", "Humanoids"]),
            ("items",           ["Items", "Age of Wonders items"]),
            # per-race units (faction mechanics)
            ("units_azrac",     ["Azrac Units"]),
            ("units_dark_elf",  ["Dark Elf Units"]),
            ("units_dwarf",     ["Dwarf Units"]),
            ("units_elf",       ["Elf Units"]),
            ("units_frostling", ["Frostling Units"]),
            ("units_goblin",    ["Goblin Units"]),
            ("units_halfling",  ["Halfling Units"]),
            ("units_highman",   ["Highman Units"]),
            ("units_human",     ["Human Units"]),
            ("units_lizardman", ["Lizardman Units"]),
            ("units_orc",       ["Orc Units"]),
            ("units_undead",    ["Undead Units"]),
            ("units_aow2",      ["Age of Wonders II units"]),
        ],
    },
    "stormlight": {
        # Brandon Sanderson novel series (not a game). "陣營機制" maps to
        # narrative entities: characters / places / orders / world concepts.
        "domain": "stormlightarchive.fandom.com",
        "work": "Stormlight_Archive",
        "buckets": [
            ("gods_heralds", ["Gods", "Heralds", "Deity"]),
            ("radiant_orders", ["Bondsmith", "Dustbringer", "Edgedancer",
                                "Elsecaller", "Lightweaver", "Releaser",
                                "Skybreaker", "Stoneward", "Truthwatcher",
                                "Willshaper", "Windrunner"]),
            ("cosmere_concepts", ["Cosmere", "Concepts", "Forms of Power",
                                  "Dawnshards", "Surges", "Investiture"]),
            ("events_eras", ["Events and Eras", "Battles"]),
            ("groups", ["Groups", "Cults", "Ghostblood"]),
            ("fabrials", ["Fabrials", "Gemstones"]),
            ("creatures", ["Creatures", "Flora and Fauna",
                           "Fauna of Roshar", "Flora of Roshar"]),
            ("places", ["Cities", "Geography", "Dawncities"]),
            ("characters", ["Characters"]),
        ],
    },
    "diablo": {
        # Huge wiki (16k+ articles) spanning D1-D4 + Immortal + novels.
        # Narrative scope ONLY: skip the 338-page Demons bestiary, item/stat
        # pages, and 21k images. Story/lore/characters/factions/places.
        "domain": "diablo.fandom.com",
        "work": "Diablo",
        "buckets": [
            ("lore", ["Lore", "Religion"]),
            ("angels", ["Angels", "Angiris Council", "Angelic orders"]),
            ("prime_evils", ["Prime Evils", "Lesser Evils"]),
            ("factions", ["Horadrim", "Barbarian Tribes", "Cults",
                          "Archmages"]),
            ("locations", ["Locations"]),
            ("nephalem", ["Nephalem"]),
            ("characters", ["Characters"]),
        ],
    },
    "malazan": {
        # Malazan Book of the Fallen (Erikson/Esslemont novels). No single
        # "Characters" cat — people are grouped by race/affiliation. Skip the
        # huge Book-covers / Fan-art / Advent-calendar image-category noise.
        "domain": "malazan.fandom.com",
        "work": "Malazan",
        "buckets": [
            ("gods_ascendants", ["Ascendants", "Elder Gods", "Gods",
                                 "Azathanai"]),
            ("faction_bridgeburners", ["Bridgeburners"]),
            ("faction_bonehunters", ["Bonehunters"]),
            ("faction_crimson_guard", ["Crimson Guard", "Avowed",
                                       "Disavowed"]),
            ("faction_claw", ["Claw"]),
            ("race_tiste", ["Tiste"]),
            ("race_tlan_imass", ["T'lan Imass", "Imass"]),
            ("race_jaghut", ["Jaghut"]),
            ("race_forkrul_assail", ["Forkrul Assail"]),
            ("race_barghast", ["Barghast"]),
            ("race_human", ["Humans", "Human"]),
            ("creatures", ["Creatures", "D'ivers", "Eleint"]),
            ("magic", ["Warrens", "Deck of Dragons", "Azath Houses"]),
            ("events", ["Battles", "Events"]),
            ("places", ["Cities", "Continents"]),
        ],
    },
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
            time.sleep(1.5 * (attempt + 1))
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
            time.sleep(0.3)
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
        ".portable-infobox .pi-image", ".reference",
    ]
    for sel in drop_selectors:
        for el in soup.select(sel):
            el.decompose()
    text = soup.get_text(separator="\n", strip=True)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def crawl(config):
    domain = config["domain"]
    api_url = "https://%s/api.php" % domain
    out_dir = os.path.join("working", config["work"], "raw")
    buckets = config["buckets"]
    os.makedirs(out_dir, exist_ok=True)

    all_cats = []
    for _b, cats in buckets:
        all_cats.extend(cats)

    print("Listing category members from %s ..." % domain)
    title_to_cats = {}
    for cat in all_cats:
        try:
            members = category_members(api_url, cat)
        except Exception as e:
            print("  ! category '%s' failed: %s" % (cat, e))
            continue
        print("  [%3d] %s" % (len(members), cat))
        for t in members:
            title_to_cats.setdefault(t, set()).add(cat)

    title_to_bucket = {}
    for title, cats in title_to_cats.items():
        for bucket_name, bucket_cats in buckets:
            if cats.intersection(bucket_cats):
                title_to_bucket[title] = bucket_name
                break

    total = len(title_to_bucket)
    print("\nSelected %d unique pages across %d buckets.\n" % (
        total, len(set(title_to_bucket.values()))))

    bucket_order = {name: i for i, (name, _c) in enumerate(buckets)}
    ordered = sorted(title_to_bucket.items(),
                     key=lambda kv: (bucket_order[kv[1]], kv[0]))

    bucket_files = {}
    manifest = []
    fetched = 0
    failed = []
    for title, bucket in ordered:
        try:
            text = page_plaintext(api_url, title)
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
            fh = open(os.path.join(out_dir, bucket + ".txt"), "w",
                      encoding="utf-8")
            bucket_files[bucket] = fh
        fh.write("\n" + "=" * 70 + "\n")
        fh.write("PAGE: %s\n" % title)
        fh.write("CATEGORIES: %s\n" % ", ".join(sorted(title_to_cats[title])))
        fh.write("URL: https://%s/wiki/%s\n" % (domain, title.replace(" ", "_")))
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

    with open(os.path.join(out_dir, "_manifest.json"), "w",
              encoding="utf-8") as f:
        json.dump({"fetched": fetched, "failed": failed, "pages": manifest},
                  f, ensure_ascii=False, indent=2)

    print("\nDONE. %d pages fetched, %d failed." % (fetched, len(failed)))
    if failed:
        print("Failed: %s" % ", ".join(failed[:30]))
    total_bytes = 0
    for name in sorted(bucket_files):
        p = os.path.join(out_dir, name + ".txt")
        sz = os.path.getsize(p)
        total_bytes += sz
        print("  %-22s %8.1f KB" % (name + ".txt", sz / 1024.0))
    print("  TOTAL %.2f MB" % (total_bytes / 1048576.0))


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in CONFIGS:
        print("Usage: python scripts/fandom_crawler.py <%s>"
              % "|".join(CONFIGS))
        sys.exit(1)
    crawl(CONFIGS[sys.argv[1]])

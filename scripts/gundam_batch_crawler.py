# -*- coding: utf-8 -*-
"""
Batch wikitext crawler for Gundam Wiki.

gundam.fandom.com is too large and slow for action=parse page-by-page. This
uses category selection from fandom_crawler.CONFIGS["gundam"], then fetches
page revisions in API batches and strips common wiki markup locally.
"""
import json
import os
import re
import time

import requests

from fandom_crawler import CONFIGS, HEADERS, api_get, category_members


BATCH_SIZE = 40
DELAY = 0.05


def strip_balanced(text, opener, closer):
    out = []
    i = 0
    depth = 0
    while i < len(text):
        if text.startswith(opener, i):
            depth += 1
            i += len(opener)
            continue
        if depth and text.startswith(closer, i):
            depth -= 1
            i += len(closer)
            continue
        if depth == 0:
            out.append(text[i])
        i += 1
    return "".join(out)


def clean_wikitext(text):
    text = re.sub(r"<ref[^>/]*/>", "", text, flags=re.I)
    text = re.sub(r"<ref[^>]*>.*?</ref>", "", text, flags=re.I | re.S)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    text = strip_balanced(text, "{{", "}}")
    text = re.sub(r"(?ms)^\{\|.*?^\|\}", "", text)
    text = re.sub(r"\[\[(?:File|Image):[^\]]+\]\]", "", text, flags=re.I)
    text = re.sub(r"\[\[Category:[^\]]+\]\]", "", text, flags=re.I)
    text = re.sub(r"\[\[[^|\]]+\|([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"'''?", "", text)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"^={2,}\s*(.*?)\s*={2,}$", r"\1", text, flags=re.M)
    text = re.sub(r"^[*#;:]+", "- ", text, flags=re.M)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunks(items, size):
    for i in range(0, len(items), size):
        yield items[i:i + size]


def revision_batch(api_url, titles):
    params = {
        "action": "query",
        "prop": "revisions",
        "rvprop": "content",
        "rvslots": "main",
        "redirects": "1",
        "titles": "|".join(titles),
        "format": "json",
    }
    r = requests.get(api_url, params=params, headers=HEADERS, timeout=60)
    r.raise_for_status()
    pages = r.json().get("query", {}).get("pages", {})
    result = {}
    for page in pages.values():
        title = page.get("title")
        revs = page.get("revisions") or []
        if not title or not revs:
            continue
        slot = revs[0].get("slots", {}).get("main", {})
        result[title] = slot.get("*", "")
    return result


def crawl():
    config = CONFIGS["gundam"]
    domain = config["domain"]
    api_url = "https://%s/api.php" % domain
    out_dir = os.path.join("working", config["work"], "raw")
    os.makedirs(out_dir, exist_ok=True)

    title_to_cats = {}
    all_cats = []
    for _bucket, cats in config["buckets"]:
        all_cats.extend(cats)

    print("Listing category members from %s ..." % domain, flush=True)
    for cat in all_cats:
        try:
            members = category_members(api_url, cat)
        except Exception as e:
            print("  ! category '%s' failed: %s" % (cat, e), flush=True)
            continue
        print("  [%4d] %s" % (len(members), cat), flush=True)
        for title in members:
            title_to_cats.setdefault(title, set()).add(cat)

    title_to_bucket = {}
    for title, cats in title_to_cats.items():
        for bucket_name, bucket_cats in config["buckets"]:
            if cats.intersection(bucket_cats):
                title_to_bucket[title] = bucket_name
                break

    bucket_order = {name: i for i, (name, _cats) in enumerate(config["buckets"])}
    ordered = sorted(title_to_bucket.items(),
                     key=lambda kv: (bucket_order[kv[1]], kv[0]))
    total = len(ordered)
    print("\nSelected %d unique pages across %d buckets.\n" %
          (total, len(set(title_to_bucket.values()))), flush=True)

    bucket_files = {}
    manifest = []
    failed = []
    fetched = 0

    for batch in chunks(ordered, BATCH_SIZE):
        titles = [title for title, _bucket in batch]
        try:
            raw_pages = revision_batch(api_url, titles)
        except Exception as e:
            print("  ! batch failed %s: %s" % (titles[:3], e), flush=True)
            failed.extend(titles)
            time.sleep(1.0)
            continue

        for title, bucket in batch:
            raw = raw_pages.get(title, "")
            text = clean_wikitext(raw)
            if not text:
                failed.append(title)
                continue
            fh = bucket_files.get(bucket)
            if fh is None:
                fh = open(os.path.join(out_dir, bucket + ".txt"), "w",
                          encoding="utf-8")
                bucket_files[bucket] = fh
            cats = sorted(title_to_cats[title])
            fh.write("\n" + "=" * 70 + "\n")
            fh.write("PAGE: %s\n" % title)
            fh.write("CATEGORIES: %s\n" % ", ".join(cats))
            fh.write("URL: https://%s/wiki/%s\n" %
                     (domain, title.replace(" ", "_")))
            fh.write("=" * 70 + "\n\n")
            fh.write(text + "\n")
            manifest.append({"title": title, "bucket": bucket,
                             "categories": cats, "chars": len(text)})
            fetched += 1
        if fetched % 200 < BATCH_SIZE:
            print("  ... %d/%d fetched" % (fetched, total), flush=True)
        time.sleep(DELAY)

    for fh in bucket_files.values():
        fh.close()

    with open(os.path.join(out_dir, "_manifest.json"), "w",
              encoding="utf-8") as f:
        json.dump({"fetched": fetched, "failed": failed, "pages": manifest},
                  f, ensure_ascii=False, indent=2)

    print("\nDONE. %d pages fetched, %d failed." % (fetched, len(failed)),
          flush=True)
    if failed:
        print("Failed: %s" % ", ".join(failed[:30]), flush=True)
    total_bytes = 0
    for name in sorted(bucket_files):
        path = os.path.join(out_dir, name + ".txt")
        size = os.path.getsize(path)
        total_bytes += size
        print("  %-22s %8.1f KB" % (name + ".txt", size / 1024.0),
              flush=True)
    print("  TOTAL %.2f MB" % (total_bytes / 1048576.0), flush=True)


if __name__ == "__main__":
    crawl()

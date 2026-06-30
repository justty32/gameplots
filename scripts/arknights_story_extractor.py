# -*- coding: utf-8 -*-
"""
Extract readable Arknights AVG story text from ArknightsGameData.

The raw files mix dialogue with engine commands such as [Background],
[charslot], [PlaySound]. This script keeps narrative text, speaker-tagged
dialogue, and subtitle text, then writes chapter-level text files for analysis.
"""
import json
import os
import re
from pathlib import Path


ROOT = Path("working/Arknights/raw/ArknightsGameData/zh_CN/gamedata")
STORY_DIR = ROOT / "story"
EXCEL_DIR = ROOT / "excel"
OUT_DIR = Path("working/Arknights/processed/main_story")
PRIORITY_ACTIVITY_IDS = [
    "act9d0",      # 生于黑夜
    "act13side",  # 长夜临光
    "act16side",  # 吾导先路
    "act17side",  # 愚人号
    "act18d0",    # 遗尘漫步
    "act21side",  # 叙拉古人
    "act25side",  # 孤星
    "act33side",  # 巴别塔
]


def sanitize_filename(text):
    text = re.sub(r"[\\/:*?\"<>|]", "_", text)
    text = re.sub(r"\s+", "_", text.strip())
    return text or "untitled"


def unescape_text(text):
    return (text.replace(r"\n", "\n")
                .replace(r"\"", '"')
                .replace("\\'", "'"))


def clean_avg(raw):
    lines = []
    current_speaker = None
    for raw_line in raw.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        name_match = re.match(r'^\[name="([^"]*)"\](.*)$', line, flags=re.I)
        if name_match:
            speaker = name_match.group(1).strip()
            text = name_match.group(2).strip()
            current_speaker = speaker or current_speaker
            if text:
                lines.append(f"{speaker}：{text}" if speaker else text)
            continue

        subtitle_match = re.search(r'\[Subtitle\(text="((?:\\.|[^"])*)"', line,
                                   flags=re.I)
        if subtitle_match:
            text = unescape_text(subtitle_match.group(1)).strip()
            if text:
                lines.append(text)
            continue

        decision_match = re.search(r'\[Decision\((.*)\)\]', line, flags=re.I)
        if decision_match:
            opts = re.findall(r'options?="((?:\\.|[^"])*)"',
                              decision_match.group(1))
            if opts:
                lines.append("选项：" + " / ".join(unescape_text(o) for o in opts))
            continue

        # Drop pure engine commands.
        if line.startswith("[") and line.endswith("]"):
            if re.match(r"^\[(dialog|Dialog|Delay|Blocker|Background|Camera|"
                        r"PlaySound|playsound|Sound|Music|stopmusic|charslot|"
                        r"Character|Image|Predicate|Tutorial|HEADER)", line):
                continue
            continue

        # Untagged lines are narration/stage prose in Arknights AVG scripts.
        if not line.startswith("["):
            lines.append(line)

    cleaned = []
    prev = None
    for line in lines:
        line = re.sub(r"\s+", " ", line).strip()
        if line and line != prev:
            cleaned.append(line)
            prev = line
    return "\n".join(cleaned).strip()


def load_story_review():
    with open(EXCEL_DIR / "story_review_table.json", encoding="utf-8") as f:
        return json.load(f)


def story_path(story_txt):
    return STORY_DIR / (story_txt + ".txt")


def extract_main_story():
    review = load_story_review()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    index = ["# Arknights 主線清理文本索引", ""]
    total_nodes = 0
    missing = []

    main_items = [
        (sid, data) for sid, data in review.items()
        if data.get("actType") == "MAIN_STORY"
    ]
    main_items.sort(key=lambda kv: int(kv[0].split("_")[1]))

    for sid, data in main_items:
        chapter_name = data.get("name") or sid
        nodes = sorted(data.get("infoUnlockDatas") or [],
                       key=lambda n: n.get("storySort", 0))
        out_name = f"{sid}_{sanitize_filename(chapter_name)}.txt"
        out_path = OUT_DIR / out_name
        chunks = [f"# {chapter_name} ({sid})", ""]
        written_nodes = 0

        for node in nodes:
            story_txt = node.get("storyTxt")
            if not story_txt:
                continue
            path = story_path(story_txt)
            if not path.exists():
                missing.append(story_txt)
                continue
            raw = path.read_text(encoding="utf-8")
            cleaned = clean_avg(raw)
            if not cleaned:
                continue
            code = node.get("storyCode") or ""
            name = node.get("storyName") or node.get("storyId") or story_txt
            tag = node.get("avgTag") or ""
            header = " / ".join(x for x in [code, name, tag] if x)
            chunks.append(f"## {header}")
            chunks.append("")
            chunks.append(cleaned)
            chunks.append("")
            written_nodes += 1

        out_path.write_text("\n".join(chunks).rstrip() + "\n", encoding="utf-8")
        index.append(f"- [{chapter_name}]({out_name}) — {written_nodes} 節點")
        total_nodes += written_nodes

    (OUT_DIR / "_index.md").write_text("\n".join(index) + "\n", encoding="utf-8")
    return len(main_items), total_nodes, missing


def extract_story_groups(group_ids, out_dir):
    review = load_story_review()
    out_dir.mkdir(parents=True, exist_ok=True)
    index = ["# Arknights 重點活動清理文本索引", ""]
    total_nodes = 0
    missing = []

    for sid in group_ids:
        data = review.get(sid)
        if not data:
            missing.append(sid)
            continue
        story_name = data.get("name") or sid
        nodes = sorted(data.get("infoUnlockDatas") or [],
                       key=lambda n: n.get("storySort", 0))
        out_name = f"{sid}_{sanitize_filename(story_name)}.txt"
        out_path = out_dir / out_name
        chunks = [f"# {story_name} ({sid})", ""]
        written_nodes = 0

        for node in nodes:
            story_txt = node.get("storyTxt")
            if not story_txt:
                continue
            path = story_path(story_txt)
            if not path.exists():
                missing.append(story_txt)
                continue
            cleaned = clean_avg(path.read_text(encoding="utf-8"))
            if not cleaned:
                continue
            code = node.get("storyCode") or ""
            name = node.get("storyName") or node.get("storyId") or story_txt
            tag = node.get("avgTag") or ""
            header = " / ".join(x for x in [code, name, tag] if x)
            chunks.append(f"## {header}")
            chunks.append("")
            chunks.append(cleaned)
            chunks.append("")
            written_nodes += 1

        out_path.write_text("\n".join(chunks).rstrip() + "\n", encoding="utf-8")
        index.append(f"- [{story_name}]({out_name}) — {written_nodes} 節點")
        total_nodes += written_nodes

    (out_dir / "_index.md").write_text("\n".join(index) + "\n", encoding="utf-8")
    return len(group_ids), total_nodes, missing


if __name__ == "__main__":
    chapters, nodes, missing = extract_main_story()
    print("main_chapters", chapters)
    print("nodes", nodes)
    print("missing", len(missing))
    if missing:
        print("missing_sample", ", ".join(missing[:20]))
    groups, activity_nodes, activity_missing = extract_story_groups(
        PRIORITY_ACTIVITY_IDS,
        Path("working/Arknights/processed/priority_events"),
    )
    print("priority_activity_groups", groups)
    print("priority_activity_nodes", activity_nodes)
    print("priority_activity_missing", len(activity_missing))
    if activity_missing:
        print("priority_missing_sample", ", ".join(activity_missing[:20]))

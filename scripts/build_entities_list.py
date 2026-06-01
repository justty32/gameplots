# -*- coding: utf-8 -*-
import os
import re

working_dir = "working/Star_Trek"
raw_dir = os.path.join(working_dir, "raw")
output_file = os.path.join(working_dir, "entities.md")

mapping = {
    "characters_main.txt": "## 人物 (characters)",
    "factions.txt": "## 種族/陣營 (factions)",
    "species.txt": "## 種族/陣營 (factions) - 續",
    "geography.txt": "## 地點 (places)",
    "lore_history.txt": "## 事件 (events)",
    "science.txt": "## 概念/設定 (concepts)",
    "technology.txt": "## 物品/技術 (items)",
}

with open(output_file, "w", encoding="utf-8") as out:
    out.write("# Star Trek 實體清單 (Entities Scan)\n\n")
    out.write("本清單由原始素材自動提取，作為詞條撰寫之覆蓋率檢查點。\n\n")
    
    for filename, header in mapping.items():
        filepath = os.path.join(raw_dir, filename)
        if not os.path.exists(filepath):
            continue
        
        out.write(f"{header}\n")
        titles = []
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("PAGE: "):
                    title = line[6:].strip()
                    titles.append(title)
        
        # Sort and write
        for title in sorted(set(titles)):
            out.write(f"- {title}\n")
        out.write("\n")

print(f"Entities list generated at {output_file}")

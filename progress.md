# 深化進度追蹤 (Progress)

> 目標：把先前由其他 agent 產出的「只有大綱」的詞條，逐一深化為帶人物動機、世界觀細節、主題分析、心理深度的全劇透詞條。
> 更新日期：2026-05-25

---

## 整體進度

- `results/` 內詞條檔總數（排除 index / relationship_map / narrative_analysis）：**346**
- 行數分布：
  - **< 50 行（待深化）：54**
  - 50–99 行：261
  - **100+ 行（已深化）：31**
- 累計「深化」commit 數：**67**

> 深化標準：讀同作品的 synopsis / characters / events / factions 等背景檔後，把每條目從大綱式（3–8 行）擴寫到帶「敘事意義引言 + 起源 + 機制 + 主題分析 + 懸念」的深度條目，全劇透，目標 100–150 行。每 3–5 檔 commit，每 2–3 commit push。

---

## 本輪 session 已完成（已 commit + push）

| 檔案 | commit |
| :--- | :--- |
| Tokyo_Ghoul/events.md、Final_Fantasy_XI/synopsis.md | 1532e22 |
| 諾弗蘭物語/items.md、千年之旅/places.md、星之彼端/items.md | 399663d |
| 星之彼端/places.md、瑪娜希斯回響/concepts.md、神代夢華譚/timeline.md、Lost_Ark/synopsis.md | 91f07c2 |
| Aion/places.md、Mabinogi/synopsis.md、爆裂魔女/places.md、諾弗蘭物語/concepts.md | dc5f3bd |
| Aion/items.md、Aura_Kingdom/events.md | d026494 |
| Girl_Cafe_Gun/factions.md、爆裂魔女/concepts.md | 347df8c |
| Vampir/factions.md、Granblue/items.md、Punishing_Gray_Raven/items.md、Tokyo_Ghoul/synopsis.md | 1731427 |
| Granblue_Fantasy/factions.md | cbbea6e |
| PGR/places.md、Tera/factions.md、星之彼端/concepts.md、終焉誓約/characters.md | eaca84f |

---

## 下一批待深化（< 50 行，依行數升冪）

下次從這裡接續，建議每批抓 3–4 檔，先讀同作品背景檔再寫：

### 最優先（44–45 行）
- [x] results/Punishing_Gray_Raven/places.md (44) → eaca84f
- [x] results/Tera/factions.md (44) → eaca84f
- [x] results/星之彼端/concepts.md (44) → eaca84f
- [x] results/終焉誓約/characters.md (44) → eaca84f
- [ ] results/終焉誓約/places.md (44)
- [ ] results/Black_Desert/synopsis.md (45)
- [ ] results/Brown_Dust_2/concepts.md (45)
- [ ] results/CounterSide/concepts.md (45)
- [ ] results/CounterSide/timeline.md (45)
- [ ] results/Epic_Seven/concepts.md (45)
- [ ] results/Final_Gear/items.md (45)
- [ ] results/RuneScape/concepts.md (45)
- [ ] results/Tera/timeline.md (45)
- [ ] results/Tokyo_Ghoul/characters/Suzuya_Juuzou.md (45)
- [ ] results/Tokyo_Ghoul/factions.md (45)
- [ ] results/鈴蘭之劍/factions.md (45)

### 次優先（46–47 行）
- [ ] results/Black_Desert/timeline.md (46)
- [ ] results/CrossCore/places.md (46)
- [ ] results/Final_Fantasy_XI/places/AlTaieu.md (46)
- [ ] results/Final_Gear/events.md (46)
- [ ] results/Punishing_Gray_Raven/timeline.md (46)
- [ ] results/Tokyo_Ghoul/characters/Amon_Kotaro.md (46)
- [ ] results/斯露德/timeline.md (46)
- [ ] results/星之彼端/factions.md (46)
- [ ] results/星之彼端/timeline.md (46)
- [ ] results/終焉誓約/timeline.md (46)
- [ ] results/鈴蘭之劍/characters/Caris.md (46)
- [ ] results/鈴蘭之劍/characters/Gloria.md (46)
- [ ] results/Epic_Seven/synopsis.md (47)
- [ ] results/Lineage_II/timeline.md (47)
- [ ] results/Mabinogi/places.md (47)
- [ ] results/Tokyo_Ghoul/characters/Arima_Kisho.md (47)
- [ ] results/千年之旅/characters/Mia.md (47)
- [ ] results/千年之旅/characters/Ritsu.md (47)
- [ ] results/星之彼端/synopsis.md (47)
- [ ] results/深空之眼/timeline.md (47)

### 第三批（48–49 行）
- [ ] results/ArcheAge/concepts.md (48)
- [ ] results/CrossCore/concepts.md (48)
- [ ] results/Lineage_II/items.md (48)
- [ ] results/RuneScape/characters/sliske.md (48)
- [ ] results/Vampir_Successor_of_Blood/events.md (48)
- [ ] results/千年之旅/characters/Angie.md (48)
- [ ] results/千年之旅/characters/Claire.md (48)
- [ ] results/幻象回憶/timeline.md (48)
- [ ] results/星之彼端/events.md (48)
- [ ] results/深空之眼/factions.md (48)
- [ ] results/CrossCore/items.md (49)
- [ ] results/CrossCore/timeline.md (49)
- [ ] results/Final_Fantasy_XI/concepts.md (49)
- [ ] results/Final_Fantasy_XI/items.md (49)
- [ ] results/Ragnarok_Online/synopsis.md (49)
- [ ] results/Tokyo_Ghoul/characters/Kirishima_Touka.md (49)
- [ ] results/千年之旅/timeline.md (49)
- [ ] results/瑪娜希斯回響/synopsis.md (49)

> 重新掃描待深化清單的指令：
> ```bash
> find results -name "*.md" | grep -v "index\|relationship_map\|narrative_analysis" | while read f; do lines=$(wc -l < "$f"); if [ "$lines" -lt 50 ]; then echo "$lines $f"; fi; done | sort -n
> ```

---

## 尚未著手的另一項使用者需求

- [ ] **多抓一些原始素材**（"可以的話，幫我多抓一些原始素材"）——尚未處理。執行任何爬蟲腳本前須先取得使用者授權；單次下載 < 50MB。

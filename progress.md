# 深化進度追蹤 (Progress)

> 目標：把先前由其他 agent 產出的「只有大綱」的詞條，逐一深化為帶人物動機、世界觀細節、主題分析、心理深度的全劇透詞條。
> 更新日期：2026-05-25

---

# 新作品攝入流水線（2026-05-29）

> 對應底部待辦「多抓一些原始素材」。從 fandom 等 wiki 攝入新作品、走 6-phase 流程產出詞條庫。
> 流程定義見 `CLAUDE.md`。

## 一、已完工並驗收（5 部）

標準 9 檔 = `synopsis / index / timeline / characters / factions / events / places / items / concepts`，全繁中、全劇透、斷鏈掃描歸零。

| 作品 | 類型 | 抓取頁 | 主檔 | 拆檔 | 備註 |
| :-- | :-- | --: | :-- | --: | :-- |
| Fall from Heaven | 遊戲（Civ IV mod） | 472 | 9/9 | 10 | factions 已補全 modmod 文明段落 |
| Endless Legend | 遊戲（4X） | 341 | 9/9 | 13 | 14 陣營齊全 |
| Age of Wonders | 遊戲（經典三部曲） | 297 | 9/9 | 7 | 涵蓋 AoW1/AoW2/Shadow Magic |
| Stormlight Archive | 小說（山德森） | 969 | 9/9 | 7 | 全劇透到 Wind and Truth |
| Diablo | 遊戲（系列合一） | 855 | 9/9 | 24 | D1–D4 + Immortal + 小說 |

各部產出在 `results/<作品>/`。

## 二、暫停點（依使用者 2026-05-29 指示，停在此處未繼續）

- **Malazan**（malazan.fandom.com）：raw **已抓完 1517 頁 / 0 失敗 / 4.9MB**，存於 `working/Malazan/raw/`（按神祇/派系/種族/地點分檔）。**尚未建詞條庫**（Phase 2–6 未開始）。`fandom_crawler.py` 已含 `malazan` config，可直接派 Phase 2–6 subagent。小說、全劇透。
- **Pillars of Eternity**（pillarsofeternity.fandom.com，約 13,350 篇）：**尚未抓取，無 config**。接手前先探分類設計 bucket。遊戲、敘事+陣營機制。
- **Grim Dawn**（grimdawn.fandom.com，約 4,184 篇）：同上，**尚未抓取、無 config**。遊戲。
- **Cosmere**：已放棄（fandom 站僅 26 頁殘樁；使用者否決改用 Coppermind）。`working/Cosmere` 已刪、config 已移除。

## 三、工具與設定

- **通用爬蟲** `scripts/fandom_crawler.py`：走 MediaWiki API（`action=parse` → 純文字），按分類歸 bucket，含 502/503/429 重試。
  - 用法：`python scripts/fandom_crawler.py <config>`
  - 現有 `CONFIGS`：`endless_legend`、`age_of_wonders`、`stormlight`、`diablo`、`malazan`
  - `DELAY = 0.15s`（每請求間隔）
- `scripts/ffh_crawler.py`：Fall from Heaven 專用（較早版本）。

## 四、慣例（與使用者確認）

- **抓取一次只一支**，不並行衝高網路流量；多站排隊。
- **抓取範圍**：遊戲類只取「敘事 + 陣營機制」，略過純數值/圖檔/模板頁；小說類取敘事實體。
- **全劇透**；**Diablo** 整系列合一；**Stormlight** 全劇透到最新一集。

## 五、下一步（待使用者下令「繼續」）

1. 開 Malazan 的 Phase 2–6 subagent → `results/Malazan/` → 驗收（檔案到齊 + 斷鏈掃描）。
2. 探 Pillars of Eternity 分類 → 設 config → 抓取（序列、0.15s）→ 建詞條庫。
3. 探 Grim Dawn 分類 → 設 config → 抓取 → 建詞條庫。

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
- [x] results/終焉誓約/places.md (44) → 1a76080
- [x] results/Black_Desert/synopsis.md (45) → 4a4fd32
- [x] results/Brown_Dust_2/concepts.md (45) → f1eb218
- [x] results/CounterSide/concepts.md (45) → 4a4fd32
- [x] results/CounterSide/timeline.md (45) → 4a4fd32
- [x] results/Epic_Seven/concepts.md (45) → f1eb218
- [x] results/Final_Gear/items.md (45) → f1eb218
- [x] results/RuneScape/concepts.md (45) → f1eb218
- [x] results/Tera/timeline.md (45) → 1a76080
- [x] results/Tokyo_Ghoul/characters/Suzuya_Juuzou.md (45) → 4a4fd32
- [x] results/Tokyo_Ghoul/factions.md (45) → 1a76080
- [x] results/鈴蘭之劍/factions.md (45) → 1a76080

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

- [x] **多抓一些原始素材**（"可以的話，幫我多抓一些原始素材"）——**進行中**，見本檔頂部「新作品攝入流水線（2026-05-29）」：已完成 5 部、Malazan raw 待處理、Pillars/Grim Dawn 排隊中。

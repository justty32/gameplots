# 技能索引 (Skills Index)

存放於 `skills/` 目錄中、可重複使用的分析提示詞。技能對應 6-phase 工作流程的不同階段。完整流程說明見 [CLAUDE.md](CLAUDE.md)。

## Phase 2：全景掃描

| 技能 | 檔案 | 產出 | 說明 |
| :--- | :--- | :--- | :--- |
| 全景實體掃描 | [scan_entities.md](skills/scan_entities.md) | `working/<作品>/entities.md` | 列出作品中所有具名人事物地概念，作為後續詞條的覆蓋 checklist |

## Phase 3：詞條撰寫

| 技能 | 檔案 | 產出 | 說明 |
| :--- | :--- | :--- | :--- |
| 人物詞條 | [extract_characters.md](skills/extract_characters.md) | `results/<作品>/characters.md` | 所有具名人物 |
| 種族/陣營詞條 | [extract_factions.md](skills/extract_factions.md) | `results/<作品>/factions.md` | 種族、國家、組織、教團 |
| 事件詞條 | [extract_events.md](skills/extract_events.md) | `results/<作品>/events.md` | 戰役、災難、儀式、政治轉折 |
| 地點詞條 | [extract_places.md](skills/extract_places.md) | `results/<作品>/places.md` | 國家、城市、地標、異界 |
| 物品詞條 | [extract_items.md](skills/extract_items.md) | `results/<作品>/items.md` | 神器、武器、技術裝置 |
| 概念詞條 | [extract_concepts.md](skills/extract_concepts.md) | `results/<作品>/concepts.md` | 魔法系統、宗教、術語、抽象設定 |

> 重要詞條（超過約 25 行）拆出單檔到 `<類>/<name>.md`。

## Phase 4：編年整理

| 技能 | 檔案 | 產出 | 說明 |
| :--- | :--- | :--- | :--- |
| 編年表 | [build_timeline.md](skills/build_timeline.md) | `results/<作品>/timeline.md` | 線性事件編年，分時代 |

## Phase 5：速覽合成

| 技能 | 檔案 | 產出 | 說明 |
| :--- | :--- | :--- | :--- |
| 速覽 | [synthesize_synopsis.md](skills/synthesize_synopsis.md) | `results/<作品>/synopsis.md` | 5–10 分鐘讀懂全貌（**全劇透**） |

> 必須在所有 Phase 3、4 詞條完成後才執行。

## Phase 6：索引建立

| 技能 | 檔案 | 產出 | 說明 |
| :--- | :--- | :--- | :--- |
| 索引 | [build_index.md](skills/build_index.md) | `results/<作品>/index.md` | 機械合成所有詞條的索引清單 |

## 共通鐵則（每個技能都帶）

1. **廣度優先**：詞條目標是窮盡名單，不是填表。
2. **短條目齊全度優先於深度**：默認 3–8 行。
3. **長條目拆檔**：超過約 25 行就拆。
4. **全劇透**：結局、反轉、隱藏設定都寫。
5. **媒介翻譯**：非文字素材轉述為敘事意義。

## 使用方式

依工作流程順序，從上表找到當前 phase 對應的技能，開啟技能檔案，將「提示詞」區塊套用於手上的原始素材或前一階段產出。

# GamePlots — Claude Code 執行規範

## 專案本意

把使用者沒時間完整體驗的作品（小說、動畫、漫畫、遊戲、影片），轉成兩層文字產出：

1. **速覽層**：每部作品一份 `synopsis.md`，5–10 分鐘讀懂全貌，密度勝過短影片摘要。
2. **詞條層**：每部作品一個小 wiki，可依人物/事件/地點/陣營/物品/概念查詢。

不同媒介的素材統一**只保留文字敘事**——把畫面、音樂、演出**轉述為敘事意義**，不要省略整段。

## 核心鐵則

1. **語言**：所有輸出（文件、報告、溝通）一律使用**繁體中文**。
2. **目錄規範**：嚴禁自行建立頂級目錄，只能使用下表中已定義者。
3. **資料隔離**：原始素材放 `working/<作品>/raw/`，最終報告放 `results/<作品>/`，不得混用。
4. **腳本授權**：執行任何自行撰寫的腳本（尤其有網路存取或檔案修改功能者）前，**必須先徵得使用者同意**。若已授權隨意執行，單次下載不超過 **50MB**。
5. **安全性**：嚴禁下載或執行具安全風險的外部內容。
6. **環境自覺**：執行 Shell 指令前先確認作業系統（Windows/Linux）與 Shell 環境。

## 內容鐵則（反「填表」、反「選輯」）

1. **廣度優先**：詞條的目標是「窮盡所有值得查的人事物地概念」，不是「填滿固定段落數」。entities 名單上的東西沒寫完之前，不算 phase 3 完成。
2. **短條目齊全度優先於深度**：默認每條目 3–8 行。只有真有故事份量的條目才展開。
3. **長條目拆檔**：詞條若超過約 25 行就拆到 `<類別>/<名稱>.md`，主檔留 1–2 行摘要 + 連結。
4. **全劇透**：使用者要的就是「不看作品也掌握全貌」——結局、死亡、反轉、隱藏設定全部寫進去，不打馬賽克。
5. **媒介翻譯**：遇到非文字素材（畫面、音樂、演出、戰鬥動畫），轉述其敘事意義；不要省略整段，也不要描述視覺細節。例：「最終戰配樂用主角搖籃曲的小調變奏」是好的；「BGM 很燃」不是。

## 目錄結構

| 目錄 | 用途 |
| :--- | :--- |
| `working/<作品>/raw/` | 未加工的原始素材（Wiki 備份、爬取文本、論壇文章） |
| `working/<作品>/` | 分析暫存檔與中間產物（含 `entities.md` 全名單） |
| `results/<作品>/` | 結構化最終報告（速覽 + 詞條庫 + 編年 + 索引） |
| `classes/` | 跨作品主題彙整 |
| `scripts/` | 爬蟲、解析器、自動化工具 |
| `skills/` | 可重複使用的分析提示詞 |

## 每部作品的 `results/<作品>/` 結構

```
synopsis.md       # 速覽（5–10 分鐘讀懂全貌，全劇透）
index.md          # 索引（所有詞條一行摘要 + 連結）
timeline.md       # 編年表
characters.md     # 人物詞條
factions.md       # 種族/陣營詞條
events.md         # 事件詞條
places.md         # 地點詞條
items.md          # 物品/技術詞條
concepts.md       # 概念/設定詞條

# 重要詞條超過約 25 行時拆出來：
characters/<name>.md
events/<name>.md
... 等
```

## 標準工作流程（6 phases）

```
Phase 1 攝入       原始素材 → working/<作品>/raw/

Phase 2 全景掃描   skills/scan_entities
                   → working/<作品>/entities.md（全名單，覆蓋 checklist）

Phase 3 詞條撰寫   skills/extract_characters / extract_factions /
                   extract_events / extract_places / extract_items /
                   extract_concepts
                   → results/<作品>/<類>.md（必要時拆檔）

Phase 4 編年整理   skills/build_timeline
                   → results/<作品>/timeline.md

Phase 5 速覽合成   skills/synthesize_synopsis
                   → results/<作品>/synopsis.md
                   ★ 必須在所有詞條完成後才能跑

Phase 6 索引建立   skills/build_index
                   → results/<作品>/index.md
```

關鍵：Phase 5 速覽必須在所有詞條完成後才合成——速覽是從詞條庫往上提煉的精華，不是先寫好的概論。

## 任務完成前的自我檢查

- [ ] 產出皆為繁體中文？
- [ ] 檔案位置符合目錄規範（working vs results vs classes）？
- [ ] 詞條是否窮盡 entities 名單？沒有「忘了寫」的？
- [ ] 速覽是否包含結局與全部關鍵轉折（不迴避劇透）？
- [ ] 非文字媒介是否轉述為敘事意義（而不是省略或描述表象）？
- [ ] 是否優先利用 `skills/` 與 `scripts/` 中既有資源？
- [ ] 若執行了腳本，是否已取得使用者授權？

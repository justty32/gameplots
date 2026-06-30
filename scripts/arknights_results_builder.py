#!/usr/bin/env python3
"""Build first-pass Arknights result notes from Kengxxiao/ArknightsGameData."""

from __future__ import annotations

import datetime as dt
import json
import re
from collections import Counter
from pathlib import Path

from opencc import OpenCC


ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "working" / "Arknights"
RAW = WORK / "raw" / "ArknightsGameData" / "zh_CN" / "gamedata"
EXCEL = RAW / "excel"
MAIN_STORY = WORK / "processed" / "main_story"
OUT = ROOT / "results" / "Arknights"

cc = OpenCC("s2twp")


CORE_CHARACTER_IDS = [
    "npc_001_doctor",
    "char_002_amiya",
    "char_003_kalts",
    "char_010_chen",
    "char_017_huang",
    "char_113_cqbw",
    "char_1502_crosly",
    "char_136_hsguma",
    "char_002_amiya2",
    "char_010_chen2",
    "char_1014_nearl2",
    "char_4009_irene",
    "char_1012_skadi2",
    "char_4087_ines",
    "char_4011_lessng",
    "char_4110_delphn",
    "char_4039_horn",
]


CORE_CONCEPTS = [
    ("源石", "泰拉文明的能源基礎，也是礦石病與天災的核心來源。源石讓移動城市、工業與法術得以運作，卻也把社會建立在慢性災害之上。"),
    ("礦石病", "感染者體內源石結晶化的疾病。它既是醫學問題，也是階級與政治問題，因為感染者常被各國制度性排斥。"),
    ("感染者", "礦石病患者的社會身分。整合運動與羅德島的衝突，核心不是誰比較善良，而是感染者如何在被剝奪權利後尋找出路。"),
    ("天災", "泰拉世界週期性發生的大型災害，常伴隨源石擴散。移動城市與天災信使制度都是為了逃離天災而存在。"),
    ("移動城市", "泰拉大型國家維持文明的主要載體。城市可以遷移，代表國家邊界與人民生活都必須服從災害邏輯。"),
    ("源石技藝", "由源石與個體適性引出的法術體系。它不是單純魔法，而是醫療、工業、軍事與身分風險交織的技術。"),
    ("羅德島製藥", "名義上的感染者醫療與製藥組織，實際上同時承擔軍事、外交、情報與人道救援功能。"),
    ("整合運動", "由感染者憤怒凝聚而成的武裝運動。早期被塔露拉與其背後力量推向屠殺，失敗後留下感染者政治的巨大陰影。"),
    ("巴別塔", "羅德島前身之一，與卡茲戴爾內戰、博士、凱爾希、特蕾西婭和特雷西斯密切相關。"),
    ("卡茲戴爾王權", "薩卡茲歷史與當代主線的核心政治問題。王權不只是統治權，也承載薩卡茲長久流亡、仇恨與復國欲望。"),
    ("石棺", "切爾諾伯格地下的重要裝置，也是博士甦醒的起點。其功能與泰拉更深層古文明線索相連。"),
    ("深海與海嗣", "阿戈爾、深海獵人與海嗣線的核心概念，將明日方舟從地表政治推向生物演化與文明存續問題。"),
    ("律法", "拉特蘭社會與薩科塔共感的核心規則。它讓宗教、法律、種族特性與武裝秩序合為一體。"),
    ("歲", "炎國神祇與分裂個體相關的長線設定，將神話、年節敘事與政治監控交織。"),
    ("泰拉", "故事所在的大地。它不是單一災後世界，而是一個由災害、歧視、國家利益與遠古祕密共同壓迫的文明系統。"),
]


MANUAL_ITEMS = [
    ("羅德島本艦", "移動平台與組織基地，是醫療船、軍事艦與政治庇護所的混合體。"),
    ("博士的石棺", "博士在切爾諾伯格甦醒的裝置，象徵主角失憶與泰拉古文明祕密的起點。"),
    ("阿米婭的戒指", "抑制與引導阿米婭力量的重要物件，和她承受的薩卡茲王權力量相關。"),
    ("陳的赤霄", "陳的代表武器，連接龍門警務身分、家族背景與她對秩序的執念。"),
    ("守護銃", "拉特蘭薩科塔文化中的象徵性武器，既是個人武裝，也是社群與律法關係的標誌。"),
    ("源石工業設備", "泰拉現代化的基礎。越依賴它，文明越難擺脫礦石病與天災循環。"),
]


MAIN_ARCS = [
    ("序章至第三章", "切爾諾伯格撤離", "博士甦醒、阿米婭救援、羅德島遭遇整合運動，故事用一場失控城市災難建立感染者暴力、烏薩斯壓迫與羅德島救援立場。"),
    ("第四至第六章", "龍門攻防", "整合運動把戰火推向龍門；陳、星熊、魏彥吾與羅德島在秩序與人道間互相試探，梅菲斯特與浮士德線則展示被仇恨消耗的少年兵。"),
    ("第七至第八章", "整合運動終局", "愛國者、霜星與塔露拉的真相收束。羅德島擊敗整合運動軍事主軸，但感染者問題沒有被解決，只是從街頭暴動變成更深的政治命題。"),
    ("第九至第十四章", "維多利亞與薩卡茲戰爭", "主線轉向維多利亞，卡茲戴爾與特雷西斯的計畫浮上台面。羅德島不再只是救援感染者，而被迫介入國家戰爭與薩卡茲歷史。"),
    ("第十五至第十七章", "新資料段落", "目前資料庫已含「離解複合」「反常光譜」「相變臨界」。從文本可見凱爾希、烏薩斯研究所、石棺與軍方清洗等背景被重新打開，主線正在把博士甦醒前史與泰拉古代裝置線拉回核心。"),
]

PRIORITY_ACTIVITY_SUMMARIES = {
    "act33side": {
        "name": "巴別塔",
        "role": "博士、特蕾西婭、特雷西斯、凱爾希與阿米婭命運的前史核心。",
        "summary": "這條活動把「羅德島」之前的巴別塔時代攤開：卡茲戴爾內戰不是單純民族復國戰，而是特蕾西婭的理想、特雷西斯的軍事現實、博士的戰略能力與凱爾希長期計畫互相撕裂的結果。它對同人最重要的價值，是把博士從玩家代理人拉回一個有舊債、有能力、也可能被審判的人。",
        "fanfic": "適合寫博士失憶前後人格落差、阿米婭繼承特蕾西婭意志、W 對舊巴別塔的複雜忠誠，以及薩卡茲復國理念如何在溫柔與戰爭間分裂。",
    },
    "act9d0": {
        "name": "生於黑夜",
        "role": "W、赫德雷、伊內絲與薩卡茲傭兵線的前史入口。",
        "summary": "故事聚焦薩卡茲傭兵在卡茲戴爾戰火中的生存方式。W、赫德雷、伊內絲的關係不是乾淨的同伴情，而是建立在戰場互信、利益盤算、情報隱瞞與對特蕾西婭旗幟的不同理解上。它讓薩卡茲不只是反派種族，而是被長期戰爭塑形的一群人。",
        "fanfic": "適合寫傭兵小隊、戰地逃亡、假死與重逢；要注意薩卡茲人物的幽默常帶防衛性，不能只寫成瘋狂好戰。",
    },
    "act18d0": {
        "name": "遺塵漫步",
        "role": "凱爾希長生視角與跨國歷史行動的代表作。",
        "summary": "這條活動讓凱爾希從羅德島醫生變成穿行各國歷史的行動者。她在不同時期、不同國家的選擇都不是全知救世，而是在有限局勢裡減少更壞的後果。它補強了凱爾希的孤獨：她知道太多，也因為知道太多，必須承受他人無法理解的冷酷判斷。",
        "fanfic": "適合寫過去時代的凱爾希、她與普通人短暫交會後留下的後果，以及『被救的人不一定知道自己被誰救過』的故事。",
    },
    "act25side": {
        "name": "孤星",
        "role": "萊茵生命、哥倫比亞科技倫理與泰拉天空 / 古文明線的關鍵活動。",
        "summary": "孤星把萊茵生命從科學公司推向文明尺度的問題：科學家想知道天空之外有什麼，資本與國家想把成果變成權力，實驗體與受害者則承擔進步的成本。赫默、塞雷婭、伊芙利特、繆爾賽思與霍爾海雅各自代表不同的科技倫理位置。",
        "fanfic": "適合寫科研機構內鬥、親情式保護與控制、實驗倫理、哥倫比亞式自由市場如何把理想變成風險投資。",
    },
    "act17side": {
        "name": "愚人號",
        "role": "伊比利亞、阿戈爾、深海獵人與海嗣線的大型展開。",
        "summary": "愚人號把海洋寫成文明邊界：伊比利亞用審判庭守住岸線，阿戈爾與深海獵人背負更深的生物戰爭，海嗣則不是傳統怪物，而是會把個體、群體與演化混在一起的存在。艾麗妮在此從律法執行者被迫面對世界尺度的恐懼。",
        "fanfic": "適合寫沿海城鎮、審判庭信仰、深海獵人身體異化、普通人面對海嗣污染時的心理崩潰。",
    },
    "act13side": {
        "name": "長夜臨光",
        "role": "卡西米爾騎士競技、商業資本與臨光家族理想的集中呈現。",
        "summary": "長夜臨光把『騎士』從英雄稱號拆成廣告、賽制、家族榮耀、城市娛樂與階級壓迫。瑪嘉烈回到卡西米爾不是單純奪冠，而是用自己的存在質疑一個把榮耀商品化的國家。感染者騎士與無胄盟讓這場競技背後的暴力浮出水面。",
        "fanfic": "適合寫公開賽、贊助商操控、騎士道與現代媒體衝突，以及耀騎士作為精神象徵如何影響普通感染者。",
    },
    "act21side": {
        "name": "敘拉古人",
        "role": "敘拉古黑幫政治、家族秩序與德克薩斯 / 拉普蘭德關係線核心。",
        "summary": "敘拉古人把黑幫寫成一套地方秩序：家族、法官、沉默、背叛與繼承規則共同維持社會。德克薩斯回到故土，不只是面對過去，也是拒絕被家族血統重新定義；拉普蘭德則像一把永遠追著她的刀，逼她承認自己仍與敘拉古相連。",
        "fanfic": "適合寫黑幫家族、舊友重逢、身份切割失敗、企鵝物流外來者闖進地方規則後造成的荒謬與危險。",
    },
    "act16side": {
        "name": "吾導先路",
        "role": "拉特蘭律法、薩科塔共感與宗教政治的代表活動。",
        "summary": "吾導先路展開拉特蘭：這不是單純天使國，而是一個把信仰、法律、銃械與種族共感綁在一起的社會。安多恩的問題不只是叛教，而是質疑律法能否照見薩科塔以外的人。菲亞梅塔、莫斯提馬、艾澤爾與教宗讓這條線同時有個人舊傷與制度辯論。",
        "fanfic": "適合寫宗教法庭、薩科塔與非薩科塔的隔閡、莫斯提馬小隊舊事，以及『善意制度是否也會排除他者』的矛盾。",
    },
}


def load_json(name: str):
    with (EXCEL / name).open(encoding="utf-8") as f:
        return json.load(f)


def tw(text: object) -> str:
    return cc.convert("" if text is None else str(text))


def tw_markdown(text: str) -> str:
    parts = re.split(r"(`[^`]*`)", text)
    return "".join(part if part.startswith("`") else tw(part) for part in parts)


def clean(text: str, limit: int | None = None) -> str:
    text = re.sub(r"<[^>]+>", "", text or "")
    text = re.sub(r"\s+", " ", text).strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip() + "…"
    return text


def anchor(name: str) -> str:
    return re.sub(r"[^\w\u4e00-\u9fff-]+", "", name.lower().replace(" ", "-"))


def fmt_time(ts: int | None) -> str:
    if not ts or ts < 0:
        return "時間未公開"
    return dt.datetime.fromtimestamp(ts, tz=dt.timezone.utc).strftime("%Y-%m-%d")


def handbook_sections(entry: dict | None) -> dict[str, str]:
    sections: dict[str, str] = {}
    if not entry:
        return sections
    for sec in entry.get("storyTextAudio", []):
        title = tw(sec.get("storyTitle") or "未命名")
        text = "\n".join(st.get("storyText", "") for st in sec.get("stories", []))
        sections[title] = text
    return sections


def base_profile(text: str) -> dict[str, str]:
    fields = {}
    for label in ["代號", "性別", "戰鬥經驗", "出身地", "生日", "種族", "身高", "礦石病感染情況"]:
        m = re.search(rf"【{label}】([^\n]+)", tw(text))
        if m:
            fields[label] = clean(m.group(1), 80)
    return fields


def power_name(char_data: dict, teams: dict) -> str:
    for key in ("teamId", "groupId", "nationId"):
        pid = char_data.get(key)
        if pid and pid in teams:
            return teams[pid].get("powerName") or pid
    main = char_data.get("mainPower") or {}
    for key in ("teamId", "groupId", "nationId"):
        pid = main.get(key)
        if pid and pid in teams:
            return teams[pid].get("powerName") or pid
    return "未標明"


def read_main_story_stats() -> list[dict]:
    stats = []
    for path in sorted(MAIN_STORY.glob("main_*.txt"), key=lambda p: int(re.search(r"main_(\d+)", p.name).group(1))):
        text = path.read_text(encoding="utf-8")
        title = re.search(r"#\s+(.+?)\s+\(", text)
        speakers = Counter()
        for line in text.splitlines():
            m = re.match(r"([^：#\n]{1,18})：", line)
            if m and not m.group(1).startswith("選項"):
                speakers[m.group(1)] += 1
        stats.append(
            {
                "file": path.name,
                "title": title.group(1) if title else path.stem,
                "nodes": text.count("\n## "),
                "chars": len(text),
                "speakers": speakers.most_common(8),
            }
        )
    return stats


def write(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(tw_markdown(body).rstrip() + "\n", encoding="utf-8")


def build_characters(chars: dict, handbook: dict, npcs: dict, teams: dict) -> None:
    rows = []
    for cid, data in chars.items():
        if cid not in handbook:
            continue
        if data.get("isSpChar"):
            continue
        rows.append((cid, data))
    for cid, data in npcs.items():
        rows.append((cid, {"name": data.get("name") or data.get("npcName") or cid, "itemUsage": data.get("desc", ""), "nationId": None}))

    order = {cid: i for i, cid in enumerate(CORE_CHARACTER_IDS)}
    rows.sort(key=lambda item: (order.get(item[0], 9999), power_name(item[1], teams), item[1].get("name") or item[0], item[0]))

    lines = ["# 人物詞條 (Characters)", "", f"> 第一版由資料表生成，共 {len(rows)} 條。主線核心人物置頂；其餘依勢力與名稱排列。", ""]
    for cid, data in rows:
        name = data.get("name") or data.get("appellation") or cid
        sections = handbook_sections(handbook.get(cid))
        profile = base_profile(sections.get("基礎檔案", ""))
        resume = sections.get("客觀履歷", "") or data.get("itemUsage", "") or data.get("itemDesc", "")
        faction = power_name(data, teams)
        tags = "、".join(data.get("tagList") or [])
        lines += [f"### {name}（{cid}）", "", f"> {faction}相關人物。{clean(data.get('itemUsage') or data.get('description') or '', 90)}"]
        bits = []
        for label in ["代號", "性別", "出身地", "種族", "礦石病感染情況"]:
            if label in profile:
                bits.append(f"{label}：{profile[label]}")
        if bits:
            lines.append(f"- **檔案**：{'；'.join(bits)}。")
        if tags:
            lines.append(f"- **戰場定位**：{tags}。")
        if resume:
            lines.append(f"- **履歷 / 故事位置**：{clean(tw(resume), 220)}")
        for title in ["檔案資料一", "升變檔案一"]:
            if title in sections:
                lines.append(f"- **補充設定**：{clean(tw(sections[title]), 180)}")
                break
        lines.append("")
    write(OUT / "characters.md", "\n".join(lines))


def build_factions(teams: dict) -> None:
    preferred = ["rhodes", "reunion", "babel", "kazdel", "lungmen", "lgd", "victoria", "ursus", "kazimierz", "laterano", "columbia", "rhine", "egir", "abyssal", "yan", "sui"]
    order = {pid: i for i, pid in enumerate(preferred)}
    rows = [(pid, d) for pid, d in teams.items() if pid != "none"]
    rows.sort(key=lambda item: (order.get(item[0], 9999), item[1].get("orderNum", 9999), item[1].get("powerName", item[0])))
    lines = ["# 陣營詞條 (Factions)", "", f"> 由 `handbook_team_table.json` 建立，共 {len(rows)} 條。", ""]
    manual = {
        "rhodes": "感染者醫療、救援與武裝行動組織。它的矛盾在於：越想以醫療解決問題，越被泰拉政治逼成準軍事行動者。",
        "babel": "羅德島前身之一，牽涉卡茲戴爾內戰、特蕾西婭、凱爾希與博士的舊債。",
        "lungmen": "炎國邊境的高度自治商業城市。龍門篇把它寫成秩序、治安、交易與冷酷治理的集合。",
        "victoria": "以王權空缺與貴族軍政為核心的大國，維多利亞篇的戰場本質是帝國權力真空被薩卡茲與各派勢力撕開。",
        "kazdel": "薩卡茲的故土與政治傷口。它既是國家，也是流亡民族長久仇恨的象徵。",
        "reunion": "感染者武裝運動，代表被壓迫者的正當怒火如何被復仇、操控與戰爭邏輯吞沒。",
    }
    for pid, data in rows:
        name = data.get("powerName") or pid
        code = data.get("powerCode") or pid
        level = data.get("powerLevel")
        lines += [f"### {name}（{pid} / {code}）", "", f"> 資料表層級 {level} 的勢力 / 地區 / 組織。"]
        if pid in manual:
            lines.append(f"- **故事定位**：{manual[pid]}")
        if data.get("isRaw"):
            lines.append("- **資料註記**：標記為 raw，通常是國家、地區或較高層級分類。")
        if data.get("isLimited"):
            lines.append("- **資料註記**：限定或特殊分類。")
        lines.append("")
    write(OUT / "factions.md", "\n".join(lines))


def build_events(story_review: dict) -> None:
    rows = sorted(story_review.items(), key=lambda item: ((item[1].get("startTime") or 0) if item[1].get("startTime", -1) > 0 else 10**12, item[0]))
    lines = ["# 事件詞條 (Events)", "", f"> 以劇情回顧表建立，共 {len(rows)} 個篇章 / 活動入口。", ""]
    for sid, data in rows:
        nodes = data.get("infoUnlockDatas") or []
        codes = [n.get("storyCode") for n in nodes if n.get("storyCode")]
        first_codes = "、".join(dict.fromkeys(codes[:6]))
        lines += [f"### {data.get('name') or sid}（{sid}）", "", f"> {data.get('actType') or data.get('entryType') or 'UNKNOWN'}；{fmt_time(data.get('startTime'))} 開始；{len(nodes)} 個劇情節點。"]
        if first_codes:
            lines.append(f"- **節點樣本**：{first_codes}。")
        if data.get("entryType"):
            lines.append(f"- **分類**：{data.get('entryType')} / {data.get('actType')}。")
        if sid.startswith("main_"):
            lines.append("- **主線定位**：主線章節，應與 `main_story_outline.md` 交叉閱讀。")
        lines.append("")
    write(OUT / "events.md", "\n".join(lines))


def build_places(zone_table: dict, teams: dict) -> None:
    zones = list(zone_table.get("zones", {}).items())
    zones.sort(key=lambda item: (item[1].get("type") or "", item[1].get("zoneIndex", 9999), item[0]))
    lines = ["# 地點詞條 (Places)", "", "> 先收錄資料表中的章節區域與主要國家 / 地區；城市細節後續可從活動文本再展開。", ""]
    lines.append("## 國家與地區")
    for pid, data in sorted(teams.items(), key=lambda item: (item[1].get("orderNum", 9999), item[0])):
        if pid == "none" or data.get("powerLevel") not in (0, 1):
            continue
        lines += [f"### {data.get('powerName') or pid}", "", f"> 代碼：{pid} / {data.get('powerCode') or ''}。", ""]
    lines.append("## 劇情區域")
    for zid, data in zones:
        name = data.get("zoneNameSecond") or data.get("zoneNameFirst") or data.get("zoneNameThird") or zid
        first = data.get("zoneNameFirst") or ""
        ztype = data.get("type") or "UNKNOWN"
        lines += [f"### {name}（{zid}）", "", f"> {ztype} 區域。{first} {data.get('zoneNameThird') or ''}".strip(), ""]
    write(OUT / "places.md", "\n".join(lines))


def build_items_and_concepts() -> None:
    lines = ["# 物品 / 技術詞條 (Items)", "", "> 第一版收錄對敘事最關鍵的物件與技術。一般養成素材未列入。", ""]
    for name, desc in MANUAL_ITEMS:
        lines += [f"### {name}", "", f"> {desc}", ""]
    write(OUT / "items.md", "\n".join(lines))

    lines = ["# 概念 / 設定詞條 (Concepts)", "", "> 同人寫作最容易牽動世界觀一致性的核心設定。", ""]
    for name, desc in CORE_CONCEPTS:
        lines += [f"### {name}", "", f"> {desc}", ""]
    write(OUT / "concepts.md", "\n".join(lines))


def build_main_story_outline() -> None:
    stats = read_main_story_stats()
    lines = ["# 主線整理與章節索引", "", "> 來源為已清理主線文本。這份文件偏向寫作參考：先抓主線弧線，再回原文查語氣與細節。", ""]
    lines.append("## 主線弧線")
    for title, name, desc in MAIN_ARCS:
        lines += [f"### {title}：{name}", "", desc, ""]
    lines.append("## 章節索引")
    for s in stats:
        speakers = "、".join(f"{tw(k)}({v})" for k, v in s["speakers"][:5])
        lines += [f"### {tw(s['title'])}", "", f"- **文本量**：{s['nodes']} 個節點，約 {s['chars']} 字元。", f"- **高頻說話者**：{speakers or '無明確說話者統計'}。", f"- **清理文本**：`working/Arknights/processed/main_story/{s['file']}`。", ""]
    write(OUT / "main_story_outline.md", "\n".join(lines))


def build_activity_story_outline(story_review: dict) -> None:
    processed_dir = WORK / "processed" / "priority_events"
    lines = [
        "# 重點活動線整理",
        "",
        "> 這份檔案面向同人寫作：先標出每條活動在世界觀中的功能，再給可回查的清理文本路徑。",
        "",
        "## 優先閱讀順序",
        "",
        "1. **巴別塔**：先理解博士、阿米婭、凱爾希與薩卡茲主線舊債。",
        "2. **生於黑夜**、**遺塵漫步**：補 W / 赫德雷 / 伊內絲與凱爾希長線。",
        "3. **孤星**、**愚人號**：補科技倫理、古文明、深海與文明邊界。",
        "4. **長夜臨光**、**敘拉古人**、**吾導先路**：補國家風味與地方制度，適合寫支線同人。",
        "",
    ]

    for sid, meta in PRIORITY_ACTIVITY_SUMMARIES.items():
        data = story_review.get(sid, {})
        paths = list(processed_dir.glob(f"{sid}_*.txt"))
        path = paths[0] if paths else None
        text = path.read_text(encoding="utf-8") if path and path.exists() else ""
        speakers = Counter()
        node_heads = []
        for line in text.splitlines():
            if line.startswith("## "):
                node_heads.append(line[3:])
            m = re.match(r"([^：#\n]{1,18})：", line)
            if m and not m.group(1).startswith(("選項", "选项")):
                speakers[m.group(1)] += 1
        top_speakers = "、".join(f"{tw(name)}({count})" for name, count in speakers.most_common(8))
        node_sample = "；".join(tw(h) for h in node_heads[:6])
        lines += [
            f"## {meta['name']}（{sid}）",
            "",
            f"> {meta['role']}",
            "",
            f"- **資料規模**：{len(node_heads)} 個節點，約 {len(text)} 字元；遊戲內分類 `{data.get('actType') or data.get('entryType') or 'UNKNOWN'}`。",
            f"- **高頻人物 / 說話者**：{top_speakers or '無統計'}。",
            f"- **節點樣本**：{node_sample or '無'}。",
            f"- **故事功能**：{meta['summary']}",
            f"- **同人切入**：{meta['fanfic']}",
        ]
        if path:
            lines.append(f"- **清理文本**：`{path.relative_to(ROOT).as_posix()}`。")
        lines.append("")

    lines += [
        "## 寫作取用建議",
        "",
        "- 寫博士中心文，優先查 `巴別塔`、主線第 14-17 章與 `遺塵漫步`；這些文本會決定博士能不能被寫成單純好人。",
        "- 寫薩卡茲或 W / 赫德雷 / 伊內絲，先查 `生於黑夜`，再查 `巴別塔` 與維多利亞主線。",
        "- 寫科技倫理，`孤星` 比一般幹員檔案更重要，因為它直接展示公司、科學家、實驗品與國家權力的互相利用。",
        "- 寫地方國家風味，`長夜臨光`、`敘拉古人`、`吾導先路` 各自代表商業騎士國、黑幫地方秩序與宗教法共同體。",
        "",
    ]
    write(OUT / "activity_story_outline.md", "\n".join(lines))


def build_timeline(story_review: dict) -> None:
    main = sorted((k, v) for k, v in story_review.items() if k.startswith("main_"))
    events = sorted(
        ((k, v) for k, v in story_review.items() if not k.startswith("main_") and v.get("startTime", -1) > 0),
        key=lambda item: item[1]["startTime"],
    )
    lines = ["# 《明日方舟》編年表", "", "## 第一紀：古文明與大地祕密（前史）", "", "> 源石、石棺、阿戈爾、海嗣與各國神話指向更古老的文明層。這部分仍由主線與活動逐步揭露。", "", "- [時期不詳] — **古文明裝置遺留** — 石棺等裝置成為現代勢力爭奪與誤用的源頭。", "- [時期不詳] — **源石文明形成** — 泰拉各國在源石技術與天災壓力下建立移動城市秩序。", "", "## 第二紀：感染者政治與羅德島前史", "", "- [主線前] — **卡茲戴爾內戰與巴別塔** — 博士、凱爾希、特蕾西婭、特雷西斯的舊關係奠定羅德島核心矛盾。", "- [主線前] — **羅德島製藥成形** — 醫療組織承接巴別塔遺產，轉向感染者救援與跨國行動。", "", "## 第三紀：整合運動篇（故事主線開始）", ""]
    for sid, data in main:
        if sid in {f"main_{i}" for i in range(0, 9)}:
            lines.append(f"- ★ **{data.get('name')}** — 博士甦醒至整合運動終局。→ [詳見](events.md)")
    lines += ["", "## 第四紀：維多利亞、薩卡茲與石棺線", ""]
    for sid, data in main:
        if sid not in {f"main_{i}" for i in range(0, 9)}:
            lines.append(f"- ★ **{data.get('name')}** — 維多利亞戰爭與更深前史線。→ [詳見](events.md)")
    lines += ["", "## 活動發布序列（資料表時間）", ""]
    for sid, data in events[:120]:
        lines.append(f"- {fmt_time(data.get('startTime'))} — **{data.get('name') or sid}** — {data.get('actType') or data.get('entryType')}，{len(data.get('infoUnlockDatas') or [])} 節點。")
    if len(events) > 120:
        lines.append(f"- ……另有 {len(events) - 120} 個有時間戳的活動 / 小故事入口，詳見 `events.md`。")
    write(OUT / "timeline.md", "\n".join(lines))


def build_synopsis_stub() -> None:
    lines = ["# 《明日方舟》速覽", "", "> 注意：這是第一版工作速覽，已能支援同人構思；嚴格版 synopsis 應在活動線與密錄詞條補完後再重寫。", "", "## 鉤子", "", "《明日方舟》不是單純的末世塔防故事，而是把「疾病」「能源」「災害」「國家暴力」綁在一起的政治奇幻。感染者不是怪物，而是被現代化犧牲後又被制度驅逐的人；羅德島不是救世主，而是一艘在各國利益、戰爭與醫療倫理之間勉強航行的船。", "", "## 世界與舞台", "", "泰拉的文明建立在源石之上。源石帶來能源、工業與源石技藝，也帶來天災與礦石病。移動城市讓國家可以逃離災害，卻不能逃離階級、軍隊、邊境與歧視。每個國家都有自己的秩序：龍門講交易與治安，烏薩斯講帝國與壓迫，維多利亞講貴族與王權空缺，卡茲戴爾講薩卡茲長久的流亡與復仇。", "", "## 開局", "", "博士從切爾諾伯格地下石棺甦醒，失去記憶，只記得自己被阿米婭與羅德島救出。城市正在陷入整合運動與烏薩斯政治災難，博士被迫重新指揮戰鬥。這個開局同時設下三個問題：博士過去做過什麼、阿米婭為何如此信任博士、感染者的怒火為何會變成屠殺。", "", "## 主軸", ""]
    for _, name, desc in MAIN_ARCS:
        lines.append(f"- **{name}**：{desc}")
    lines += ["", "## 寫同人時最重要的張力", "", "- 羅德島可以救人，但無法單靠善意改造國家制度。", "- 感染者的痛苦是真的，整合運動的暴力後果也是真的；不要把其中一邊寫成純粹背景板。", "- 阿米婭的溫柔一直和權力、王權、責任綁在一起。", "- 博士的失憶不是方便設定，而是逃避舊債、重建人格與重新選擇立場的敘事裝置。", "- 凱爾希常像謎語人，但她的核心不是冷漠，而是活得太久後形成的風險管理。", ""]
    write(OUT / "synopsis.md", "\n".join(lines))


def build_relationship_map() -> None:
    lines = [
        "# 《明日方舟》關係與衝突圖",
        "",
        "這份圖不是配對清單，而是寫同人時最容易推動情節的壓力點：誰欠誰、誰信任誰、誰的理想會傷害誰。",
        "",
        "## 羅德島核心三角",
        "",
        "### 博士 ↔ 阿米婭",
        "",
        "- **表層關係**：指揮官與羅德島公開領袖；阿米婭在博士失憶後仍選擇信任博士。",
        "- **深層張力**：阿米婭繼承的不只是羅德島責任，還有特蕾西婭與薩卡茲王權線的重量。博士若逐步想起巴別塔舊事，這份信任會變成審判與和解的入口。",
        "- **同人用法**：適合描寫兩人位置反轉、阿米婭不願讓博士再成為過去那個人的恐懼、博士重新選擇羅德島的過程。",
        "",
        "### 博士 ↔ 凱爾希",
        "",
        "- **表層關係**：共同維持羅德島運作的戰略搭檔。",
        "- **深層張力**：凱爾希知道博士的過去，也知道博士的能力可能帶來什麼代價。她需要博士，但不會天真地原諒博士。",
        "- **同人用法**：兩人對話適合寫成資訊不對等的審訊；凱爾希越平靜，代表她越清楚風險。",
        "",
        "### 阿米婭 ↔ 凱爾希",
        "",
        "- **表層關係**：監護、教育與組織治理關係。",
        "- **深層張力**：凱爾希保護阿米婭，也在訓練她面對不得不殘酷的政治現實；阿米婭則是凱爾希長期計畫中少數仍能代表希望的人。",
        "- **同人用法**：適合寫『溫柔的人如何學會下命令』，或凱爾希明知殘酷卻仍把選擇權交給阿米婭。",
        "",
        "## 巴別塔與薩卡茲舊債",
        "",
        "### 特蕾西婭 ↔ 博士 ↔ 特雷西斯",
        "",
        "- **核心衝突**：特蕾西婭代表一種想讓薩卡茲走向不同未來的理想；特雷西斯代表軍事現實與復國意志；博士則是能讓戰局改變的人，也因此難以保持無辜。",
        "- **同人用法**：不要只寫誰背叛誰；更有力的是寫每個人都能提出合理理由，卻仍把彼此推向無法回頭的結局。",
        "",
        "### W ↔ 特蕾西婭 / 巴別塔",
        "",
        "- **核心衝突**：W 的玩世不恭是保護色。她對巴別塔的記憶與對特蕾西婭的執念，讓她很難真正成為羅德島的普通合作者。",
        "- **同人用法**：W 適合當揭傷疤的人，她不一定說真話，但常會逼別人承認不想承認的真相。",
        "",
        "### W ↔ 赫德雷 ↔ 伊內絲",
        "",
        "- **核心衝突**：三人的關係建立在傭兵式信任上：可以把命交給對方，但不一定把真相交給對方。",
        "- **同人用法**：適合寫重逢、假死後的情緒債、任務中默契與私下互相防備並存。",
        "",
        "## 國家線關係網",
        "",
        "### 龍門：陳 / 星熊 / 魏彥吾",
        "",
        "- **核心衝突**：龍門的秩序有效，但冷酷。陳相信法律與警務，魏彥吾相信城市存續，星熊夾在街頭現實與制度任務之間。",
        "- **同人用法**：適合寫城市治理、警察倫理，以及『正確命令是否仍會傷害無辜者』。",
        "",
        "### 卡西米爾：瑪嘉烈 / 商業聯合會 / 感染者騎士",
        "",
        "- **核心衝突**：騎士精神被包裝成商品，感染者被允許成為看點卻不被允許真正獲得尊嚴。",
        "- **同人用法**：公開賽場是最好用的舞臺，因為每場勝利都同時是體育、政治、廣告與階級表演。",
        "",
        "### 敘拉古：德克薩斯 / 拉普蘭德 / 家族",
        "",
        "- **核心衝突**：德克薩斯想離開家族定義，拉普蘭德則像敘拉古本身一樣追上來，提醒她血統、暴力與過去不是搬家就能切斷。",
        "- **同人用法**：適合寫『逃離故鄉的人回來後，發現故鄉仍認得她』。",
        "",
        "### 拉特蘭：莫斯提馬 / 菲亞梅塔 / 安多恩 / 律法",
        "",
        "- **核心衝突**：拉特蘭的善意建立在律法和共感上，但律法照不到所有人。安多恩的叛離把制度的盲點推到臺前。",
        "- **同人用法**：適合寫宗教共同體、異端審判、昔日小隊的裂痕，以及非薩科塔在拉特蘭的疏離。",
        "",
        "## 科技與文明邊界",
        "",
        "### 萊茵生命：赫默 / 塞雷婭 / 伊芙利特 / 繆爾賽思",
        "",
        "- **核心衝突**：保護、控制、實驗與親情糾纏在一起。萊茵生命的每個善意都可能被公司制度變成研究資料。",
        "- **同人用法**：適合寫研究倫理、家人式關係是否也是監護權爭奪，以及科學家面對受害者時的愧疚。",
        "",
        "### 深海線：斯卡蒂 / 歌蕾蒂婭 / 幽靈鯊 / 艾麗妮",
        "",
        "- **核心衝突**：深海獵人的身體本身就是戰場。艾麗妮代表岸上的律法與人類尺度，深海獵人則代表已經被迫跨過人類邊界的人。",
        "- **同人用法**：適合寫身體異化、記憶污染、海岸城鎮恐懼，以及『怪物是否仍能選擇守護人類』。",
        "",
        "## 寫作檢查",
        "",
        "- 角色不是只屬於個人關係，也屬於國家、公司、種族、疾病與戰爭史。",
        "- 親密關係裡常有資訊不對等；明日方舟的角色很少能把全部真相說清楚。",
        "- 最好的衝突通常不是善惡，而是兩種合理選擇互相排斥。",
        "",
    ]
    write(OUT / "relationship_map.md", "\n".join(lines))


def build_character_deep_dive() -> None:
    lines = [
        "# 《明日方舟》核心人物深挖包",
        "",
        "這份檔案服務同人寫作：每個人物都按「核心動機、舊債、關係雷點、可寫衝突」整理。它不替代 `characters.md`，而是幫你判斷角色在劇情壓力下會怎麼選。",
        "",
        "## 羅德島核心",
        "",
        "### 博士",
        "",
        "> 失憶後的羅德島指揮官；巴別塔時代舊債的承載者。",
        "",
        "- **核心動機**：失憶後的博士表面上是在重新理解世界，實際上是在重新選擇自己要成為誰。寫博士時，重點不是「聰明」，而是他是否願意承認自己的決策會讓他人付出代價。",
        "- **舊債**：巴別塔線讓博士不再只是玩家代理人。他曾經是能改變戰局的人，也因此可能參與過讓特蕾西婭、薩卡茲與巴別塔走向破裂的關鍵決策。",
        "- **關係雷點**：阿米婭的信任不是免費的；凱爾希的合作也不是原諒。博士若把自己寫成完全無辜，會削弱這兩段關係的重量。",
        "- **可寫衝突**：博士面對舊部、巴別塔倖存者、W 或凱爾希時，被迫承認「我不記得」不能抵消「我曾經造成」。",
        "- **回查文本**：`working/Arknights/processed/priority_events/act33side_巴别塔.txt`、`working/Arknights/processed/main_story/main_14_慈悲灯塔.txt`。",
        "",
        "### 阿米婭",
        "",
        "> 羅德島公開領袖；溫柔、責任與薩卡茲王權力量的交界點。",
        "",
        "- **核心動機**：阿米婭想救感染者，也想守住羅德島仍能相信人的理由。她的溫柔不是軟弱，而是一種明知世界殘酷仍不放棄人的政治選擇。",
        "- **舊債**：她與特蕾西婭、薩卡茲王權和博士過去的關係相連。這讓她不只是少女領袖，也是一個被迫承接歷史重量的人。",
        "- **關係雷點**：她信任博士，但不是沒有判斷力。寫阿米婭時不要把她寫成只會依賴博士；她會請博士指揮，也會在必要時承擔博士無法替她承擔的責任。",
        "- **可寫衝突**：阿米婭在救人與下令犧牲之間抉擇；她害怕自己越來越像君王，卻又不能逃避領袖位置。",
        "- **回查文本**：`working/Arknights/processed/main_story/main_0_黑暗时代·上.txt`、`working/Arknights/processed/main_story/main_8_怒号光明.txt`、`working/Arknights/processed/priority_events/act33side_巴别塔.txt`。",
        "",
        "### 凱爾希",
        "",
        "> 羅德島醫療與戰略核心；長期歷史行動者。",
        "",
        "- **核心動機**：凱爾希不是冷漠，而是把情緒壓在判斷之後。她活得太久、看過太多失敗，所以她的善意常以風險控管的形式出現。",
        "- **舊債**：她穿過不同國家與歷史現場，持續介入泰拉走向。這讓她對短期勝利非常警惕，也讓她不容易向任何人交出完整真相。",
        "- **關係雷點**：她需要博士，但不等於信任博士的一切；她保護阿米婭，也會把阿米婭推上必須承擔的位置。",
        "- **可寫衝突**：凱爾希救下一個人，卻不告訴對方全部理由；她被指責冷酷時，不能用真相替自己辯護，因為真相會造成更大風險。",
        "- **回查文本**：`working/Arknights/processed/priority_events/act18d0_遗尘漫步.txt`、`working/Arknights/processed/main_story/main_7_苦难摇篮.txt`。",
        "",
        "## 巴別塔與薩卡茲",
        "",
        "### 特蕾西婭",
        "",
        "> 巴別塔理想的中心；阿米婭與博士舊債的關鍵人物。",
        "",
        "- **核心動機**：她不是單純聖女，而是試圖讓薩卡茲走出戰爭循環的政治人物。她的溫柔帶有強烈方向感，不是逃避權力。",
        "- **舊債**：她的理想讓很多人願意跟隨，也讓她與特雷西斯的路線差異變得不可調和。她對博士的信任，是巴別塔悲劇最敏感的核心之一。",
        "- **關係雷點**：不要把她寫成只會被悼念的象徵。她是能做決定的人，也因此她的失敗才有重量。",
        "- **可寫衝突**：特蕾西婭明知理想會被戰爭吞噬，仍選擇相信一條更難的路；旁人因愛她而願意犧牲，卻未必真正理解她想要的未來。",
        "- **回查文本**：`working/Arknights/processed/priority_events/act33side_巴别塔.txt`。",
        "",
        "### 特雷西斯",
        "",
        "> 薩卡茲軍事路線的代表；特蕾西婭理念的對照面。",
        "",
        "- **核心動機**：特雷西斯不是只為征服而戰。他代表的是一種殘酷但有吸引力的現實判斷：薩卡茲長久受辱，沒有力量就沒有談判資格。",
        "- **舊債**：他與特蕾西婭的衝突像是同一個民族創傷的兩種答案。這比單純兄妹或王權內鬥更重要。",
        "- **關係雷點**：把他寫成純惡會變薄；把他洗成純粹救世也會失準。他的可怕之處在於，他的論點對許多薩卡茲有說服力。",
        "- **可寫衝突**：特雷西斯面對願意追隨特蕾西婭的人時，不只是在消滅敵人，也是在消滅另一種薩卡茲未來。",
        "- **回查文本**：`working/Arknights/processed/priority_events/act33side_巴别塔.txt`、`working/Arknights/processed/main_story/main_13_恶兆湍流.txt`。",
        "",
        "### W",
        "",
        "> 薩卡茲傭兵；巴別塔記憶與特蕾西婭之死的移動傷口。",
        "",
        "- **核心動機**：W 的笑與挑釁是防衛。她不輕易表達忠誠，但她會用危險、嘲諷和破壞去守住自己不肯承認的執念。",
        "- **舊債**：她承接了「W」這個名字，也承接了薩卡茲傭兵的生存規則。巴別塔讓她短暫看見戰爭之外的旗幟，這也是她後來難以放下的原因。",
        "- **關係雷點**：W 不等於瘋狂爆破愛好者。她可以很殘忍，但她對特蕾西婭、赫德雷、伊內絲與博士的反應，都有舊事在後面。",
        "- **可寫衝突**：W 用笑話逼博士或凱爾希承認舊事；她明明想留下，卻用最像背叛的方式表現關心。",
        "- **回查文本**：`working/Arknights/processed/priority_events/act9d0_生于黑夜.txt`、`working/Arknights/processed/priority_events/act33side_巴别塔.txt`。",
        "",
        "### 赫德雷",
        "",
        "> 薩卡茲傭兵指揮者；在生存、責任與信任間維持隊伍的人。",
        "",
        "- **核心動機**：赫德雷想讓隊伍活下去。他比 W 更像指揮者，比伊內絲更願意留下餘地，但這不代表他天真。",
        "- **舊債**：他在傭兵規則中長大，知道每一份合約都可能是陷阱。他選擇接納新的 W，本質上是一次風險判斷，也是一點不合時宜的信任。",
        "- **關係雷點**：他不是單純溫和老大哥。他能算價碼、談利益，也能在不知道整體局勢時承認自己掌握不足。",
        "- **可寫衝突**：赫德雷在保全隊伍與保全某個人之間做選擇；他知道信任很危險，卻仍必須有人先伸手。",
        "- **回查文本**：`working/Arknights/processed/priority_events/act9d0_生于黑夜.txt`。",
        "",
        "### 伊內絲",
        "",
        "> 薩卡茲情報與偵察者；把關心藏在懷疑之後的人。",
        "",
        "- **核心動機**：伊內絲的第一反應永遠是風險。她不相信來路不明的人，不相信漂亮承諾，也不相信自己能毫無代價地活下去。",
        "- **舊債**：她與赫德雷、W 的關係建立在戰場默契與互相拆臺上。她的尖刻常是提醒，而不是單純惡意。",
        "- **關係雷點**：不要把她寫成只會吐槽的冷面角色。她感知危險，也感知人的不安；她只是很少把關心說成關心。",
        "- **可寫衝突**：伊內絲察覺同伴正在撒謊，卻選擇暫時不拆穿，因為任務比情緒更急。",
        "- **回查文本**：`working/Arknights/processed/priority_events/act9d0_生于黑夜.txt`、`working/Arknights/processed/main_story/main_12_惊霆无声.txt`。",
        "",
        "## 整合運動與龍門篇",
        "",
        "### 塔露拉",
        "",
        "> 整合運動領袖；感染者怒火、烏薩斯創傷與操控悲劇的交會點。",
        "",
        "- **核心動機**：塔露拉最初不是為了屠殺而存在。她身上同時有感染者解放的正當願望、對壓迫的憤怒，以及被操控後走向災難的悲劇。",
        "- **舊債**：她與陳的血緣 / 過去關係讓龍門篇不只是城市防衛戰，也是一場被政治拆散的親緣悲劇。",
        "- **關係雷點**：不要把整合運動全部壓縮成塔露拉的錯。她是悲劇核心，但感染者受壓迫的土壤是真實存在的。",
        "- **可寫衝突**：塔露拉清醒片刻，看見自己理想如何被復仇和外力扭曲；陳想救她，卻不能否認她造成的傷害。",
        "- **回查文本**：`working/Arknights/processed/main_story/main_8_怒号光明.txt`。",
        "",
        "### 霜星",
        "",
        "> 雪怪小隊領袖；整合運動中最能呈現『敵人也有要守護之人』的角色。",
        "",
        "- **核心動機**：霜星想保護自己的小隊與感染者同伴。她的敵意來自長期被壓迫後的現實，而不是抽象仇恨。",
        "- **舊債**：她與愛國者的關係讓整合運動擁有家庭感，也讓她的死亡不是戰利品，而是羅德島必須承受的道德重量。",
        "- **關係雷點**：不要只把她寫成悲情美化角色。她站在羅德島對面時是真的敵人，但她的死亡也真的讓羅德島無法輕鬆宣稱勝利。",
        "- **可寫衝突**：霜星與羅德島短暫互相理解，卻因立場和時間都太晚而無法同行。",
        "- **回查文本**：`working/Arknights/processed/main_story/main_6_局部坏死.txt`。",
        "",
        "### 愛國者",
        "",
        "> 游擊隊領袖；老兵、父親與感染者抵抗意志的集合。",
        "",
        "- **核心動機**：愛國者想保護感染者與自己的隊伍，也想維持一種老派軍人的尊嚴。他知道整合運動有問題，但仍被歷史和責任綁在那裡。",
        "- **舊債**：他是烏薩斯暴力和感染者抵抗史的活證。他越強，越顯示羅德島勝利不是正義碾壓邪惡，而是另一種悲劇必要性。",
        "- **關係雷點**：不要把他寫成只會高喊信念的巨人。他的父性、疲憊、判斷和固執同樣重要。",
        "- **可寫衝突**：愛國者明知前路錯誤仍選擇戰到最後，因為他不能丟下那些仍把他當旗幟的人。",
        "- **回查文本**：`working/Arknights/processed/main_story/main_7_苦难摇篮.txt`。",
        "",
        "### 陳",
        "",
        "> 龍門近衛局督察；秩序、親緣與個人正義的衝突點。",
        "",
        "- **核心動機**：陳相信法律與行動，厭惡空談。她想守住龍門，但也無法對龍門制度裡的冷酷完全視而不見。",
        "- **舊債**：塔露拉讓陳的故事從警察職責變成親緣與政治創傷。她越堅持秩序，越必須面對秩序曾經如何傷害自己身邊的人。",
        "- **關係雷點**：陳不是單純衝動警察。她會衝，但她的衝動常來自無法接受制度把人當成本。",
        "- **可寫衝突**：陳在魏彥吾、近衛局、羅德島與塔露拉之間，被迫判斷『合法』和『正確』是不是同一件事。",
        "- **回查文本**：`working/Arknights/processed/main_story/main_5_靶向药物.txt`、`working/Arknights/processed/main_story/main_8_怒号光明.txt`。",
        "",
        "## 萊茵生命與哥倫比亞",
        "",
        "### 塞雷婭",
        "",
        "> 前萊茵生命防衛科主任；控制、責任與保護欲的集合。",
        "",
        "- **核心動機**：塞雷婭想阻止萊茵生命把人當實驗材料，也想守住她認為自己應該負責的人。她的保護常帶有強硬控制感，因為她習慣先處理風險，再處理情緒。",
        "- **舊債**：伊芙利特事件讓她與赫默、萊茵生命決裂，也讓她不再能把公司內部問題視為單純制度缺陷。",
        "- **關係雷點**：塞雷婭不是單純可靠監護人。她會為保護而隱瞞，為避免失控而壓制別人的選擇。",
        "- **可寫衝突**：塞雷婭明知赫默需要自主判斷，卻仍想用最安全的方式替她排除危險。",
        "- **回查文本**：`working/Arknights/processed/priority_events/act25side_孤星.txt`。",
        "",
        "### 赫默",
        "",
        "> 萊茵生命研究者；從旁觀科學家轉向倫理承擔的人。",
        "",
        "- **核心動機**：赫默想保護伊芙利特，也想證明科學不該只服務公司野心。她的成長重點是從『做正確研究』走向『為研究後果負責』。",
        "- **舊債**：伊芙利特使她無法再把自己放在中立研究者的位置。她對塞雷婭既依賴又抗拒，因為塞雷婭的保護也像另一種控制。",
        "- **關係雷點**：不要把赫默寫成只會溫柔照顧人。她的溫柔裡有非常強的倫理固執，必要時會反抗比自己更強勢的人。",
        "- **可寫衝突**：赫默面對萊茵生命的新計畫，必須判斷自己留下監督是否也在替公司維持運轉。",
        "- **回查文本**：`working/Arknights/processed/priority_events/act25side_孤星.txt`。",
        "",
        "### 伊芙利特",
        "",
        "> 萊茵生命實驗受害者；力量、創傷與被照顧者自主性的矛盾點。",
        "",
        "- **核心動機**：伊芙利特想被當成一個人，而不是危險源或病歷。她的粗暴常是對恐懼與不安的直接反應。",
        "- **舊債**：她的存在逼赫默與塞雷婭面對萊茵生命的倫理失敗。她不是被拯救後就完好的孩子，而是持續承受實驗後果的人。",
        "- **關係雷點**：不要只把她寫成任性小孩或火力單位。她的自尊、恐懼和被監護的窒息感同樣重要。",
        "- **可寫衝突**：伊芙利特想證明自己能做選擇，赫默和塞雷婭卻都害怕她受傷或失控。",
        "- **回查文本**：`working/Arknights/processed/priority_events/act25side_孤星.txt`。",
        "",
        "### 繆爾賽思",
        "",
        "> 萊茵生命生態科主任；親近、孤獨與非人感的混合體。",
        "",
        "- **核心動機**：繆爾賽思渴望連結，但她理解世界的方式和普通人不同。她的親近常帶著試探，像在確認自己能不能被接納。",
        "- **舊債**：孤星讓她站在科技與生命定義的邊界上；她不是單純公司高層，而是萊茵生命最能把『研究對象』與『自我』混在一起的人。",
        "- **關係雷點**：不要只寫成輕浮或黏人。她的玩笑下有孤獨，對赫默、塞雷婭等人的靠近也常帶著對自身位置的不安。",
        "- **可寫衝突**：繆爾賽思想加入人群，卻發現自己的能力與本質會讓旁人本能地保持距離。",
        "- **回查文本**：`working/Arknights/processed/priority_events/act25side_孤星.txt`。",
        "",
        "## 深海、伊比利亞與海嗣",
        "",
        "### 斯卡蒂",
        "",
        "> 深海獵人；孤獨的守護者與潛在災厄的同體。",
        "",
        "- **核心動機**：斯卡蒂想遠離他人，因為靠近意味著風險。她的沉默不是沒有情感，而是知道自己可能帶來不該由別人承受的後果。",
        "- **舊債**：深海獵人的身體與海嗣問題讓她永遠處在『人類守護者』和『非人未來』之間。",
        "- **關係雷點**：不要只寫成孤高強者。她的力量本身就是悲劇來源，她越在意某人，越可能選擇離開。",
        "- **可寫衝突**：斯卡蒂想保護普通人，卻必須隱瞞自己可能正是災難入口。",
        "- **回查文本**：`working/Arknights/processed/priority_events/act17side_愚人号.txt`。",
        "",
        "### 歌蕾蒂婭",
        "",
        "> 深海獵人指揮者；優雅、冷酷與責任並存。",
        "",
        "- **核心動機**：歌蕾蒂婭把深海獵人的存續與任務放在個人情緒之前。她的優雅不是裝飾，而是對失控世界維持秩序的方式。",
        "- **舊債**：她知道比艾麗妮等岸上人更多的真相，也知道深海獵人不是乾淨的英雄。",
        "- **關係雷點**：不要把她寫成只會發號施令的貴族式角色。她冷，是因為她正在管理不能說破的恐懼。",
        "- **可寫衝突**：歌蕾蒂婭必須在保護深海獵人成員與保護地表文明之間做不可能的取捨。",
        "- **回查文本**：`working/Arknights/processed/priority_events/act17side_愚人号.txt`。",
        "",
        "### 艾麗妮",
        "",
        "> 前伊比利亞審判官；從律法確信走向世界恐懼的人。",
        "",
        "- **核心動機**：艾麗妮相信審判庭與律法，但愚人號讓她看見海洋威脅遠大於她原本理解的罪與罰。",
        "- **舊債**：她師承審判庭，也承接伊比利亞對海洋的創傷。她的成長不是背棄律法，而是理解律法之外還有更大的黑暗。",
        "- **關係雷點**：不要只寫成正義新人。她有驕傲、有恐懼，也會因知道太少而做出過度簡化的判斷。",
        "- **可寫衝突**：艾麗妮面對深海獵人時，必須承認自己所學的審判語言不足以處理所有怪物。",
        "- **回查文本**：`working/Arknights/processed/priority_events/act17side_愚人号.txt`。",
        "",
        "## 卡西米爾、敘拉古與拉特蘭",
        "",
        "### 瑪嘉烈・臨光",
        "",
        "> 耀騎士；把騎士理想帶回商業化國家的逆行者。",
        "",
        "- **核心動機**：臨光相信騎士應為他人而戰。她不是不知道卡西米爾已經把騎士變成商品，而是選擇用自己的存在證明另一種騎士仍可能成立。",
        "- **舊債**：她與臨光家、卡西米爾騎士制度、感染者騎士和羅德島都有關。她的理想每次落地都會撞上商業和政治。",
        "- **關係雷點**：不要把她寫成單純陽光聖騎士。她也知道自己的光會被消費、被利用，甚至會讓追隨者陷入危險。",
        "- **可寫衝突**：臨光在公開賽場上勝利，卻發現勝利本身也可能被商業聯合會包裝成商品。",
        "- **回查文本**：`working/Arknights/processed/priority_events/act13side_长夜临光.txt`、`working/Arknights/processed/main_story/main_1_黑暗时代·下.txt`。",
        "",
        "### 德克薩斯",
        "",
        "> 企鵝物流成員；逃離家族後仍被故鄉認出的敘拉古人。",
        "",
        "- **核心動機**：德克薩斯想把自己從敘拉古家族秩序中切開，活成現在的自己。她的冷淡常是拒絕過去重新命名她。",
        "- **舊債**：敘拉古人讓她面對家族、血統、舊友與暴力規則。她不是忘了過去，而是不願讓過去決定現在。",
        "- **關係雷點**：不要把她寫成無感酷哥。她的沉默是高度自制，尤其面對拉普蘭德時更像一種避免被拖回舊世界的防線。",
        "- **可寫衝突**：德克薩斯為了保護現在的同伴，必須短暫使用她一直想丟掉的敘拉古手段。",
        "- **回查文本**：`working/Arknights/processed/priority_events/act21side_叙拉古人.txt`。",
        "",
        "### 拉普蘭德",
        "",
        "> 敘拉古舊日暴力的追跡者；德克薩斯過去的活證。",
        "",
        "- **核心動機**：拉普蘭德想逼德克薩斯承認她沒有真正離開。她的瘋癲感不是亂來，而是用暴力和挑釁撕開對方維持的平靜。",
        "- **舊債**：她和德克薩斯共享敘拉古的家族邏輯；她像一個不肯讓故事結束的過去。",
        "- **關係雷點**：不要只寫成病嬌追逐。拉普蘭德的危險在於她懂德克薩斯，也懂敘拉古的規則。",
        "- **可寫衝突**：拉普蘭德幫了企鵝物流，卻用最像威脅的方式表現自己的靠近。",
        "- **回查文本**：`working/Arknights/processed/priority_events/act21side_叙拉古人.txt`。",
        "",
        "### 莫斯提馬",
        "",
        "> 墮天使般的拉特蘭信使；舊小隊裂痕與律法例外的承載者。",
        "",
        "- **核心動機**：莫斯提馬把很多事情藏在輕鬆態度後面。她知道自己是例外，也知道例外會讓身邊的人持續受傷。",
        "- **舊債**：她與菲亞梅塔、蕾繆安、安多恩的舊事，是拉特蘭線最私人也最制度性的傷口。",
        "- **關係雷點**：不要只寫成神秘散漫旅人。她的散漫是一種不讓人靠近核心傷口的方式。",
        "- **可寫衝突**：莫斯提馬知道真相的一部分，卻選擇不解釋，因為解釋也無法把舊小隊帶回從前。",
        "- **回查文本**：`working/Arknights/processed/priority_events/act16side_吾导先路.txt`。",
        "",
        "### 菲亞梅塔",
        "",
        "> 追著莫斯提馬與舊事不放的拉特蘭局外人。",
        "",
        "- **核心動機**：菲亞梅塔想要答案，也想要一種遲來的公平。她的憤怒不是任性，而是因為她被迫在事件後果裡活了太久。",
        "- **舊債**：她不是薩科塔，卻被拉特蘭、律法與舊小隊事件深深捲入。她的位置天然帶有局外人痛感。",
        "- **關係雷點**：不要把她寫成只會暴躁。她的追問是對友情、責任與真相的堅持。",
        "- **可寫衝突**：菲亞梅塔終於得到解釋，卻發現解釋不能修復失去的時間與信任。",
        "- **回查文本**：`working/Arknights/processed/priority_events/act16side_吾导先路.txt`。",
        "",
        "### 安多恩",
        "",
        "> 質疑拉特蘭律法邊界的叛離者。",
        "",
        "- **核心動機**：安多恩不是單純反派。他看到拉特蘭律法照亮薩科塔，卻照不到其他受苦者，因此選擇用極端方式逼制度回答。",
        "- **舊債**：他與莫斯提馬、菲亞梅塔的舊小隊創傷，讓他的理念不是抽象政治，而是從私人破裂裡長出來的問題。",
        "- **關係雷點**：不要把他寫成單純溫柔革命者。他的問題有力量，但手段會把旁人拖進代價。",
        "- **可寫衝突**：安多恩救助被律法排除的人，同時傷害仍珍惜他的人。",
        "- **回查文本**：`working/Arknights/processed/priority_events/act16side_吾导先路.txt`。",
        "",
        "## 使用方式",
        "",
        "- 寫角色前先選壓力來源：疾病、國家、戰爭、舊債、組織命令、親密關係，至少要有兩個同時作用。",
        "- 角色的台詞可以少解釋，但行動要承認代價。明日方舟的角色常把真心藏在任務、命令、嘲諷或沉默裡。",
        "- 若要改寫或續寫，先決定角色是否知道真相。資訊差比戰鬥勝負更能推動這個世界的劇情。",
        "",
    ]
    write(OUT / "character_deep_dive.md", "\n".join(lines))


def build_index() -> None:
    files = [
        ("synopsis.md", "5–10 分鐘速覽與同人寫作核心張力。"),
        ("main_story_outline.md", "主線弧線、章節文本量與高頻說話者。"),
        ("activity_story_outline.md", "重點活動線整理：巴別塔、孤星、愚人號等同人關鍵篇章。"),
        ("relationship_map.md", "角色關係與衝突圖，整理同人可用的壓力點。"),
        ("character_deep_dive.md", "核心人物深挖包：動機、舊債、關係雷點與可寫衝突。"),
        ("characters.md", "干員與 NPC 人物詞條。"),
        ("factions.md", "國家、組織、地區與小隊。"),
        ("events.md", "主線、活動與小故事入口。"),
        ("places.md", "國家 / 地區與劇情區域。"),
        ("items.md", "敘事關鍵物件與技術。"),
        ("concepts.md", "源石、礦石病、天災等核心設定。"),
        ("timeline.md", "主線分期與活動發布序列。"),
        ("fanfic_notes.md", "同人小說用的關係、禁忌與切入角度。"),
    ]
    lines = ["# 《明日方舟》資料索引", "", "> 來源：Kengxxiao/ArknightsGameData CN `Client:2.7.41 Data:26-06-23-12-12-11_556baa`。", ""]
    for fn, desc in files:
        lines.append(f"- [{fn}]({fn}) — {desc}")
    write(OUT / "index.md", "\n".join(lines))


def build_fanfic_notes() -> None:
    lines = ["# 《明日方舟》同人小說寫作筆記", "", "## 核心原則", "", "- **先選國家，再選事件**：泰拉人物的行動通常被國家制度、感染者身分與災害經濟推動。只寫個人恩怨會變薄。", "- **感染者不是單一階級**：同樣是感染者，羅德島醫療幹員、烏薩斯難民、薩卡茲傭兵、整合運動殘黨的處境完全不同。", "- **羅德島不是無敵中立地帶**：它能提供醫療與庇護，但跨國行動必然牽動外交、軍事與情報代價。", "- **博士適合當視角，但不宜全知**：失憶讓博士能重新理解世界；寫作時保留資訊落差，比讓博士解釋一切更接近原作味道。", "", "## 好用的衝突模板", "", "- **醫療 vs 治安**：感染者需要治療，但城市管理者只看到風險。龍門、烏薩斯、維多利亞都能套用。", "- **救援 vs 主權**：羅德島想救人，當地政府不願外部武裝介入。", "- **個人善意 vs 組織命令**：幹員想留下救某個人，但任務要求撤退。", "- **歷史仇恨 vs 當下合作**：薩卡茲、拉特蘭、維多利亞線特別適合。", "- **源石技術的便利 vs 感染風險**：城市需要源石維持生活，卻把因此染病的人排除。", "", "## 角色關係支點", "", "- **博士 / 阿米婭**：信任與舊債。阿米婭相信博士，但博士不知道自己是否配得上這份信任。", "- **博士 / 凱爾希**：合作與審判。凱爾希需要博士的能力，也始終記得博士過去的重量。", "- **阿米婭 / 薩卡茲王權**：少女領袖與君王力量的矛盾，是溫柔被迫承擔暴力的核心。", "- **陳 / 龍門**：秩序、血緣、警察倫理與個人正義互相拉扯。", "- **W / 巴別塔**：玩世不恭外表下，是對舊日戰爭與特蕾西婭之死的執念。", "", "## 避免踩雷", "", "- 不要把礦石病寫成單純超能力代價；它首先是疾病與社會排斥。", "- 不要讓羅德島輕易推翻國家；原作的重量感來自「能救一部分人，但不能立刻修好世界」。", "- 不要把整合運動全員寫成惡人；也不要洗掉其造成的屠殺與創傷。", "- 不要讓所有幹員都用同一種現代口吻；不同國家、階級、職業的語氣差異很重要。", ""]
    write(OUT / "fanfic_notes.md", "\n".join(lines))


def main() -> None:
    chars = load_json("character_table.json")
    handbook_info = load_json("handbook_info_table.json")
    teams = load_json("handbook_team_table.json")
    story_review = load_json("story_review_table.json")
    zones = load_json("zone_table.json")

    OUT.mkdir(parents=True, exist_ok=True)
    build_characters(chars, handbook_info.get("handbookDict", {}), handbook_info.get("npcDict", {}), teams)
    build_factions(teams)
    build_events(story_review)
    build_places(zones, teams)
    build_items_and_concepts()
    build_main_story_outline()
    build_activity_story_outline(story_review)
    build_timeline(story_review)
    build_synopsis_stub()
    build_relationship_map()
    build_character_deep_dive()
    build_fanfic_notes()
    build_index()
    print(f"Wrote Arknights results to {OUT}")


if __name__ == "__main__":
    main()

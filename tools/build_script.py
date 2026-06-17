from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parent / "rebirth_system_xuanhuan_1m" / "exports" / "novel_full.txt"
OUT = ROOT / "data" / "script.json"
MANIFEST_OUT = ROOT / "data" / "manifest.json"
CHAPTER_DIR = ROOT / "data" / "chapters"

CHAPTER_RE = re.compile(r"^第[一二三四五六七八九十百千万零〇两\d]+章\s+(.+)$")
QUOTE_RE = re.compile(r"^[“\"].+[”\"]$")


BACKGROUND_RULES = [
    (
        "reverse_causality_space",
        re.compile(r"逆转因果|重生开始|绑定失败|备用方案|目标时间|宿主已死亡"),
    ),
    (
        "system_mission_panel",
        re.compile(r"任务|奖励|完成|领取|触发|结算|评级"),
    ),
    (
        "causality_debt_ledger",
        re.compile(r"因果点|因果|清算|债|债户|债主|旧账|清账"),
    ),
    (
        "shock_value_surge",
        re.compile(r"震惊值|显圣值|显圣|震惊|敬畏|信服"),
    ),
    (
        "system_interface",
        re.compile(r"【|系统|万象借势|震惊值|显圣值|因果点|任务|绑定"),
    ),
    (
        "return_zero_gate",
        re.compile(r"归零之门|天命退位|新秩序|众生自证|因果之主|拒绝成为新天命"),
    ),
    (
        "outer_heaven_battlefield",
        re.compile(r"天外战场|星墟古道|无光天幕|界外|诸神|诸界|天命军|战舰"),
    ),
    (
        "burial_emperor_plain",
        re.compile(r"葬帝原|埋骨|尸骨|失败救世者|上一纪元|墓|帝骨"),
    ),
    (
        "ancient_world_gate",
        re.compile(r"古界|古族|祖脉|血脉|传承|老祖|古界开门"),
    ),
    (
        "tianjiao_banquet",
        re.compile(r"天骄宴|九州天骄|天骄大会|赌盘|排名|天骄榜|万宗"),
    ),
    (
        "ancient_battlefield",
        re.compile(r"古战场|禁区|断天岭|黑碑林|血月湖|无声谷|战场|残骸"),
    ),
    (
        "sacrifice_hall",
        re.compile(r"鼎炉|祭台|祭火|镇魂钉|玄骨|圣殿|封帝祭坛|祭品|魂飞魄散"),
    ),
    (
        "rebirth_room",
        re.compile(r"夜雨|油灯|床边|药|床沿|窗外|大比前夜|小竹|屋内|木气"),
    ),
    (
        "qinglan_city_night",
        re.compile(r"城中|街|灯笼|雨夜"),
    ),
    (
        "lin_family_hall",
        re.compile(r"退婚|婚书|休书|信物|林家|林清雪"),
    ),
    (
        "lu_family_hall",
        re.compile(r"族堂|族老|账册|少主令|母亲遗物|二房|陆承远"),
    ),
    (
        "pill_pavilion",
        re.compile(r"丹阁|丹方|丹药|丹炉|炼丹|炸炉|丹会|药阁"),
    ),
    (
        "law_enforcement_hall",
        re.compile(r"执法殿|宗规|长老派系|反审判|违规证据|赔罪"),
    ),
    (
        "sect_trial_realm",
        re.compile(r"秘境|试炼|新人考核|源头|灵根|灵脉|灵草|山谷"),
    ),
    (
        "royal_court",
        re.compile(r"王朝|大乾|朝堂|皇室|女帝|登基|皇城|兵权"),
    ),
    (
        "sacred_judgement_hall",
        re.compile(r"圣地|神子|圣女|审判|天命碑|三十三天阙|太初道场|神子试炼"),
    ),
    (
        "qinglan_zong_gate",
        re.compile(r"青岚宗|山门|外门|内门|宗门|考核|祖地|威压阵|执法殿"),
    ),
    (
        "clan_stage",
        re.compile(r"陆家大比|演武场|族老|少主令|陆川|陆承远|青岚城|陆家"),
    ),
]

CHARACTER_RULES = {
    "lu_chenyuan": re.compile(r"陆沉渊|少主"),
    "lin_qingxue": re.compile(r"林清雪|清雪|未婚妻"),
    "qin_wuque": re.compile(r"秦无缺|无缺|天命圣子"),
    "yunheng_zhenren": re.compile(r"云衡真人|云衡|师尊|真人"),
    "xiaozhu": re.compile(r"小竹|丫鬟"),
    "shen_qingluan": re.compile(r"沈清鸾|圣女"),
    "lu_chuan": re.compile(r"陆川|堂弟"),
    "lu_chengyuan": re.compile(r"陆承远|二叔|二爷"),
}

SPEAKER_HINTS = {
    "陆沉渊": re.compile(r"陆沉渊|他笑|他声音|他嘶声|他低吼|主角"),
    "林清雪": re.compile(r"林清雪|清雪|她抬起眼|她终究"),
    "秦无缺": re.compile(r"秦无缺|无缺|金袍"),
    "云衡真人": re.compile(r"云衡真人|师尊|真人"),
    "小竹": re.compile(r"小竹|丫鬟"),
    "沈清鸾": re.compile(r"沈清鸾|圣女"),
    "陆川": re.compile(r"陆川|堂弟"),
    "陆承远": re.compile(r"陆承远|二叔|二爷"),
}


@dataclass
class Beat:
    id: str
    text: str
    kind: str
    speaker: str
    background: str
    characters: list[str]


def normalize_text(raw: str) -> str:
    raw = raw.replace("\ufeff", "")
    raw = raw.replace("\r\n", "\n").replace("\r", "\n")
    return raw.strip() + "\n"


def detect_background(text: str, current: str) -> str:
    for key, pattern in BACKGROUND_RULES:
        if pattern.search(text):
            return key
    return current or "key_art"


def detect_characters(text: str) -> list[str]:
    chars: list[str] = []
    for key, pattern in CHARACTER_RULES.items():
        if pattern.search(text):
            chars.append(key)
    return chars


def detect_speaker(text: str, previous: str) -> str:
    if text.startswith("【"):
        return "万象借势系统"
    if not QUOTE_RE.match(text):
        return ""
    context = previous[-160:]
    for speaker, pattern in SPEAKER_HINTS.items():
        if pattern.search(context):
            return speaker
    return ""


def split_chapters(text: str) -> list[dict]:
    lines = [line.strip() for line in text.splitlines()]
    title = lines[0] if lines else "万象清算：重生后我让天命退位"
    author = lines[1] if len(lines) > 1 and lines[1].startswith("作者") else ""

    chapters: list[dict] = []
    current: dict | None = None
    buffer: list[str] = []

    def flush() -> None:
        nonlocal current, buffer
        if current is None:
            return
        paragraphs = [p for p in buffer if p]
        current["paragraphs"] = paragraphs
        chapters.append(current)
        buffer = []

    for i, line in enumerate(lines):
        if i < 2 and (line == title or line == author):
            continue
        match = CHAPTER_RE.match(line)
        if match:
            flush()
            current = {
                "id": f"ch{len(chapters) + 1:04d}",
                "index": len(chapters) + 1,
                "title": line,
            }
            continue
        if current is None:
            if line:
                current = {"id": "ch0000", "index": 0, "title": "序章"}
                buffer.append(line)
            continue
        buffer.append(line)
    flush()

    return [
        {
            "meta": {
                "title": title,
                "author": author.replace("作者：", "") if author else "",
            },
            "chapters": chapters,
        }
    ][0]


def build() -> dict:
    raw = SOURCE.read_text(encoding="utf-8")
    normalized = normalize_text(raw)
    source_hash = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    split = split_chapters(normalized)

    total_beats = 0
    last_bg = "key_art"
    processed_chapters = []

    for chapter in split["chapters"]:
        beats: list[Beat] = []
        previous = ""
        for paragraph_index, text in enumerate(chapter["paragraphs"], start=1):
            bg = detect_background(text, last_bg)
            chars = detect_characters(text)
            speaker = detect_speaker(text, previous)
            kind = "system" if text.startswith("【") else "dialogue" if QUOTE_RE.match(text) else "narration"
            beat = Beat(
                id=f"{chapter['id']}_b{paragraph_index:04d}",
                text=text,
                kind=kind,
                speaker=speaker,
                background=bg,
                characters=chars,
            )
            beats.append(beat)
            total_beats += 1
            last_bg = bg
            previous += "\n" + text

        processed_chapters.append(
            {
                "id": chapter["id"],
                "index": chapter["index"],
                "title": chapter["title"],
                "beatCount": len(beats),
                "beats": [beat.__dict__ for beat in beats],
            }
        )

    payload = {
        "meta": {
            **split["meta"],
            "sourceFile": str(SOURCE),
            "sourceSha256": source_hash,
            "sourceCharacters": len(normalized),
            "chapterCount": len(processed_chapters),
            "beatCount": total_beats,
            "restorationPolicy": "Every displayed story beat stores an exact paragraph from novel_full.txt; scene, speaker, and asset cues are additive metadata only.",
        },
        "assets": {
            "backgrounds": {
                "key_art": "assets/backgrounds/key_art.png",
                "sacrifice_hall": "assets/backgrounds/sacrifice_hall.png",
                "rebirth_room": "assets/backgrounds/rebirth_room.png",
                "qinglan_city_night": "assets/backgrounds/qinglan_city_night.png",
                "lu_family_hall": "assets/backgrounds/lu_family_hall.png",
                "lin_family_hall": "assets/backgrounds/lin_family_hall.png",
                "clan_stage": "assets/backgrounds/clan_stage.png",
                "qinglan_zong_gate": "assets/backgrounds/qinglan_zong_gate.png",
                "law_enforcement_hall": "assets/backgrounds/law_enforcement_hall.png",
                "sect_trial_realm": "assets/backgrounds/sect_trial_realm.png",
                "pill_pavilion": "assets/backgrounds/pill_pavilion.png",
                "royal_court": "assets/backgrounds/royal_court.png",
                "sacred_judgement_hall": "assets/backgrounds/sacred_judgement_hall.png",
                "tianjiao_banquet": "assets/backgrounds/tianjiao_banquet.png",
                "ancient_world_gate": "assets/backgrounds/ancient_world_gate.png",
                "ancient_battlefield": "assets/backgrounds/ancient_battlefield.png",
                "burial_emperor_plain": "assets/backgrounds/burial_emperor_plain.png",
                "outer_heaven_battlefield": "assets/backgrounds/outer_heaven_battlefield.png",
                "return_zero_gate": "assets/backgrounds/return_zero_gate.png",
                "system_mission_panel": "assets/backgrounds/system_mission_panel.png",
                "causality_debt_ledger": "assets/backgrounds/causality_debt_ledger.png",
                "shock_value_surge": "assets/backgrounds/shock_value_surge.png",
                "reverse_causality_space": "assets/backgrounds/reverse_causality_space.png",
                "system_interface": "assets/backgrounds/system_interface.png",
                "system_void": "assets/backgrounds/system_void.png",
            },
            "characters": {
                "lu_chenyuan": "assets/characters/lu_chenyuan.png",
                "lin_qingxue": "assets/characters/lin_qingxue.png",
                "qin_wuque": "assets/characters/qin_wuque.png",
                "yunheng_zhenren": "assets/characters/yunheng_zhenren.png",
                "xiaozhu": "assets/characters/xiaozhu.png",
                "shen_qingluan": "assets/characters/shen_qingluan.png",
                "lu_chuan": "assets/characters/lu_chuan.png",
                "lu_chengyuan": "assets/characters/lu_chengyuan.png",
            },
        },
        "chapters": processed_chapters,
    }
    return payload


if __name__ == "__main__":
    payload = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    CHAPTER_DIR.mkdir(parents=True, exist_ok=True)

    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    for old in CHAPTER_DIR.glob("*.json"):
        old.unlink()

    chapter_summaries = []
    for chapter in payload["chapters"]:
        chapter_path = CHAPTER_DIR / f"{chapter['id']}.json"
        chapter_path.write_text(json.dumps(chapter, ensure_ascii=False, indent=2), encoding="utf-8")
        chapter_summaries.append(
            {
                "id": chapter["id"],
                "index": chapter["index"],
                "title": chapter["title"],
                "beatCount": chapter["beatCount"],
                "path": f"data/chapters/{chapter['id']}.json",
            }
        )

    manifest = {
        "meta": payload["meta"],
        "assets": payload["assets"],
        "chapters": chapter_summaries,
    }
    MANIFEST_OUT.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Wrote {OUT}")
    print(f"Wrote {MANIFEST_OUT}")
    print(f"Wrote {len(chapter_summaries)} chapter files to {CHAPTER_DIR}")
    print(f"chapters={payload['meta']['chapterCount']} beats={payload['meta']['beatCount']} sha256={payload['meta']['sourceSha256']}")

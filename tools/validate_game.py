from __future__ import annotations

import hashlib
import json
import struct
import sys
from pathlib import Path

from build_script import build, normalize_text


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "data" / "script.json"
MANIFEST_PATH = ROOT / "data" / "manifest.json"
SOURCE_PATH = ROOT.parent / "rebirth_system_xuanhuan_1m" / "exports" / "novel_full.txt"


def read_png_info(path: Path) -> dict:
    with path.open("rb") as fh:
        header = fh.read(32)
    if header[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"{path} is not a PNG")
    width, height, bit_depth, color_type = struct.unpack(">IIBB", header[16:26])
    return {
        "width": width,
        "height": height,
        "bitDepth": bit_depth,
        "colorType": color_type,
        "hasAlpha": color_type in (4, 6),
    }


def sha256_normalized(path: Path) -> str:
    text = normalize_text(path.read_text(encoding="utf-8"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def main() -> None:
    if not SOURCE_PATH.exists():
        fail(f"source novel missing: {SOURCE_PATH}")
    if not MANIFEST_PATH.exists():
        fail(f"manifest missing: {MANIFEST_PATH}")
    if not SCRIPT_PATH.exists():
        fail(f"script missing: {SCRIPT_PATH}")

    data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    full_script = json.loads(SCRIPT_PATH.read_text(encoding="utf-8"))
    rebuilt = build()

    if data["meta"]["sourceSha256"] != sha256_normalized(SOURCE_PATH):
        fail("manifest sourceSha256 does not match current source novel")
    if data["meta"]["sourceSha256"] != rebuilt["meta"]["sourceSha256"]:
        fail("rebuilt source hash mismatch")
    if full_script["meta"]["sourceSha256"] != data["meta"]["sourceSha256"]:
        fail("full script sourceSha256 does not match manifest")
    if data["meta"]["chapterCount"] != len(data["chapters"]):
        fail("chapterCount does not match chapters array")
    if data["meta"]["chapterCount"] != 430:
        fail(f"expected 430 chapters, got {data['meta']['chapterCount']}")

    text_count = 0
    for chapter_index, summary in enumerate(data["chapters"]):
        chapter_path = ROOT / summary["path"]
        if not chapter_path.exists():
            fail(f"chapter file missing: {summary['path']}")
        chapter = json.loads(chapter_path.read_text(encoding="utf-8"))
        rebuilt_chapter = rebuilt["chapters"][chapter_index]
        if summary["id"] != rebuilt_chapter["id"] or chapter["id"] != rebuilt_chapter["id"]:
            fail(f"chapter id mismatch at {chapter_index + 1}")
        if summary["title"] != rebuilt_chapter["title"]:
            fail(f"manifest chapter title mismatch at {chapter_index + 1}")
        if chapter["title"] != rebuilt_chapter["title"]:
            fail(f"chapter title mismatch at {chapter_index + 1}")
        if chapter["beatCount"] != len(chapter["beats"]):
            fail(f"beatCount mismatch in {chapter['title']}")
        if summary["beatCount"] != chapter["beatCount"]:
            fail(f"manifest beatCount mismatch in {chapter['title']}")
        if chapter["beatCount"] != rebuilt_chapter["beatCount"]:
            fail(f"rebuilt beat count mismatch in {chapter['title']}")
        if full_script["chapters"][chapter_index] != chapter:
            fail(f"full script and chapter file differ at {chapter['title']}")
        for beat_index, beat in enumerate(chapter["beats"]):
            if beat["text"] != rebuilt_chapter["beats"][beat_index]["text"]:
                fail(f"text mismatch at chapter {chapter_index + 1}, beat {beat_index + 1}")
            text_count += 1

    if text_count != data["meta"]["beatCount"]:
        fail("beatCount does not match actual total")

    checked_assets: list[str] = []
    for group, assets in data["assets"].items():
        for asset_id, relative in assets.items():
            path = ROOT / relative
            if not path.exists():
                fail(f"asset missing: {relative}")
            if path.stat().st_size <= 0:
                fail(f"asset is empty: {relative}")
            info = read_png_info(path)
            if info["width"] < 900 or info["height"] < 900:
                fail(f"asset resolution too small: {relative} {info['width']}x{info['height']}")
            if group == "characters" and not info["hasAlpha"]:
                fail(f"character sprite is not transparent PNG: {relative}")
            checked_assets.append(f"{relative} {info['width']}x{info['height']}")

    print("OK: source hash, manifest, per-chapter files, exact text mapping, and PNG assets verified")
    print(f"chapters={data['meta']['chapterCount']} beats={data['meta']['beatCount']} sha256={data['meta']['sourceSha256']}")
    for asset in checked_assets:
        print(f"asset={asset}")


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:
        print(f"FAIL: {exc}")
        sys.exit(1)

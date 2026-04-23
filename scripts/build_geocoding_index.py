"""位置参照情報 CSV → ブラウザ用ジオコーディング辞書 JSON。

街区レベル位置参照情報・大字・町丁目位置参照情報（国土交通省、2024年）の CSV を読み込み、
ブラウザで使える軽量な辞書 JSON を data/ 直下に生成する。

表記ゆれ（招堤↔招提、樟葉↔楠葉、星ケ丘↔星丘 など）は前処理段階で全バリエーションを
キー展開する方針。ブラウザ側は軽い正規化＋辞書 lookup で住所を解決できる。

出典:
  街区レベル位置参照情報 国土交通省（2024年）
  大字・町丁目位置参照情報 国土交通省（2024年）
  利用規約: https://nlftp.mlit.go.jp/isj/agreement.html
  （出典明記を条件に自由利用可。高精度測量用途には使用不可。）

編集・加工: hukushimap (aikautau) — build_geocoding_index.py
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

# scripts/geocode.py の正規化ロジックを再利用
from geocode import (
    GAIKU_CSV,
    OAZA_CSV,
    _ADDR_ALIASES,
    _normalize,
    _normalize_ke,
    _to_kanji,
)

ROOT = Path(__file__).resolve().parent.parent
OUT_GAIKU = ROOT / "data" / "geocoding_gaiku.json"
OUT_OAZA = ROOT / "data" / "geocoding_oaza.json"
OUT_TOWNS = ROOT / "data" / "geocoding_towns.json"

KEY_SEP = "\t"

LICENSE_META_GAIKU = {
    "_source": "街区レベル位置参照情報 国土交通省（2024年）",
    "_license": "出典明記を条件に自由利用可 https://nlftp.mlit.go.jp/isj/agreement.html",
    "_processed_by": "hukushimap (aikautau) — build_geocoding_index.py",
}

LICENSE_META_OAZA = {
    "_source": "大字・町丁目位置参照情報 国土交通省（2024年）",
    "_license": "出典明記を条件に自由利用可 https://nlftp.mlit.go.jp/isj/agreement.html",
    "_processed_by": "hukushimap (aikautau) — build_geocoding_index.py",
}


# ── キー展開 ──────────────────────────────────────

import re as _re


def _expand_town_variants(town: str) -> list[str]:
    """1つの町名から表記ゆれの全バリエーションを生成。

    - _ADDR_ALIASES に登録された表記ゆれの両方（招堤↔招提、樟葉↔楠葉、星ケ丘↔星丘）
    - N丁目 ↔ 漢数字丁目 の両方
    - ヶ↔ケ の両方（ADDR_ALIASES で "星ケ丘" が混入した後にも適用されるよう最後に行う）
    """
    variants = {town}

    # ADDR_ALIASES 双方向展開
    expanded: set[str] = set()
    for v in variants:
        expanded.add(v)
        for a, b in _ADDR_ALIASES:
            if a in v:
                expanded.add(v.replace(a, b))
            if b in v:
                expanded.add(v.replace(b, a))
    variants = expanded

    # 「N丁目」を「漢数字丁目」に展開、および逆方向
    expanded = set()
    for v in variants:
        expanded.add(v)
        for n in range(1, 21):
            k = _to_kanji(n) + "丁目"
            if k in v:
                expanded.add(v.replace(k, str(n) + "丁目"))
        m = _re.search(r"(\d+)丁目", v)
        if m:
            n = int(m.group(1))
            expanded.add(v.replace(m.group(0), _to_kanji(n) + "丁目"))
    variants = expanded

    # ヶ↔ケ 展開（最後に適用：先行パスで新しく生まれた "ケ" もカバー）
    expanded = set()
    for v in variants:
        expanded.add(v)
        if "ケ" in v:
            expanded.add(v.replace("ケ", "ヶ"))
        if "ヶ" in v:
            expanded.add(v.replace("ヶ", "ケ"))
    variants = expanded

    return sorted(variants)


# ── CSV 読み込み（geocode.py と同等だが、正規化をキー展開しやすいように分離） ──

def load_gaiku_raw(path: Path) -> list[tuple[str, str, float, float]]:
    """(町名, 街区符号, lon, lat) のリスト。代表フラグ優先。"""
    rows: dict[tuple[str, str], tuple[float, float]] = {}
    representative: set[tuple[str, str]] = set()
    with open(path, encoding="cp932") as f:
        for row in csv.DictReader(f):
            town = _normalize_ke(row["大字・丁目名"].strip())
            block = _normalize(row["街区符号・地番"].strip())
            lat, lon = row["緯度"].strip(), row["経度"].strip()
            if not lat or not lon:
                continue
            key = (town, block)
            is_rep = row.get("代表フラグ", "").strip() == "1"
            # 代表フラグを優先、無ければ最初のものを残す
            if key not in rows or (is_rep and key not in representative):
                rows[key] = (float(lon), float(lat))
                if is_rep:
                    representative.add(key)
    return [(t, b, lon, lat) for (t, b), (lon, lat) in rows.items()]


def load_oaza_raw(path: Path) -> list[tuple[str, float, float]]:
    """(町名, lon, lat) のリスト。"""
    rows: dict[str, tuple[float, float]] = {}
    with open(path, encoding="cp932") as f:
        for row in csv.DictReader(f):
            town = _normalize_ke(row["大字町丁目名"].strip())
            lat, lon = row["緯度"].strip(), row["経度"].strip()
            if not lat or not lon:
                continue
            rows.setdefault(town, (float(lon), float(lat)))
    return [(t, lon, lat) for t, (lon, lat) in rows.items()]


# ── メイン ──────────────────────────────────────

def build_gaiku_dict(raw: list[tuple[str, str, float, float]]) -> dict[str, list[float]]:
    """街区辞書を全バリエーション展開して構築。"""
    out: dict[str, list[float]] = {}
    for town, block, lon, lat in raw:
        coord = [round(lon, 6), round(lat, 6)]
        for variant in _expand_town_variants(town):
            key = variant + KEY_SEP + block
            out.setdefault(key, coord)
    return out


def build_oaza_dict(raw: list[tuple[str, float, float]]) -> dict[str, list[float]]:
    """大字辞書を全バリエーション展開して構築。"""
    out: dict[str, list[float]] = {}
    for town, lon, lat in raw:
        coord = [round(lon, 6), round(lat, 6)]
        for variant in _expand_town_variants(town):
            out.setdefault(variant, coord)
    return out


def build_towns_list(
    gaiku_raw: list[tuple[str, str, float, float]],
    oaza_raw: list[tuple[str, float, float]],
) -> list[str]:
    """全バリエーション展開した町名配列（長さ降順、最長一致用）。"""
    towns: set[str] = set()
    for town, _, _, _ in gaiku_raw:
        for v in _expand_town_variants(town):
            towns.add(v)
    for town, _, _ in oaza_raw:
        for v in _expand_town_variants(town):
            towns.add(v)
    return sorted(towns, key=lambda s: (-len(s), s))


def dump_json(path: Path, obj: dict | list) -> int:
    """minify JSON を書き出し、サイズをバイト数で返す。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))
    return path.stat().st_size


def main() -> int:
    for p in (GAIKU_CSV, OAZA_CSV):
        if not p.exists():
            print(f"[error] {p} が見つかりません。", file=sys.stderr)
            return 1

    print("位置参照情報 CSV を読み込み中...")
    gaiku_raw = load_gaiku_raw(GAIKU_CSV)
    oaza_raw = load_oaza_raw(OAZA_CSV)
    print(f"  街区レベル: {len(gaiku_raw)} 行, 大字レベル: {len(oaza_raw)} 行")

    print("表記ゆれを展開して辞書を構築中...")
    gaiku_dict = build_gaiku_dict(gaiku_raw)
    oaza_dict = build_oaza_dict(oaza_raw)
    towns = build_towns_list(gaiku_raw, oaza_raw)
    print(f"  街区辞書: {len(gaiku_dict)} キー, 大字辞書: {len(oaza_dict)} キー, 町名: {len(towns)} 種")

    # ライセンスメタデータを先頭に含める
    gaiku_out: dict = {**LICENSE_META_GAIKU, **gaiku_dict}
    oaza_out: dict = {**LICENSE_META_OAZA, **oaza_dict}

    size_g = dump_json(OUT_GAIKU, gaiku_out)
    size_o = dump_json(OUT_OAZA, oaza_out)
    size_t = dump_json(OUT_TOWNS, towns)

    print("\n生成物:")
    print(f"  {OUT_GAIKU.relative_to(ROOT)}  {size_g / 1024:.1f} KB")
    print(f"  {OUT_OAZA.relative_to(ROOT)}  {size_o / 1024:.1f} KB")
    print(f"  {OUT_TOWNS.relative_to(ROOT)}  {size_t / 1024:.1f} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())

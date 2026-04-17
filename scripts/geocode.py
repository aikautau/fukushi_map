"""位置参照情報（国土地理院）を使ったローカルジオコーディング。

街区レベル (23.0a) と大字レベル (18.0b) の CSV で住所→座標を解決する。
API 不要・レート制限なし。
"""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
IN_CSV = ROOT / "data" / "processed" / "jigyosho.csv"
OUT_GEOJSON = ROOT / "data" / "processed" / "jigyosho.geojson"

GAIKU_CSV = ROOT / "data" / "geodata" / "27210-23.0a" / "27210_2024.csv"
OAZA_CSV = ROOT / "data" / "geodata" / "27210-18.0b" / "27210_2024.csv"

KANJI_DIGITS = "〇一二三四五六七八九"


def _to_kanji(n: int) -> str:
    if 1 <= n <= 9:
        return KANJI_DIGITS[n]
    if n == 10:
        return "十"
    if 11 <= n <= 19:
        return "十" + KANJI_DIGITS[n - 10]
    if 20 <= n <= 99:
        t, o = divmod(n, 10)
        return KANJI_DIGITS[t] + "十" + (KANJI_DIGITS[o] if o else "")
    return str(n)


def _normalize(s: str) -> str:
    for z, h in zip("０１２３４５６７８９", "0123456789"):
        s = s.replace(z, h)
    for c in "－ー−‐—–":
        s = s.replace(c, "-")
    return s


def _normalize_ke(s: str) -> str:
    return s.replace("ヶ", "ケ").replace("ｹ", "ケ").replace("が", "ケ")


# 枚方市の住所で頻出する表記ゆれ
_ADDR_ALIASES = [
    ("招堤", "招提"),       # 堤↔提 の混同
    ("樟葉", "楠葉"),       # 旧字↔現行字
    ("星ケ丘", "星丘"),      # ケ が入る表記ゆれ
    ("津田餅", "津田元町"),   # 入力ミス
]

_ADDR_ALIASES_RE = [
    (re.compile(r"(?<!楠葉)花園町"), "楠葉花園町"),  # 楠葉 の省略（既に楠葉花園町なら変換しない）
]


def _normalize_addr_aliases(s: str) -> str:
    for wrong, right in _ADDR_ALIASES:
        s = s.replace(wrong, right)
    for pat, repl in _ADDR_ALIASES_RE:
        s = pat.sub(repl, s)
    return s


# ── データ読み込み ──────────────────────────────────────

def load_gaiku(path: Path) -> dict[tuple[str, str], tuple[float, float]]:
    """{(町名, 街区符号): (lat, lon)}。代表フラグ=1 を優先。"""
    lookup: dict[tuple[str, str], tuple[float, float]] = {}
    with open(path, encoding="cp932") as f:
        for row in csv.DictReader(f):
            town = _normalize_ke(row["大字・丁目名"].strip())
            block = _normalize(row["街区符号・地番"].strip())
            lat, lon = row["緯度"].strip(), row["経度"].strip()
            if not lat or not lon:
                continue
            key = (town, block)
            if key not in lookup or row.get("代表フラグ", "").strip() == "1":
                lookup[key] = (float(lat), float(lon))
    return lookup


def load_oaza(path: Path) -> dict[str, tuple[float, float]]:
    """{町名: (lat, lon)}。"""
    lookup: dict[str, tuple[float, float]] = {}
    with open(path, encoding="cp932") as f:
        for row in csv.DictReader(f):
            town = _normalize_ke(row["大字町丁目名"].strip())
            lat, lon = row["緯度"].strip(), row["経度"].strip()
            if not lat or not lon:
                continue
            lookup.setdefault(town, (float(lat), float(lon)))
    return lookup


# ── 住所パース ──────────────────────────────────────

def _strip_prefix(addr: str) -> str:
    addr = re.sub(r"^大阪府?枚方市", "", addr)
    addr = re.sub(r"^枚方市", "", addr)
    return addr


def _remove_duplicate(addr: str) -> str:
    """重複住所 (e.g. '養父東町65番1号大阪府枚方市養父東町65番1号') を除去。"""
    m = re.search(r"大阪府?枚方市", addr)
    if m:
        return addr[: m.start()].rstrip()
    return addr


def _extract_block(s: str) -> str:
    s = re.sub(r"^[番地のノ]+", "", s.strip())
    m = re.match(r"(\d+)", s)
    return m.group(1) if m else ""


def parse_address(addr: str, known_towns: set[str]) -> tuple[str, str]:
    """住所 → (町名, 街区番号)。"""
    addr = _normalize(addr)
    addr = _normalize_ke(addr)
    addr = _strip_prefix(addr)
    addr = _remove_duplicate(addr)
    addr = _normalize_addr_aliases(addr)

    # N丁 (目が抜けている) → N丁目 に補正
    addr = re.sub(r"(\d+)丁(\d)", r"\g<1>丁目\2", addr)

    # 明示的な N丁目 を漢数字に変換してマッチ
    chome = re.match(r"(.+?)(\d+)丁目(.*)$", addr)
    if chome:
        kanji_town = chome.group(1) + _to_kanji(int(chome.group(2))) + "丁目"
        if kanji_town in known_towns:
            return kanji_town, _extract_block(chome.group(3))

    # 最長一致で町名を探す
    best = ""
    for town in known_towns:
        if addr.startswith(town) and len(town) > len(best):
            best = town

    if best:
        rest = addr[len(best):]
        return best, _extract_block(rest)

    # 町名に丁目がない場合: 最初の数字を丁目と仮定して再試行
    # e.g. 茄子作1-43-35 → 茄子作一丁目, block=43
    m = re.match(r"([^\d]+?)(\d+)[-番](.*)$", addr)
    if m:
        base, first_num, rest = m.group(1), int(m.group(2)), m.group(3)
        candidate = base + _to_kanji(first_num) + "丁目"
        if candidate in known_towns:
            return candidate, _extract_block(rest)
        # 丁目ではなく直接番地の場合 (e.g. 伊加賀東町2-17)
        if base in known_towns:
            return base, str(first_num)

    # 町 suffix 補完 (e.g. 宇山東→宇山東町, 須山→須山町)
    m = re.match(r"([^\d]+?)(\d+)(.*)$", addr)
    if m:
        base, num, rest = m.group(1), m.group(2), m.group(3)
        if base + "町" in known_towns:
            return base + "町", num

    # 最終フォールバック: 数字の手前で分割
    m = re.match(r"([^\d]+?)(\d.*)$", addr)
    if m:
        return m.group(1), _extract_block(m.group(2))

    return addr, ""


# ── ジオコーディング ──────────────────────────────────

def geocode_one(
    addr: str,
    gaiku: dict[tuple[str, str], tuple[float, float]],
    oaza: dict[str, tuple[float, float]],
    known_towns: set[str],
) -> tuple[float, float, str] | None:
    town, block = parse_address(addr, known_towns)

    if block and (town, block) in gaiku:
        return (*gaiku[(town, block)], "gaiku")

    if town in oaza:
        return (*oaza[town], "oaza")

    # 丁目付き町名の基底部分で大字マッチ
    base = re.sub(r"[一二三四五六七八九十]+丁目$", "", town)
    if base != town and base in oaza:
        return (*oaza[base], "oaza_base")

    return None


# ── GeoJSON 出力 ──────────────────────────────────

def to_geojson(df: pd.DataFrame, out_path: Path) -> None:
    geo_df = df.dropna(subset=["lon", "lat"])
    features = []
    for _, row in geo_df.iterrows():
        def _s(val: object) -> str:
            if pd.isna(val):
                return ""
            return str(val)

        props = {
            "jigyosho_id": _s(row["jigyosho_id"]),
            "name": _s(row["name"]),
            "category": _s(row["category"]),
            "service_type": _s(row["service_type"]),
            "address_full": _s(row["address_full"]),
            "tel": _s(row.get("tel", "")),
            "capacity": _s(row.get("capacity", "")),
        }
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [row["lon"], row["lat"]]},
            "properties": props,
        })

    geojson = {
        "type": "FeatureCollection",
        "features": features,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)


# ── メイン ──────────────────────────────────────

def main() -> int:
    if not IN_CSV.exists():
        print(f"[error] {IN_CSV} が見つかりません。先に normalize.py を実行してください。", file=sys.stderr)
        return 1
    for p in (GAIKU_CSV, OAZA_CSV):
        if not p.exists():
            print(f"[error] {p} が見つかりません。data/geodata/ に位置参照情報を配置してください。", file=sys.stderr)
            return 1

    print("位置参照情報を読み込み中...")
    gaiku = load_gaiku(GAIKU_CSV)
    oaza = load_oaza(OAZA_CSV)
    known_towns = {t for t, _ in gaiku} | set(oaza)
    print(f"  街区レベル: {len(gaiku)} 件, 大字レベル: {len(oaza)} 件, 町名: {len(known_towns)} 種")

    df = pd.read_csv(IN_CSV, dtype=str)
    print(f"入力: {len(df)} 件\n")

    lons: list[float | None] = []
    lats: list[float | None] = []
    levels: list[str | None] = []
    stats = {"gaiku": 0, "oaza": 0, "oaza_base": 0, "fail": 0}

    for i, addr in enumerate(df["address_full"]):
        addr = str(addr).strip()
        result = geocode_one(addr, gaiku, oaza, known_towns)
        if result:
            lat, lon, level = result
            lats.append(lat)
            lons.append(lon)
            levels.append(level)
            stats[level] = stats.get(level, 0) + 1
        else:
            lats.append(None)
            lons.append(None)
            levels.append(None)
            stats["fail"] += 1

        done = i + 1
        if done % 100 == 0 or done == len(df):
            print(f"  進捗: {done}/{len(df)}", flush=True)

    df = df.copy()
    df["lon"] = lons
    df["lat"] = lats
    df["match_level"] = levels

    success = df["lon"].notna().sum()
    fail = df["lon"].isna().sum()
    print(f"\n結果: 成功 {success} / 失敗 {fail} / 合計 {len(df)}")
    print(f"  街区: {stats['gaiku']}, 大字: {stats['oaza']}, 大字基底: {stats['oaza_base']}")

    if fail > 0:
        print("\n--- 失敗リスト ---")
        for _, row in df[df["lon"].isna()].iterrows():
            town, block = parse_address(str(row["address_full"]).strip(), known_towns)
            print(f"  {row['jigyosho_id']}  [{row['address_full']}]  → 町={town}, 番={block}")

    to_geojson(df, OUT_GEOJSON)
    print(f"\nGeoJSON 出力: {OUT_GEOJSON.relative_to(ROOT)}  ({success} features)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

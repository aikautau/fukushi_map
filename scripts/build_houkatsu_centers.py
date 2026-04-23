"""枚方市 地域包括支援センター（13か所）の住所をジオコーディングして GeoJSON を生成。

入力: data/raw/hirakata/houkatsu_centers.csv
出力: data/houkatsu_centers.geojson
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

from geocode import GAIKU_CSV, OAZA_CSV, geocode_one, load_gaiku, load_oaza

ROOT = Path(__file__).resolve().parent.parent
IN_CSV = ROOT / "data" / "raw" / "hirakata" / "houkatsu_centers.csv"
OUT_GEOJSON = ROOT / "data" / "houkatsu_centers.geojson"


def main() -> int:
    if not IN_CSV.exists():
        print(f"[error] {IN_CSV} が見つかりません。", file=sys.stderr)
        return 1
    for p in (GAIKU_CSV, OAZA_CSV):
        if not p.exists():
            print(f"[error] {p} が見つかりません。", file=sys.stderr)
            return 1

    print("位置参照情報を読み込み中...")
    gaiku = load_gaiku(GAIKU_CSV)
    oaza = load_oaza(OAZA_CSV)
    known_towns = {t for t, _ in gaiku} | set(oaza)

    features = []
    fail = 0
    with open(IN_CSV, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            addr = row["address_full"].strip()
            result = geocode_one(addr, gaiku, oaza, known_towns)
            if result is None:
                print(f"[warn] ジオコーディング失敗: 第{row['area_id']} {row['center_name']} [{addr}]")
                fail += 1
                continue
            lat, lon, level = result
            features.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [lon, lat]},
                "properties": {
                    "area_id": int(row["area_id"]),
                    "center_name": row["center_name"],
                    "address_full": addr,
                    "tel": row["tel"],
                    "school_districts": row["school_districts"],
                    "match_level": level,
                },
            })

    geojson = {"type": "FeatureCollection", "features": features}
    OUT_GEOJSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_GEOJSON, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)

    print(f"\n結果: 成功 {len(features)} / 失敗 {fail} / 合計 {len(features) + fail}")
    print(f"出力: {OUT_GEOJSON.relative_to(ROOT)}")
    return 0 if fail == 0 else 2


if __name__ == "__main__":
    sys.exit(main())

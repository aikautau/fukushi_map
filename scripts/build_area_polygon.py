"""
地域包括支援センター管轄区域ポリゴンを生成する。

小学校区ポリゴン（ElementaryPoly.geojson）を 13 圏域にマージ（dissolve）し、
data/chiiki_houkatsu.geojson として出力する。
"""

import json
import os
import sys
from pathlib import Path

from shapely.geometry import mapping, shape
from shapely.ops import unary_union

# ---------------------------------------------------------------------------
# 入出力パス
# ---------------------------------------------------------------------------
INPUT_PATH = Path(os.path.expanduser(
    "~/hoikumap/papamama-hirakata/data/ElementaryPoly.geojson"
))
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data"
OUTPUT_PATH = OUTPUT_DIR / "chiiki_houkatsu.geojson"

# ---------------------------------------------------------------------------
# 圏域マッピング（area_id, センター名, 小学校区 label リスト）
# ---------------------------------------------------------------------------
AREA_MAPPING: list[tuple[int, str, list[str]]] = [
    (1,  "はなまる",                   ["樟葉北", "樟葉", "樟葉南"]),
    (2,  "社協ふれあい",               ["樟葉西", "牧野"]),
    (3,  "聖徳園",                     ["船橋", "招提", "平野", "殿山第二"]),
    (4,  "安心苑",                     ["小倉", "西牧野", "殿山第一", "磯島"]),
    (5,  "サール・ナート",             ["交北", "山田", "山田東", "禁野"]),
    (6,  "松徳会",                     ["桜丘", "桜丘北", "中宮", "明倫"]),
    (7,  "美郷会",                     ["さだ", "さだ西", "さだ東", "伊加賀"]),
    (8,  "みどり",                     ["山之上", "枚方", "枚方第二"]),
    (9,  "アイリス",                   ["香陽", "香里", "開成", "五常"]),
    (10, "大阪高齢者生協",             ["春日", "川越", "東香里"]),
    (11, "パナソニック エイジフリー",   ["菅原", "西長尾", "長尾"]),
    (12, "大潤会",                     ["田口山", "藤阪", "菅原東"]),
    (13, "東香会",                     ["津田", "津田南", "氷室"]),
]


def main() -> None:
    # --- 入力読み込み ---------------------------------------------------------
    if not INPUT_PATH.exists():
        print(f"ERROR: 入力ファイルが見つかりません: {INPUT_PATH}", file=sys.stderr)
        sys.exit(1)

    with open(INPUT_PATH, encoding="utf-8") as f:
        geojson = json.load(f)

    # label -> Shapely geometry の辞書を作成
    label_to_geom: dict[str, object] = {}
    for feature in geojson["features"]:
        label = feature["properties"]["label"]
        geom = shape(feature["geometry"])
        label_to_geom[label] = geom

    print(f"入力: {len(label_to_geom)} 小学校区ポリゴンを読み込みました")
    print()

    # --- 圏域ごとに union して Feature を組み立て --------------------------------
    features: list[dict] = []
    total_matched = 0

    for area_id, center_name, labels in AREA_MAPPING:
        geometries = []
        matched_labels = []
        missing_labels = []

        for lbl in labels:
            if lbl in label_to_geom:
                geometries.append(label_to_geom[lbl])
                matched_labels.append(lbl)
            else:
                missing_labels.append(lbl)

        if missing_labels:
            print(f"  WARNING: 圏域{area_id} {center_name} — "
                  f"未一致の校区: {', '.join(missing_labels)}")

        if not geometries:
            print(f"  ERROR: 圏域{area_id} {center_name} — "
                  f"一致する校区がありません。スキップします。")
            continue

        merged = unary_union(geometries)

        feature = {
            "type": "Feature",
            "geometry": mapping(merged),
            "properties": {
                "area_id": area_id,
                "center_name": center_name,
                "school_districts": ", ".join(matched_labels),
            },
        }
        features.append(feature)

        print(f"  圏域{area_id:>2} {center_name:<20s} "
              f"校区数 {len(matched_labels)}/{len(labels)}  "
              f"タイプ: {merged.geom_type}")
        total_matched += len(matched_labels)

    print()
    print(f"合計: {total_matched} 校区を {len(features)} 圏域にマージしました")

    # --- 出力 -----------------------------------------------------------------
    output_geojson = {
        "type": "FeatureCollection",
        "features": features,
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output_geojson, f, ensure_ascii=False, indent=2)

    print(f"出力: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()

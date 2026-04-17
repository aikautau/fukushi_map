"""厚労省CSV群と枚方市Excelを統合し、枚方市の事業所一覧を生成する。

- 厚労省CSV（`data/raw/mhlw/jigyosho_*.csv`）: 市区町村コード 272108（枚方市、JIS）で絞り込み
- 枚方市Excel（`data/raw/hirakata/272104_care_service_*.xlsx`）: 差分・穴埋め用
- 事業所番号＋事業所名で dedupe（厚労省=Aを優先）。同一事業所で複数サービスは 1 行に集約
- サービス種類を 8 カテゴリに集約し、事業所ごとに代表カテゴリ（優先順位順）を付与
- `data/processed/jigyosho.csv` に出力
"""

from __future__ import annotations

import glob
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW_MHLW = ROOT / "data" / "raw" / "mhlw"
RAW_HIRAKATA = ROOT / "data" / "raw" / "hirakata"
OUT_CSV = ROOT / "data" / "processed" / "jigyosho.csv"

JST = timezone(timedelta(hours=9))

# 枚方市の市区町村コード。
# - 27210     : JIS X 0402 5桁
# - 272108    : 厚労省CSVが採用する総務省6桁（チェックデジット=8）
# - 272104    : 枚方市Excel内部で使われている6桁表記（末尾=4、出典側の独自採番）
HIRAKATA_CITY_CODES = {"27210", "272108", "272104"}

# 厚労省CSVのファイル名サフィックス（3桁）→ カテゴリ。
# plans/vast-tumbling-knuth.md の分類表に従う。特定施設系はすべて「施設」にまとめる。
CATEGORY_BY_CODE: dict[str, str] = {
    # 訪問系
    "110": "訪問",  # 訪問介護
    "120": "訪問",  # 訪問入浴介護
    "130": "訪問",  # 訪問看護
    "710": "訪問",  # 夜間対応型訪問介護
    "760": "訪問",  # 定期巡回・随時対応型訪問介護看護
    # リハ
    "140": "リハ",  # 訪問リハビリテーション
    "160": "リハ",  # 通所リハビリテーション
    # デイ
    "150": "デイ",  # 通所介護
    "155": "デイ",  # 指定療養通所介護
    "720": "デイ",  # 認知症対応型通所介護
    "780": "デイ",  # 地域密着型通所介護
    # 短期入所
    "210": "短期入所",  # 短期入所生活介護
    "220": "短期入所",  # 短期入所療養介護（老健）
    "230": "短期入所",  # 短期入所療養介護（療養病床を有する病院等）
    "551": "短期入所",  # 短期入所療養介護（介護医療院）
    # 多機能・密着型
    "320": "多機能・密着型",  # 認知症対応型共同生活介護（グループホーム）
    "730": "多機能・密着型",  # 小規模多機能型居宅介護
    "770": "多機能・密着型",  # 看護小規模多機能型居宅介護
    # 施設（特定施設入居者生活介護・地域密着型特定施設も施設カテゴリに束ねる）
    "510": "施設",  # 介護老人福祉施設
    "520": "施設",  # 介護老人保健施設
    "530": "施設",  # 介護療養型医療施設
    "540": "施設",  # 地域密着型介護老人福祉施設入所者生活介護
    "550": "施設",  # 介護医療院
    "331": "施設",
    "332": "施設",
    "334": "施設",
    "335": "施設",
    "336": "施設",
    "337": "施設",
    "361": "施設",
    "362": "施設",
    "364": "施設",
    # 用具・住改
    "170": "用具・住改",  # 福祉用具貸与
    "410": "用具・住改",  # 特定福祉用具販売
    # 居宅支援
    "430": "居宅支援",  # 居宅介護支援
}

# 代表カテゴリ選定の優先順位（数値が小さいほど強い）。
# 複合事業所はより「入所・滞在性」の強いサービス側を代表にする。
CATEGORY_PRIORITY: dict[str, int] = {
    "施設": 1,
    "短期入所": 2,
    "多機能・密着型": 3,
    "リハ": 4,
    "デイ": 5,
    "訪問": 6,
    "居宅支援": 7,
    "用具・住改": 8,
    "その他": 99,
}


def _classify_by_service_name(name: str) -> str:
    """枚方市Excelの「実施サービス」名からカテゴリを判定（キーワード一致）。"""
    if not isinstance(name, str):
        return "その他"
    s = name
    # 訪問リハビリ / 通所リハビリ を先に拾う（訪問に吸われるのを防ぐ）
    if "リハビリ" in s:
        return "リハ"
    if any(k in s for k in ("訪問介護", "訪問入浴", "訪問看護", "夜間対応", "定期巡回")):
        return "訪問"
    if any(k in s for k in ("通所介護", "認知症対応型通所", "療養通所")):
        return "デイ"
    if "短期入所" in s:
        return "短期入所"
    if any(k in s for k in ("小規模多機能", "看護小規模多機能", "認知症対応型共同生活", "グループホーム")):
        return "多機能・密着型"
    if any(
        k in s
        for k in (
            "介護老人福祉施設",
            "介護老人保健施設",
            "老健",
            "介護医療院",
            "介護療養型",
            "特定施設",
            "有料老人ホーム",
            "軽費老人ホーム",
            "サービス付き高齢者",
        )
    ):
        return "施設"
    if "福祉用具" in s:
        return "用具・住改"
    if "居宅介護支援" in s or "介護予防支援" in s:
        return "居宅支援"
    return "その他"


def _file_fetched_at(p: Path) -> str:
    return datetime.fromtimestamp(p.stat().st_mtime, tz=JST).strftime("%Y-%m-%d")


def _combine_address(addr: str | float, kata: str | float) -> str:
    a = str(addr).strip() if pd.notna(addr) else ""
    k = str(kata).strip() if pd.notna(kata) else ""
    if not k or k in a:
        return a
    return f"{a} {k}"


def load_mhlw(csv_dir: Path) -> pd.DataFrame:
    """厚労省CSV群から枚方市の事業所を取り出す。"""
    records: list[pd.DataFrame] = []
    for path_str in sorted(glob.glob(str(csv_dir / "jigyosho_*.csv"))):
        path = Path(path_str)
        m = re.search(r"jigyosho_(\d{3})\.csv$", path.name)
        if not m:
            continue
        code = m.group(1)
        df = pd.read_csv(path, encoding="utf-8", dtype=str)

        # 列名は年度でブレるので存在確認してから参照
        code_col = "都道府県コード又は市町村コード"
        required = (code_col, "事業所番号", "事業所名", "サービスの種類", "住所")
        missing = [c for c in required if c not in df.columns]
        if missing:
            print(f"[warn] {path.name}: 列欠落 {missing}", file=sys.stderr)
            continue

        df = df[df[code_col].astype(str).str.strip().isin(HIRAKATA_CITY_CODES)]
        if df.empty:
            continue

        fetched = _file_fetched_at(path)
        category = CATEGORY_BY_CODE.get(code) or _classify_by_service_name(
            df["サービスの種類"].iloc[0] if len(df) else ""
        )

        sub = pd.DataFrame(
            {
                "jigyosho_id": df["事業所番号"].str.strip(),
                "name": df["事業所名"].str.strip(),
                "category": category,
                "service_type": df["サービスの種類"].str.strip(),
                "prefecture": df.get("都道府県名", pd.Series("大阪府", index=df.index)),
                "city": df.get("市区町村名", pd.Series("枚方市", index=df.index)),
                "address_full": [
                    _combine_address(a, k)
                    for a, k in zip(df["住所"], df.get("方書（ビル名等）", pd.Series([None] * len(df), index=df.index)))
                ],
                "tel": df.get("電話番号", pd.Series([None] * len(df), index=df.index)),
                "capacity": df.get("定員", pd.Series([None] * len(df), index=df.index)),
                "source": "mhlw",
                "fetched_at": fetched,
            }
        )
        records.append(sub)

    if not records:
        return pd.DataFrame()
    return pd.concat(records, ignore_index=True)


def load_hirakata(xlsx: Path) -> pd.DataFrame:
    """枚方市Excelから事業所×サービスの行を取り出す。"""
    df = pd.read_excel(xlsx, sheet_name=0, dtype=str)
    # 列名のゆらぎに備えて候補から選ぶ
    def pick(*cands: str) -> str | None:
        for c in cands:
            if c in df.columns:
                return c
        return None

    col_name = pick("介護サービス事業所名称", "事業所名")
    col_svc = pick("実施サービス", "サービスの種類")
    col_addr = pick("住所")
    col_kata = pick("方書", "方書（ビル名等）")
    col_tel = pick("電話番号")
    col_cap = pick("定員")
    col_id = pick("事業所番号")
    col_pref = pick("都道府県名")
    col_city = pick("市区町村名")

    required = (col_name, col_svc, col_addr, col_id)
    if any(c is None for c in required):
        print(f"[warn] {xlsx.name}: 必須列が見つかりません", file=sys.stderr)
        return pd.DataFrame()

    fetched = _file_fetched_at(xlsx)
    out = pd.DataFrame(
        {
            "jigyosho_id": df[col_id].astype(str).str.strip(),
            "name": df[col_name].astype(str).str.strip(),
            "category": df[col_svc].map(_classify_by_service_name),
            "service_type": df[col_svc].astype(str).str.strip(),
            "prefecture": df[col_pref] if col_pref else "大阪府",
            "city": df[col_city] if col_city else "枚方市",
            "address_full": [
                _combine_address(a, k)
                for a, k in zip(
                    df[col_addr],
                    df[col_kata] if col_kata else pd.Series([None] * len(df)),
                )
            ],
            "tel": df[col_tel] if col_tel else None,
            "capacity": df[col_cap] if col_cap else None,
            "source": "hirakata",
            "fetched_at": fetched,
        }
    )
    # ヘッダー行や空行の除去
    out = out[out["jigyosho_id"].notna() & (out["jigyosho_id"] != "")]
    out = out[out["jigyosho_id"] != "事業所番号"]
    return out.reset_index(drop=True)


def filter_target_cities(df: pd.DataFrame) -> pd.DataFrame:
    """市区町村名に「枚方市」を含む行のみ残す安全フィルタ。"""
    if df.empty or "city" not in df.columns:
        return df
    return df[df["city"].fillna("").str.contains("枚方", na=False)].reset_index(drop=True)


def _pick_representative_category(cats: list[str]) -> str:
    """複数サービスを持つ事業所の代表カテゴリを優先順位で選ぶ。"""
    clean = [c for c in cats if isinstance(c, str) and c]
    if not clean:
        return "その他"
    return sorted(clean, key=lambda c: CATEGORY_PRIORITY.get(c, 99))[0]


def merge_dedupe(frames: list[pd.DataFrame]) -> pd.DataFrame:
    """A（mhlw）優先で事業所単位に dedupe。複数サービスは 1 行に集約する。"""
    frames = [f for f in frames if f is not None and not f.empty]
    if not frames:
        return pd.DataFrame()
    merged = pd.concat(frames, ignore_index=True)

    # 優先度: mhlw > hirakata。以降の「最初の行を残す」系で A が残るように。
    priority = {"mhlw": 0, "hirakata": 1}
    merged["_prio"] = merged["source"].map(priority).fillna(9)
    merged = merged.sort_values(["_prio", "jigyosho_id", "name"]).reset_index(drop=True)

    # 事業所番号は全国で一意に採番されるので、これをキーに事業所を束ねる。
    # 名前は表示用に A（mhlw）の表記を優先採用する。
    merged["_key_id"] = merged["jigyosho_id"].fillna("").astype(str).str.strip()

    grouped_rows: list[dict] = []
    for kid, g in merged.groupby("_key_id", sort=False):
        if not kid:
            continue
        # A（mhlw）行があればそれをベースに、なければ B（hirakata）先頭を採用
        base = g.iloc[0]
        # サービス種類は全ソース横断でユニーク化
        svc_types = (
            g["service_type"].dropna().astype(str).str.strip().replace("", pd.NA).dropna().unique().tolist()
        )
        svc_types = sorted(svc_types)
        category = _pick_representative_category(g["category"].tolist())

        # 属性の穴埋めは A を優先しつつ、空なら B で埋める
        def _pick_field(col: str) -> object:
            for _, row in g.iterrows():
                v = row.get(col)
                if pd.notna(v) and str(v).strip():
                    return v
            return base.get(col)

        grouped_rows.append(
            {
                "jigyosho_id": kid,
                "name": base["name"],
                "category": category,
                "service_type": "; ".join(svc_types),
                "prefecture": _pick_field("prefecture"),
                "city": _pick_field("city"),
                "address_full": _pick_field("address_full"),
                "tel": _pick_field("tel"),
                "capacity": _pick_field("capacity"),
                "source": "mhlw" if (g["source"] == "mhlw").any() else "hirakata",
                "fetched_at": _pick_field("fetched_at"),
            }
        )

    return pd.DataFrame(grouped_rows)


def main() -> int:
    mhlw_df = load_mhlw(RAW_MHLW)
    print(f"[mhlw] 枚方市: {len(mhlw_df)} 行")

    hirakata_files = sorted(RAW_HIRAKATA.glob("*care_service*.xlsx"))
    if not hirakata_files:
        print(f"[warn] 枚方市Excelが見つかりません: {RAW_HIRAKATA}", file=sys.stderr)
        hirakata_df = pd.DataFrame()
    else:
        # 最新日付のExcelを採用
        hirakata_df = load_hirakata(hirakata_files[-1])
        print(f"[hirakata] {hirakata_files[-1].name}: {len(hirakata_df)} 行")

    merged = merge_dedupe([mhlw_df, hirakata_df])
    merged = filter_target_cities(merged)

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    columns = [
        "jigyosho_id",
        "name",
        "category",
        "service_type",
        "prefecture",
        "city",
        "address_full",
        "tel",
        "capacity",
        "source",
        "fetched_at",
    ]
    merged[columns].to_csv(OUT_CSV, index=False, encoding="utf-8")

    print(f"\n出力: {OUT_CSV.relative_to(ROOT)}  ({len(merged)} 行)")
    print("\nカテゴリ別件数:")
    cat_counts = merged["category"].value_counts(dropna=False).sort_index()
    for cat, n in cat_counts.items():
        print(f"  {cat}: {n}")
    print("\n出典別件数:")
    for src, n in merged["source"].value_counts().items():
        print(f"  {src}: {n}")
    uniq = merged.drop_duplicates(subset=["jigyosho_id"]).shape[0]
    print(f"\nユニーク事業所数（事業所番号ベース）: {uniq}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

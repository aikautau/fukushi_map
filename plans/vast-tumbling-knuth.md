# 枚方市 介護事業所マップ（個人利用）

## Context
枚方市の介護保険事業所（居宅介護支援、通所介護・地域密着型通所介護、通所リハ・訪問リハ、訪問介護・訪問看護・訪問入浴、ほか短期入所・定期巡回・小多機 等）の所在地を地図に落としたい。用途は個人の情報整理のみ。

ユーザー選択（確定）：
- **出力形式**: QGISでの静的画像（PNG/PDF）
- **国交省MCP**: Claude Desktop に MCP を登録し、対話ベースだけで完結させる運用も並行で使う
- **対象サービス種別**: 全部（介護保険対象の全事業所）
- **対象自治体**: **枚方市のみ**（大阪市は対象外）
- **実装言語**: Python

---

## データソース（確定）

| # | ソース | 形式 | 対象 | 備考 |
| --- | --- | --- | --- | --- |
| A | [厚労省 介護サービス情報公表システム オープンデータ](https://www.mhlw.go.jp/stf/kaigo-kouhyou_opendata.html) | CSV（ZIP、UTF-8）、サービス種別ごと（全国統合、全28種類） | 市区町村コードで枚方市(27210 / 6桁 272104)をフィルタ | **本命**。収録最も広く、全サービス種別を網羅。緯度経度なし→要ジオコーディング。6月末／12月末更新。CC BY |
| B | [枚方市 介護サービス事業所一覧](https://www.city.hirakata.osaka.jp/0000037120.html) | Excel (.xlsx) | 枚方市の居宅・居宅介護支援・地域密着型・介護保険施設 | 更新 2026-03-10。CC BY 2.1（「枚方市」出典表示必須）。Aとの差分確認・補完に使用 |

**取得戦略**: A（厚労省）を一次ソースとし、市区町村コード（枚方市 27210）でフィルタ。Bは差分確認と事業所名・電話などの補完用に使う。

---

## サービス種別（全部 = 以下を対象）

厚労省コード基準で、枚方市に存在する介護保険系サービスを全部プロット：

| カテゴリ | 含むサービス（例） |
| --- | --- |
| 居宅支援 | 居宅介護支援、介護予防支援 |
| デイ | 通所介護(150)、地域密着型通所介護、認知症対応型通所介護 |
| リハ | 通所リハビリテーション、訪問リハビリテーション |
| 訪問 | 訪問介護(110)、訪問入浴介護(120)、訪問看護(130)、夜間対応型訪問介護、定期巡回・随時対応型訪問介護看護 |
| 多機能・密着型 | 小規模多機能型居宅介護、看護小規模多機能型居宅介護、認知症対応型共同生活介護 |
| 短期入所 | 短期入所生活介護、短期入所療養介護 |
| 施設 | 介護老人福祉施設(510)、介護老人保健施設(520)、介護医療院 |
| 用具・住改 | 福祉用具貸与、特定福祉用具販売 |

→ QGISでは **6〜8 レイヤ**（上記カテゴリ単位）に分けて色分け／アイコン分けする。

---

## 構成

```
hukushimap/
├── data/
│   ├── raw/                     # 各ソースからダウンロードしたCSV/Excel
│   │   ├── mhlw/                # 厚労省 CSV 群
│   │   └── hirakata/            # 枚方市 Excel
│   ├── processed/
│   │   ├── jigyosho.csv         # 統一スキーマの事業所一覧
│   │   ├── geocode_cache.json   # 住所→緯度経度キャッシュ
│   │   └── jigyosho.geojson     # QGIS読込用
│   └── SOURCES.md               # 取得日・ライセンス・出典表記
├── scripts/
│   ├── fetch.py                 # 各ソースをダウンロード
│   ├── normalize.py             # 列名統一、カテゴリ分類、dedupe
│   └── geocode.py               # 国土地理院 AddressSearch でlat/lng付与
├── qgis/
│   ├── hukushimap.qgz           # QGISプロジェクトファイル
│   └── export_map.py            # PyQGIS スクリプト（PNG/PDF一括出力）
├── output/
│   ├── hirakata_all.png
│   └── by_category/*.png
├── mcp/
│   └── README.md                # Claude Desktop への MLIT MCP 登録手順
└── README.md
```

---

## 処理フロー

### 1. データ取得（`scripts/fetch.py`）
- 厚労省ページの最新版CSVリンクをスクレイプし、サービス種別ごとにダウンロード → `data/raw/mhlw/`
- 枚方市ページからExcelをダウンロード → `data/raw/hirakata/`
- 取得日・URL・ライセンスを `data/SOURCES.md` に追記

### 2. 正規化・マージ（`scripts/normalize.py`）
- **pandas + openpyxl** を使用
- 統一スキーマ：`jigyosho_id, name, category, service_type, prefecture, city, address_full, tel, capacity, source, fetched_at`
- 市区町村コードで **枚方市 (27210 / 6桁 272104)** をフィルタ
- 事業所番号＋事業所名でdedupe（A を優先、B で足りない属性を穴埋め）
- カテゴリ分類（上表に従って `category` 列を付与）
- `data/processed/jigyosho.csv` として出力

### 3. ジオコーディング（`scripts/geocode.py`）
- 国土地理院 Address Search API：`https://msearch.gsi.go.jp/address-search/AddressSearch?q={住所}`
- 1秒あたり1〜2リクエストにレート制限
- `data/processed/geocode_cache.json` に `{住所: [lon, lat]}` をキャッシュ（次回以降は差分のみ）
- 失敗したものは残差リストとして出力し、手動でQGIS内で補正できるようにする
- 最終成果物：`data/processed/jigyosho.geojson`（EPSG:4326）

### 4. QGIS 地図作成（`qgis/hukushimap.qgz`＋`qgis/export_map.py`）
- 背景: **地理院地図（標準／淡色）XYZタイル**
  - URL: `https://cyberjapandata.gsi.go.jp/xyz/pale/{z}/{x}/{y}.png`
  - 出典表記: 「国土地理院」をレイアウトの凡例に明記
- `jigyosho.geojson` を読み込み、`category` 列で **カテゴリ化シンボル**（6〜8色）
- BBox: 枚方市全域 を `qgis-bbox` スキルで定義
- 印刷レイアウト：タイトル、凡例、スケールバー、出典（国土地理院／枚方市 CC BY 2.1／厚労省 CC BY）
- **`export_map.py`**（PyQGIS）でレイアウトから PNG と PDF を `output/` に一括書き出し
- カテゴリ別マップもループで出力（`output/by_category/訪問系.png` など）

### 5. Claude Desktop + 国交省MCP（対話運用）
- `mcp/README.md` に [MLIT-DATA-PLATFORM/mlit-dpf-mcp](https://github.com/MLIT-DATA-PLATFORM/mlit-dpf-mcp) と [地理空間MCP Server](https://www.mlit.go.jp/tochi_fudousan_kensetsugyo/tochi_fudousan_kensetsugyo_fr17_000001_00047.html) の Claude Desktop `claude_desktop_config.json` 登録手順を書く
- 登録後の想定ユースケース（対話例）：
  - 「枚方市の浸水想定区域を教えて」→ 訪問系事業所の訪問エリア災害リスク確認
- **注意**: 介護事業所データ自体はMCPに含まれない。国交省MCPは「背景情報・リスク情報の対話取得」用として QGIS マップと組み合わせる

---

## 実装する重要スクリプト（関数シグネチャ）

### `scripts/fetch.py`
```python
def fetch_mhlw(out_dir: Path) -> list[Path]: ...
def fetch_hirakata(out_file: Path) -> Path: ...
```

### `scripts/normalize.py`
```python
CATEGORY_MAP: dict[str, str]  # サービス種別コード/名称 → カテゴリ

def load_mhlw(csv_dir: Path) -> pd.DataFrame: ...
def load_hirakata(xlsx: Path) -> pd.DataFrame: ...
def merge_dedupe(frames: list[pd.DataFrame]) -> pd.DataFrame: ...
def filter_target_cities(df: pd.DataFrame) -> pd.DataFrame: ...  # 27210 / 272104
```

### `scripts/geocode.py`
```python
def geocode(address: str, cache: dict) -> tuple[float, float] | None: ...
def geocode_df(df: pd.DataFrame, cache_path: Path) -> pd.DataFrame: ...
def to_geojson(df: pd.DataFrame, out_path: Path) -> None: ...
```

### `qgis/export_map.py`（PyQGIS）
```python
# QGIS Project から枚方市全域レイアウトとカテゴリ別レイアウトを
# PNG / PDF で output/ に書き出す
```

---

## 検証方法

1. `python scripts/fetch.py` → `data/raw/` に全ファイルが揃う
2. `python scripts/normalize.py` → `data/processed/jigyosho.csv` の行数を確認（カテゴリ別件数を標準出力）
3. `python scripts/geocode.py` → 失敗件数を標準出力。失敗ゼロが理想、数件なら住所手修正
4. QGIS GUIで `qgis/hukushimap.qgz` を開き、地理院地図＋ポイントが正しく表示されること
5. **スポットチェック**：自宅近くの既知事業所が正しい位置にプロットされているか目視
6. `python qgis/export_map.py` → `output/` に PNG/PDF が生成され、凡例・スケールバー・出典表記が含まれること
7. Claude Desktop を再起動後、「浸水想定区域を枚方市で取得して」等の対話でMCPが応答すること
8. すべての出力物に **出典表記（国土地理院、枚方市 CC BY 2.1、厚労省 CC BY）** が含まれること

---

## 修正対象ファイル（新規作成のみ、編集対象の既存ファイルなし）

- `data/SOURCES.md`
- `scripts/fetch.py`
- `scripts/normalize.py`
- `scripts/geocode.py`
- `qgis/hukushimap.qgz`（QGIS GUI操作で作成）
- `qgis/export_map.py`
- `mcp/README.md`
- `README.md`
- `requirements.txt`（`pandas`, `openpyxl`, `requests`, `beautifulsoup4`）

---

## 未解決・リスク

- **枚方市データはExcel形式のみ**（CSV無し）→ openpyxlで読み込み
- **ジオコーディング数百件規模**（枚方市 742事業所想定）→ 国土地理院APIへのレート制御とキャッシュ必須
- 厚労省オープンデータの列名は年度で微変動する可能性あり → normalize時に列名の存在チェックを入れる
- QGIS本体は別途インストール必要（PyQGIS は QGIS の Python 経由で実行）
- MCP Server は **α版**。動作保証なく仕様変更リスクあり。不動産情報ライブラリ利用約款の遵守が必要
- 個人利用前提のため公開ホスティングは行わない。成果物をGitHub等に再配布する場合は、データ出典のライセンス（特に枚方市・厚労省）を再確認

---

## 参考リンク（情報源）

- 厚労省 介護サービス情報公表システム オープンデータ: https://www.mhlw.go.jp/stf/kaigo-kouhyou_opendata.html
- 枚方市 介護サービス事業所一覧: https://www.city.hirakata.osaka.jp/0000037120.html
- 国交省 地理空間MCP Server (α版): https://www.mlit.go.jp/tochi_fudousan_kensetsugyo/tochi_fudousan_kensetsugyo_fr17_000001_00047.html
- MLIT DATA PLATFORM MCP Server: https://github.com/MLIT-DATA-PLATFORM/mlit-dpf-mcp
- 国土地理院 Address Search API: https://msearch.gsi.go.jp/address-search/AddressSearch
- 地理院タイル（淡色）: https://cyberjapandata.gsi.go.jp/xyz/pale/{z}/{x}/{y}.png

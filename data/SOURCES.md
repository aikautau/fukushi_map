# データソース記録

このファイルはプロジェクトで使っているデータの取得履歴・出典・ライセンスを記録する台帳。`scripts/fetch.py` を実行したら **追記**（上書き禁止）する。地図や PDF などの成果物にはここに書かれた出典表記を必ず入れること。

---

## 一次ソース一覧

| 記号 | ソース | URL | 形式 | ライセンス | 出典表記（必須） |
| --- | --- | --- | --- | --- | --- |
| A | 厚労省 介護サービス情報公表システム オープンデータ | https://www.mhlw.go.jp/stf/kaigo-kouhyou_opendata.html | CSV (ZIP, UTF-8) | CC BY 4.0 | 「厚生労働省 介護サービス情報公表システム」 |
| N | 厚労省 医療情報ネット（ナビイ）オープンデータ 施設票（病院・診療所・歯科診療所） | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryou/newpage_43373.html | CSV (ZIP, UTF-8-BOM) | 公共データ利用規約 第1.0版（PDL1.0）— CC BY 4.0 と同等条件で再配布可 | 「厚生労働省 医療情報ネット（ナビイ）」 |
| B | 枚方市 介護サービス事業所一覧 | https://www.city.hirakata.osaka.jp/0000037120.html | Excel (.xlsx) | CC BY 2.1 JP | 「枚方市」 |
| M | 国土地理院 地理院タイル（淡色） | https://cyberjapandata.gsi.go.jp/xyz/pale/{z}/{x}/{y}.png | XYZ タイル | 国土地理院 利用規約 | 「国土地理院」 |
| M2 | 国土地理院 地理院タイル（航空写真 / シームレス） | https://cyberjapandata.gsi.go.jp/xyz/seamlessphoto/{z}/{x}/{y}.jpg | XYZ タイル | 国土地理院 利用規約 | 「国土地理院」 |
| M3 | MIERUNE Mono タイル | https://tile.mierune.co.jp/mierune_mono/{z}/{x}/{y}.png | XYZ タイル | CC BY（MIERUNE）＋ ODbL（OpenStreetMap contributors） | `Maptiles by MIERUNE, under CC BY. Data by OpenStreetMap contributors, under ODbL.` |
| M4 | OpenStreetMap 標準タイル | https://tile.openstreetmap.org/{z}/{x}/{y}.png | XYZ タイル | ODbL（OpenStreetMap contributors） | `© OpenStreetMap contributors` |
| G | 街区レベル位置参照情報（23.0a）／大字・町丁目位置参照情報（18.0b）国土交通省（2024年） | https://nlftp.mlit.go.jp/cgi-bin/isj/dls/_choose_method.cgi | CSV | [国土交通省 位置参照情報利用規約](https://nlftp.mlit.go.jp/isj/agreement.html) | 「街区レベル位置参照情報・大字・町丁目位置参照情報 国土交通省（2024年）」（正式名称での表記が必須） |
| S | 国土数値情報 小学校区データ | https://nlftp.mlit.go.jp/ksj/ | GeoJSON | 国土交通省 利用規約 | 「国土数値情報（小学校区データ）」（国土交通省） |
| H | 枚方市 地域包括支援センター管轄区域 | https://www.city.hirakata.osaka.jp/kourei/0000002638.html | — | 枚方市 | 「枚方市」 |

---

## 取得履歴

取得ごとに以下テンプレを追記する：

```
### YYYY-MM-DD

- ソース: [A/B]
- URL: <ダウンロード元の具体的URL>
- 取得ファイル: data/raw/<path>
- ファイルサイズ: 例）12.3 MB
- 基準日 / 公表日: 例）令和8年2月1日
- 備考: 列名や仕様変更など気づいたこと
```

---

<!-- 実際の取得ログはこの下に追記していく。最初のエントリは scripts/fetch.py を実行した日に記録する。 -->

### 2026-04-16 15:20 UTC+09:00

#### A. 厚労省 介護サービス情報公表システム オープンデータ

- `data/raw/mhlw/jigyosho_110.csv` (15,748.0 KB) — <https://www.mhlw.go.jp/content/12300000/jigyosho_110.csv>
- `data/raw/mhlw/jigyosho_120.csv` (673.0 KB) — <https://www.mhlw.go.jp/content/12300000/jigyosho_120.csv>
- `data/raw/mhlw/jigyosho_130.csv` (7,873.5 KB) — <https://www.mhlw.go.jp/content/12300000/jigyosho_130.csv>
- `data/raw/mhlw/jigyosho_140.csv` (2,132.6 KB) — <https://www.mhlw.go.jp/content/12300000/jigyosho_140.csv>
- `data/raw/mhlw/jigyosho_150.csv` (10,350.2 KB) — <https://www.mhlw.go.jp/content/12300000/jigyosho_150.csv>
- `data/raw/mhlw/jigyosho_155.csv` (22.5 KB) — <https://www.mhlw.go.jp/content/12300000/jigyosho_155.csv>
- `data/raw/mhlw/jigyosho_160.csv` (3,334.1 KB) — <https://www.mhlw.go.jp/content/12300000/jigyosho_160.csv>
- `data/raw/mhlw/jigyosho_170.csv` (2,768.9 KB) — <https://www.mhlw.go.jp/content/12300000/jigyosho_170.csv>
- `data/raw/mhlw/jigyosho_210.csv` (4,486.2 KB) — <https://www.mhlw.go.jp/content/12300000/jigyosho_210.csv>
- `data/raw/mhlw/jigyosho_220.csv` (1,485.6 KB) — <https://www.mhlw.go.jp/content/12300000/jigyosho_220.csv>
- `data/raw/mhlw/jigyosho_230.csv` (47.5 KB) — <https://www.mhlw.go.jp/content/12300000/jigyosho_230.csv>
- `data/raw/mhlw/jigyosho_320.csv` (5,157.1 KB) — <https://www.mhlw.go.jp/content/12300000/jigyosho_320.csv>
- `data/raw/mhlw/jigyosho_331.csv` (1,801.6 KB) — <https://www.mhlw.go.jp/content/12300000/jigyosho_331.csv>
- `data/raw/mhlw/jigyosho_332.csv` (196.7 KB) — <https://www.mhlw.go.jp/content/12300000/jigyosho_332.csv>
- `data/raw/mhlw/jigyosho_334.csv` (280.4 KB) — <https://www.mhlw.go.jp/content/12300000/jigyosho_334.csv>
- `data/raw/mhlw/jigyosho_335.csv` (4.0 KB) — <https://www.mhlw.go.jp/content/12300000/jigyosho_335.csv>
- `data/raw/mhlw/jigyosho_336.csv` (2.7 KB) — <https://www.mhlw.go.jp/content/12300000/jigyosho_336.csv>
- `data/raw/mhlw/jigyosho_337.csv` (5.1 KB) — <https://www.mhlw.go.jp/content/12300000/jigyosho_337.csv>
- `data/raw/mhlw/jigyosho_361.csv` (106.7 KB) — <https://www.mhlw.go.jp/content/12300000/jigyosho_361.csv>
- `data/raw/mhlw/jigyosho_362.csv` (26.2 KB) — <https://www.mhlw.go.jp/content/12300000/jigyosho_362.csv>
- `data/raw/mhlw/jigyosho_364.csv` (24.1 KB) — <https://www.mhlw.go.jp/content/12300000/jigyosho_364.csv>
- `data/raw/mhlw/jigyosho_410.csv` (2,353.8 KB) — <https://www.mhlw.go.jp/content/12300000/jigyosho_410.csv>
- `data/raw/mhlw/jigyosho_430.csv` (15,129.3 KB) — <https://www.mhlw.go.jp/content/12300000/jigyosho_430.csv>
- `data/raw/mhlw/jigyosho_510.csv` (3,200.8 KB) — <https://www.mhlw.go.jp/content/12300000/jigyosho_510.csv>
- `data/raw/mhlw/jigyosho_520.csv` (1,538.1 KB) — <https://www.mhlw.go.jp/content/12300000/jigyosho_520.csv>
- `data/raw/mhlw/jigyosho_530.csv` (25.8 KB) — <https://www.mhlw.go.jp/content/12300000/jigyosho_530.csv>
- `data/raw/mhlw/jigyosho_540.csv` (1,098.0 KB) — <https://www.mhlw.go.jp/content/12300000/jigyosho_540.csv>
- `data/raw/mhlw/jigyosho_550.csv` (324.8 KB) — <https://www.mhlw.go.jp/content/12300000/jigyosho_550.csv>
- `data/raw/mhlw/jigyosho_551.csv` (68.5 KB) — <https://www.mhlw.go.jp/content/12300000/jigyosho_551.csv>
- `data/raw/mhlw/jigyosho_710.csv` (99.1 KB) — <https://www.mhlw.go.jp/content/12300000/jigyosho_710.csv>
- `data/raw/mhlw/jigyosho_720.csv` (1,292.1 KB) — <https://www.mhlw.go.jp/content/12300000/jigyosho_720.csv>
- `data/raw/mhlw/jigyosho_730.csv` (2,168.0 KB) — <https://www.mhlw.go.jp/content/12300000/jigyosho_730.csv>
- `data/raw/mhlw/jigyosho_760.csv` (621.0 KB) — <https://www.mhlw.go.jp/content/12300000/jigyosho_760.csv>
- `data/raw/mhlw/jigyosho_770.csv` (558.4 KB) — <https://www.mhlw.go.jp/content/12300000/jigyosho_770.csv>
- `data/raw/mhlw/jigyosho_780.csv` (7,641.7 KB) — <https://www.mhlw.go.jp/content/12300000/jigyosho_780.csv>

#### B. 枚方市 介護サービス事業所一覧

- `data/raw/hirakata/272104_care_service_202603.xlsx` (121.9 KB) — <https://www.city.hirakata.osaka.jp/cmsfiles/contents/0000037/37120/272104_care_service_202603.xlsx>

### 2026-04-23

#### G. 街区レベル位置参照情報・大字・町丁目位置参照情報（国土交通省、2024年）— ブラウザ検索用辞書の生成

- 生成物: `data/geocoding_gaiku.json` (約 1.0 MB)、`data/geocoding_oaza.json` (約 34 KB)、`data/geocoding_towns.json` (約 16 KB)
- スクリプト: `scripts/build_geocoding_index.py`
- 用途: ブラウザ側のツールバー検索ボックスで、入力された住所を APIなしでローカル解決するための辞書
- 備考: 表記ゆれ（招堤↔招提、樟葉↔楠葉、星ケ丘↔星丘、N丁目↔漢数字丁目、ヶ↔ケ）を前処理段階で全展開してキー登録。各 JSON 先頭に `_source` / `_license` / `_processed_by` のメタキーを含める。利用規約: <https://nlftp.mlit.go.jp/isj/agreement.html>

#### H. 枚方市 地域包括支援センター（13か所）一覧

- 取得元ページ: <https://www.city.hirakata.osaka.jp/kourei/0000002638.html>
- 取得日: 2026-04-23（ページ掲載の最新名簿）
- 生成物: `data/raw/hirakata/houkatsu_centers.csv`（手入力した名称・住所・電話・担当校区）、`data/houkatsu_centers.geojson`（13 件すべて 街区レベル位置参照情報でジオコーディング成功）
- スクリプト: `scripts/build_houkatsu_centers.py`
- 出典表記: 「枚方市」（CC BY 2.1 JP）＋ 座標解決は G. 街区レベル位置参照情報（国土交通省、2024年）
- 備考: 第1〜第13 圏域の `center_name`（運営法人名の略称）は既存の `data/chiiki_houkatsu.geojson` のポリゴン `center_name` と同じ値で揃えている。


### 2026-04-24 08:43 UTC+09:00

#### N. 厚労省 医療情報ネット（ナビイ）オープンデータ （※最初の取得時は M. 見出しで記録されましたが、一次ソース一覧の記号と揃えるため N. に改称。ファイル実体は同一です）

- `data/raw/mhlw_medical/hospital_facility_info_20251201.zip` (740.7 KB) — <https://www.mhlw.go.jp/content/11121000/01-1_hospital_facility_info_20251201.zip>
- `data/raw/mhlw_medical/clinic_facility_info_20251201.zip` (6,497.1 KB) — <https://www.mhlw.go.jp/content/11121000/02-1_clinic_facility_info_20251201.zip>
- `data/raw/mhlw_medical/dental_facility_info_20251201.zip` (3,812.3 KB) — <https://www.mhlw.go.jp/content/11121000/03-1_dental_facility_info_20251201.zip>

基準日（公表時点）: 2025-12-01。PDL1.0（公共データ利用規約 第1.0版、CC BY 4.0 と同等条件で再配布可）。
枚方市分件数: 病院 23、診療所 245、歯科診療所 186（合計 454。座標同梱のためジオコーディング不要）。
施設票 CSV の主な列: `ID` / `正式名称` / `機関区分` / `都道府県コード` / `市区町村コード` / `所在地` / `所在地座標（緯度・経度）` / `案内用ホームページアドレス` / `合計病床数` 等。
電話番号・診療科目は同 CSV（施設票）には含まれない（将来的に「診療科時間票」を統合する場合は別途検討）。


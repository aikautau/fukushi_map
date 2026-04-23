# CLAUDE.md

このファイルは Claude Code がこのプロジェクトで作業するときの指針。

## プロジェクト概要

枚方市の介護保険事業所（全種別）をインタラクティブ Web マップとして GitHub Pages で公開するプロジェクト。[codeforsapporo/papamama](https://github.com/codeforsapporo/papamama)（MIT License）のフォークをベースに、介護事業所向けに改変。データパイプラインは Python、Web フロントエンドは OpenLayers + Bootstrap（ビルド不要の静的サイト）。

設計の大元は [plans/vast-tumbling-knuth.md](plans/vast-tumbling-knuth.md)。

## よく使うコマンド

```bash
# === データパイプライン（Python venv 内で実行） ===
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python scripts/fetch.py                     # data/raw/ にダウンロード
python scripts/normalize.py                 # data/processed/jigyosho.csv を生成
python scripts/geocode.py                   # data/processed/jigyosho.geojson を生成
python scripts/build_geocoding_index.py     # data/geocoding_*.json（ブラウザ検索用辞書）を生成
python scripts/build_houkatsu_centers.py    # data/houkatsu_centers.geojson（地域包括支援センター13か所）を生成

# === Web マップのローカル確認 ===
python3 -m http.server 8000
# → http://localhost:8000 をブラウザで開く
```

## 作業するときのルール

### データと出典
- **出典表記は必須**。README・Web ページのフッターに以下を必ず入れる。削ってはいけない：
  - 「厚生労働省 介護サービス情報公表システム」（CC BY 4.0）
  - 「枚方市」（CC BY 2.1 JP）
  - 「国土地理院」（地理院タイル）
  - 「街区レベル位置参照情報・大字・町丁目位置参照情報 国土交通省（2024年）」（ジオコーディング用 — 正式名称での表記が必須）
  - 「国土数値情報（小学校区データ）」（国土交通省）（ポリゴン用）
  - フォーク元: [codeforsapporo/papamama](https://github.com/codeforsapporo/papamama)（MIT License）
- 生データ（`data/raw/`）は git 管理しない。公開用 GeoJSON（`data/` 直下）は git 管理する。
- データ取得日・URL・ライセンスは毎回 `data/SOURCES.md` に追記する。上書きではなく追記。

### コード方針
- 厚労省オープンデータは列名が年度で微妙に変わる。`normalize.py` では列名の存在チェックを入れてから参照する。
- ジオコーディングは国土交通省 位置参照情報（街区レベル 23.0a ＋ 大字レベル 18.0b）によるローカルマッチング。API 不要。
- 市区町村コード: **枚方市 27210**（6桁 JIS は 272104）。フィルタ対象はこれのみ。大阪市は対象外。
- 事業所の dedupe は「事業所番号＋事業所名」。優先度は A（厚労省）> B（枚方市）。
- カテゴリは 8 つ（居宅支援・デイ・リハ・訪問・多機能/密着型・短期入所・施設・用具）。

### Web マップ
- 背景は地理院タイル淡色 `https://cyberjapandata.gsi.go.jp/xyz/pale/{z}/{x}/{y}.png`。
- フロントエンドは OpenLayers 10 + Bootstrap 5。ビルドステップなしの静的ファイル構成。
- GitHub Pages でデプロイ（main ブランチ直接）。
- ポリゴンレイヤー: 小学校区（国土数値情報）を 13 圏域に結合して地域包括支援センター管轄区域として表示。

## やってはいけないこと

- データ出典のライセンス表記を削る・簡略化する。
- 厚労省以外のソースを一次データに格上げする（A 優先の原則を崩さない）。
- フォーク元（codeforsapporo/papamama）の MIT License 表記を削除する。

## 参考

- フォーク元: https://github.com/codeforsapporo/papamama (MIT License)
- 姉妹プロジェクト: [papamama_hirakata](https://github.com/aikautau/papamama_hirakata)（保育施設マップ）
- 設計ドキュメント: [plans/vast-tumbling-knuth.md](plans/vast-tumbling-knuth.md)
- 厚労省オープンデータ: https://www.mhlw.go.jp/stf/kaigo-kouhyou_opendata.html
- 国土交通省 位置参照情報: https://nlftp.mlit.go.jp/cgi-bin/isj/dls/_choose_method.cgi
- 国土数値情報（小学校区データ）: https://nlftp.mlit.go.jp/ksj/
- 枚方市 地域包括支援センター: https://www.city.hirakata.osaka.jp/kourei/0000002638.html

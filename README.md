# Fukushimap｜枚方市 介護事業所マップ

枚方市の介護保険事業所（全8カテゴリ・779施設）を地図上で確認できる Web アプリです。
施設をタップすると名称・住所・電話番号・カテゴリなどが表示されます。

**デモ：** https://aikautau.github.io/fukushi_map/

---

## 機能

- 介護事業所のインタラクティブ地図表示（779施設）
- タップ／クリックで事業所の詳細をポップアップ表示
- カテゴリ別フィルタリング（居宅支援・デイ・リハ・訪問・多機能/密着型・短期入所・施設・用具）
- 地域包括支援センター管轄区域（13圏域）のポリゴン表示
- 背景地図の切替

## 対象サービス種別

| カテゴリ | 含むサービス（例） |
|---------|-----------------|
| 居宅支援 | 居宅介護支援、介護予防支援 |
| デイ | 通所介護、地域密着型通所介護、認知症対応型通所介護 |
| リハ | 通所リハビリテーション、訪問リハビリテーション |
| 訪問 | 訪問介護、訪問入浴介護、訪問看護、定期巡回・随時対応型訪問介護看護 |
| 多機能・密着型 | 小規模多機能型居宅介護、看護小規模多機能型居宅介護、認知症対応型共同生活介護 |
| 短期入所 | 短期入所生活介護、短期入所療養介護 |
| 施設 | 介護老人福祉施設、介護老人保健施設、介護医療院 |
| 用具・住改 | 福祉用具貸与、特定福祉用具販売 |

---

## 使い方

### ローカルで動かす

```bash
git clone https://github.com/aikautau/fukushi_map.git
cd fukushi_map
python3 -m http.server 8000
# → http://localhost:8000 をブラウザで開く
```

### データを再生成する

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python scripts/fetch.py       # 厚労省・枚方市データを取得
python scripts/normalize.py   # 統一スキーマに正規化
python scripts/geocode.py     # 位置参照情報で座標を付与
```

---

## 技術スタック

| 用途 | ライブラリ |
|------|-----------|
| 地図表示 | [OpenLayers 10](https://openlayers.org/) |
| UI フレームワーク | [Bootstrap 5](https://getbootstrap.com/) |
| データ形式 | GeoJSON |
| データパイプライン | Python |
| ホスティング | GitHub Pages |

---

## データソースとライセンス

このプロジェクトは以下のオープンデータ・サービスを利用しています。

| データ | 出典 | ライセンス |
|--------|------|-----------|
| 介護事業所データ（一次ソース） | [厚生労働省 介護サービス情報公表システム オープンデータ](https://www.mhlw.go.jp/stf/kaigo-kouhyou_opendata.html) | CC BY 4.0 |
| 介護事業所データ（補完） | [枚方市 介護サービス事業所一覧](https://www.city.hirakata.osaka.jp/0000037120.html) | CC BY 2.1 JP（「枚方市」表示必須） |
| ジオコーディング（住所→座標変換） | [国土交通省 位置参照情報](https://nlftp.mlit.go.jp/cgi-bin/isj/dls/_choose_method.cgi)（街区レベル・大字レベル） | 国土交通省の利用規約に基づく |
| 背景地図 | [国土地理院 地理院タイル（淡色）](https://maps.gsi.go.jp/development/ichiran.html) | 「国土地理院」表示必須 |
| 地域包括支援センター管轄区域 | [国土数値情報（小学校区データ）](https://nlftp.mlit.go.jp/ksj/)（国土交通省）を加工して作成 | 国土交通省の利用規約に基づく |
| 地域包括支援センター圏域情報 | [枚方市 地域包括支援センター](https://www.city.hirakata.osaka.jp/kourei/0000002638.html) | 枚方市 |

---

## ライセンス

MIT License — 詳細は [LICENSE.txt](LICENSE.txt) を参照してください。

元プロジェクト [papamama](https://github.com/codeforsapporo/papamama)（Code for Sapporo・MIT License）をベースに、枚方市の介護事業所マップ向けに改変しています。

---

## 謝辞

- [Code for Sapporo](https://github.com/codeforsapporo) — [papamama](https://github.com/codeforsapporo/papamama) プロジェクト
- 厚生労働省 — 介護サービス情報公表システム オープンデータの公開
- 枚方市 — 介護サービス事業所一覧のオープンデータ公開
- 国土地理院 — 地理院タイルの提供
- 国土交通省 — 位置参照情報・国土数値情報の公開

# ツールバー検索機能（事業所名検索＋住所ジオコーディング）

## Context

枚方市介護事業所マップは現在、カテゴリ絞り込みと圏域ドロップダウンしか絞り込み手段がない。ユーザーは目的の事業所を探すときに地図をパンして目視で探すしかない。「事業所名で検索」と「住所を入れたらその場所を中心に表示」をツールバーから行えるようにしたい。

枚方市内の住所解決は、データパイプライン（`scripts/geocode.py`）で既に国土交通省の位置参照情報（`data/geodata/`）を使ってローカルに行っており、このデータ資産をブラウザでも活用できる。したがって外部APIに依存せず、オフラインで完結するジオコーディングができる。

## 最終仕様

- ツールバー右側に**1つの検索ボックス**を追加。入力内容から自動判定して施設名と住所を同時に引く（候補リストに「施設」「住所」バッジを付けて混在表示）。
- 施設名を選択 → 該当施設にズーム＋既存ポップアップ表示。
- 住所を選択 → 中心移動＋ズーム17＋**一時的なピン**を立て、ピンのポップアップにマッチレベル（街区／大字／基底）と入力住所を表示。次の検索で消える。
- 位置参照情報はPython側で**表記ゆれを全展開した辞書JSON**に変換し、`data/` 直下に配置して git 管理。ブラウザは軽い正規化＋辞書lookupで解決。

## データ前処理

### 新規: [scripts/build_geocoding_index.py](scripts/build_geocoding_index.py)

[scripts/geocode.py](scripts/geocode.py) の以下を流用して JSON を生成する（重複実装は 13 行程度で済むので、最小変更として新スクリプト内で読み替え実装する）：
- `load_gaiku()` ([scripts/geocode.py:75-88](scripts/geocode.py#L75-L88)) — 街区データ読み込み
- `load_oaza()` ([scripts/geocode.py:91-101](scripts/geocode.py#L91-L101)) — 大字データ読み込み
- `_normalize_ke()` ([scripts/geocode.py:48-49](scripts/geocode.py#L48-L49))
- `_ADDR_ALIASES` ([scripts/geocode.py:53-58](scripts/geocode.py#L53-L58))
- `_to_kanji()` ([scripts/geocode.py:27-37](scripts/geocode.py#L27-L37)) — 「1丁目 ⇄ 一丁目」両対応

**前処理段階で全バリエーションをキー展開する方針**（ブラウザ側の正規化コードを最小にするため）：
- 表記ゆれ（招堤↔招提、樟葉↔楠葉、星ケ丘↔星丘）を**両方の綴りでキー登録**
- ヶ/ケ/が を統一したキー
- 「1丁目」と「一丁目」両方のキー

### 生成物（`data/` 直下、git 管理）

| ファイル | 中身 | 推定サイズ |
|---|---|---|
| `data/geocoding_gaiku.json` | `{"町名\t街区符号": [lon, lat], ...}` | 約 500-600KB（gzip で 150-200KB） |
| `data/geocoding_oaza.json` | `{"町名": [lon, lat], ...}` | 約 20KB |
| `data/geocoding_towns.json` | 既知町名配列（長さ降順、最長一致用） | 約 10KB |

- タブ区切りキー（実住所に出現しない）
- 座標は小数6桁に丸める
- `json.dump(..., ensure_ascii=False, separators=(',',':'))` で minify

### ドキュメント更新

- [CLAUDE.md](CLAUDE.md) の「よく使うコマンド」に `python scripts/build_geocoding_index.py` を追加
- [README.md](README.md) のデータ再生成手順に同コマンドを追記
- `requirements.txt` は変更不要（既存の `pandas` 等で足りる）

## フロントエンド UI

### [index.html](index.html) 変更

**L33-37 のツールバー右側セクションに検索ボックスを追加**（圏域ドロップダウンの左）：

```html
<div class="d-flex align-items-center gap-2 position-relative" id="searchWrap">
  <input type="search" id="searchBox" class="form-control form-control-sm"
         placeholder="事業所名・住所で検索" autocomplete="off"
         style="width:220px;font-size:.8rem;">
  <div id="searchSuggest" class="list-group position-absolute"
       style="top:100%;left:0;width:260px;z-index:1050;display:none;
              max-height:300px;overflow-y:auto;"></div>
  <select id="selectArea" ...>...</select>
</div>
```

**L64-66 に `<script src="js/search.js"></script>` を `js/index.js` の前に追加**。

### [css/style.css](css/style.css) 追記

- サジェスト `list-group` の影・ホバー色・バッジサイズ
- モバイル（`@media (max-width:991px)`）で検索ボックスを幅100%に

## JavaScript 実装

### 新規: [js/search.js](js/search.js)

既存 [js/hukushimap.js](js/hukushimap.js) と同じ **prototype ベース + ES5スタイル** で書く（`class`/`const`/`let`/アロー関数/テンプレリテラルは使わない）。

```js
function FacilitySearch(hmap, facilities, gaiku, oaza, towns) { ... }
FacilitySearch.prototype.attach = function(inputEl, suggestEl) { ... };
FacilitySearch.prototype._onInput = function(query) { ... };          // debounce 150ms
FacilitySearch.prototype._normalizeInput = function(s) { ... };
FacilitySearch.prototype._searchFacilities = function(q) { ... };     // 最大8件
FacilitySearch.prototype._isAddressLike = function(q) { ... };
FacilitySearch.prototype._geocode = function(q) { ... };
FacilitySearch.prototype._renderSuggest = function(facItems, addrItem) { ... };
FacilitySearch.prototype._pickFacility = function(feature) { ... };   // ズーム + 既存popup
FacilitySearch.prototype._pickAddress = function(result) { ... };     // 中心移動 + ピン
FacilitySearch.prototype._clearPin = function() { ... };
```

#### 入力正規化 `_normalizeInput`（20行以内）

1. 全角数字 → 半角
2. ハイフン類（`－ー−‐—–`） → `-`
3. `ヶ/ｹ/が` → `ケ`
4. 接頭辞 `大阪府枚方市` / `枚方市` を除去
5. `1丁[^目]` → `1丁目` 補正
6. 小文字化（施設名検索用。住所には影響しない）

#### 施設名検索

- 778 features の `name` を同じ正規化で比較 → `indexOf(q) >= 0` で filter
- 最大8件、ヒット件数によらず常に試行
- 再利用: [js/hukushimap.js:96-120](js/hukushimap.js#L96-L120) の `getPopupTitle` / `getPopupContent`

#### 住所ジオコーディング `_geocode`（[scripts/geocode.py:126-178](scripts/geocode.py#L126-L178) の簡易版）

```
1. towns 配列（長さ降順）で最長一致町名を決定
2. 残り文字列から数字を抽出 → block
3. gaiku[town + '\t' + block] があれば street-level ヒット
4. なければ oaza[town] を試す（大字マッチ）
5. なければ丁目を除いた基底 base を oaza で試す（大字基底マッチ）
6. すべて失敗なら null
```

戻り値 `{ lonlat: [lon,lat], level: 'gaiku'|'oaza'|'oaza_base', town, block? }`。

#### 住所判定 `_isAddressLike`

`/[\d０-９一二三四五六七八九十]/` か `/丁目|番地|番|号/` にマッチすれば住所扱い。施設名に数字が混ざるケースは施設名マッチも並行して出すので誤判定による損失なし。

#### 住所選択時のピン表示

- `search.js` 内で `ol.layer.Vector` を1つだけ作り `hmap.map.addLayer()`（zIndex: 30、事業所レイヤーより上）
- スタイルは `ol.style.Circle` の二重リング（赤系、事業所ピンと区別）
- `hmap.map.getView().animate({ center: ol.proj.fromLonLat(lonlat), zoom: 17, duration: 400 })`
- OpenLayersのpopupをピン座標にセットし、タイトル「検索した住所」、中身に入力住所＋マッチレベル（`街区レベル` / `大字レベル` / `大字基底レベル`）を表示
- 次の検索 or 地図クリック or popup×ボタンでクリア

#### サジェストUI（Bootstrap `.list-group-item-action`）

```html
<button class="list-group-item list-group-item-action py-1">
  <small class="badge bg-secondary">施設</small>
  <span class="ms-1">○○デイサービス</span>
  <small class="text-muted d-block">大阪府枚方市…</small>
</button>
```

- 施設バッジ: `bg-secondary`、住所バッジ: `bg-info`
- ヒット0件かつ住所判定されて失敗 → `<div class="list-group-item text-muted">該当住所が見つかりません</div>`

### 既存修正: [js/index.js](js/index.js)

- `allFeatures` を IIFE トップレベルの変数として宣言（現状 L44 でクロージャ内のローカル）
- 初期化を `Promise.all` 化して jigyosho.geojson + geocoding_*.json の4つが揃ってから `FacilitySearch` を初期化する
- area polygon の fetch（[js/index.js:63-80](js/index.js#L63-L80)）は独立なので据え置き
- `FacilitySearch` 側が popup / map を触るので、既存のクリックハンドラ（[js/index.js:109-126](js/index.js#L109-L126)）と競合しないよう「検索ピンをクリック」ケースを特別扱いするか、単純にピン上クリックで通常の popup 閉じ動作に任せる（後者で十分）

## 変更・新規ファイル一覧

| 種別 | パス | 役割 |
|---|---|---|
| 修正 | [index.html](index.html) | L33-37 に検索ボックスUI / L64-66 に script 追加 |
| 修正 | [js/index.js](js/index.js) | `allFeatures` スコープ露出 / `Promise.all` 化 / `FacilitySearch` 初期化 |
| 新規 | [js/search.js](js/search.js) | `FacilitySearch` 検索・ジオコーディング・ピン管理 |
| 新規 | [scripts/build_geocoding_index.py](scripts/build_geocoding_index.py) | 位置参照情報CSV → JSON変換 |
| 新規 | [data/geocoding_gaiku.json](data/geocoding_gaiku.json) | 街区辞書（git管理） |
| 新規 | [data/geocoding_oaza.json](data/geocoding_oaza.json) | 大字辞書（git管理） |
| 新規 | [data/geocoding_towns.json](data/geocoding_towns.json) | 町名配列（git管理） |
| 修正 | [css/style.css](css/style.css) | 検索UIスタイル＋モバイル対応 |
| 修正 | [README.md](README.md) | 機能欄＋再生成手順 |
| 修正 | [CLAUDE.md](CLAUDE.md) | 「よく使うコマンド」に build_geocoding_index.py を追加 |

## 実装順序

1. [scripts/build_geocoding_index.py](scripts/build_geocoding_index.py) を作成して3つのJSONを生成、サイズ目視確認
2. [js/search.js](js/search.js) のスケルトン — 施設名検索のみ、サジェストなしで `console.log`
3. [index.html](index.html) に検索ボックス追加、施設名→ズーム+popup が動くことを確認
4. ジオコーディング実装、住所サジェスト + ピン + マッチレベル表示
5. [css/style.css](css/style.css) で見た目とモバイル調整
6. [README.md](README.md) / [CLAUDE.md](CLAUDE.md) 更新

## 検証手順

`python3 -m http.server 8000` で起動し `http://localhost:8000` を開く。

### 施設名検索
- 「楠葉」で楠葉を含む事業所がサジェストに並び、選択で該当施設にズーム＋popup表示

### 住所ジオコーディング（街区レベル）
- 「津田元町1-1-1」「楠葉花園町10-85」→ サジェストに「住所」バッジで1件、選択で中心移動＋ピン＋「街区レベル」表示
- 「星丘4-33」→ `_ADDR_ALIASES` 展開（星ケ丘⇄星丘）でヒット確認
- 「大阪府枚方市招堤南町2丁目」→ 招堤⇄招提展開でヒット確認
- 全角数字「楠葉花園町１０－８５」→ 正規化でヒット確認

### 住所ジオコーディング（大字フォールバック）
- 「堤町」（番地なし）→ 大字レベルで町代表点＋「大字レベル」表示

### 失敗系
- 「東京都新宿区」→ 「該当住所が見つかりません」

### レスポンシブ
- ブラウザ幅 500px → navbar折り畳み時に検索ボックスが幅100%で表示される

## 出典・ライセンス遵守（重要）

国土交通省 位置参照情報の利用規約（https://nlftp.mlit.go.jp/isj/agreement.html ）を確認した結果：

- **再配布・JSON変換は可**：「利用者が編集・加工して作成した成果物」として許可されている。CC BY ではなく独自規約
- **必須**：「**街区レベル位置参照情報　国土交通省**」および「**大字・町丁目位置参照情報　国土交通省**」という**正式名称での出典明記**
- **推奨**：整備年（2024年）、ファイル名、編集・加工責任者の併記
- 高精度測量用途には使用不可（本プロジェクトは対象外）

現状 [index.html:57](index.html#L57) のフッターは「国土交通省 位置参照情報」という簡略表記で、**規約要求の正式名称になっていない**。この機会に修正する。

### 出典表記の修正

**[index.html](index.html) フッター**: 「国土交通省 位置参照情報」を以下に差し替え
```
街区レベル位置参照情報・大字・町丁目位置参照情報 国土交通省（2024年）
```

**[README.md](README.md)**: 同様に正式名称で記載。編集・加工責任者として本プロジェクト（hukushimap, aikautau）を明記。

**生成ファイル内のメタデータ**: `data/geocoding_gaiku.json` / `data/geocoding_oaza.json` の**先頭にライセンスコメント相当のキー**（`_source` / `_license`）を入れる。純粋な辞書を読むコードに影響しないよう、キー名は `_` 始まりで区別：

```json
{
  "_source": "街区レベル位置参照情報 国土交通省（2024年）",
  "_license": "出典明記を条件に自由利用可 https://nlftp.mlit.go.jp/isj/agreement.html",
  "_processed_by": "hukushimap (aikautau) — build_geocoding_index.py",
  "堂山三丁目\t13": [135.672438, 34.818786],
  ...
}
```

ブラウザ側では `_` で始まるキーを無視するだけで良い（lookup には影響しない）。

**[scripts/build_geocoding_index.py](scripts/build_geocoding_index.py)**: ファイル冒頭のdocstringにも出典と利用規約URLを明記。

**[CLAUDE.md](CLAUDE.md)** の「出典表記は必須」リストを正式名称に更新。

## スコープ外（将来拡張）

- キーボード操作（↑↓ Enter Esc）
- 検索ヒストリー（localStorage）
- ひらがな↔カタカナ変換
- あいまい検索（Levenshtein 距離）
- 「現在地から近い事業所」

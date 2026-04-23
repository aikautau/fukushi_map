---
version: alpha
name: hukushimap
description: >
  枚方市 介護事業所マップのためのデザインシステム。
  高齢のご本人・ご家族・ケアマネジャー・地域包括支援センター職員が、
  スマートフォンでもPCでも、落ち着いて情報を読み取れることを最優先にする。
  トーンは「温かく、清潔で、信頼できる自治体サービス」。

colors:
  # Base（紙のような暖色ベース。純白より柔らかい）
  bg: "#FAF7F2"
  surface: "#FFFDF9"
  surface-muted: "#F2EEE6"
  border: "#E7E2D9"
  border-strong: "#C9C2B6"

  # Text（やや青みを抑えたウォームブラック）
  text: "#1C1917"
  text-muted: "#57534E"
  text-subtle: "#78716C"
  text-on-primary: "#FFFDF9"

  # Primary（介護・医療・自治体らしい深緑。既存の包括センター色と調和）
  primary: "#0F6E4F"
  primary-hover: "#0B5A40"
  primary-soft: "#E6F1EC"
  primary-ring: "#9CCFB7"

  # Accent（CTA・ハイライト用の温かい琥珀）
  accent: "#C2681C"
  accent-hover: "#A4561A"
  accent-soft: "#FCEEDD"

  # Area polygon（圏域ポリゴン用、Primaryと調和するライムグリーン）
  area-stroke: "#1BA466"
  area-fill: "rgba(27, 164, 102, 0.08)"
  area-fill-selected: "rgba(27, 164, 102, 0.25)"

  # Status
  info: "#1565C0"
  info-soft: "#E8F1FB"

  # Category pins（既存維持。カテゴリ識別性を損なわないため触らない）
  cat-kyotaku: "#4CAF50"
  cat-day: "#FF9800"
  cat-riha: "#2196F3"
  cat-houmon: "#9C27B0"
  cat-takinou: "#F44336"
  cat-tanki: "#00BCD4"
  cat-shisetsu: "#795548"
  cat-yougu: "#607D8B"
  cat-center: "#0d7a42"

typography:
  # 日本語優先。Noto Sans JP は Google Fonts から CDN 読み込み。
  # 英数字は Inter、等幅はシステム。
  font-sans: >
    "Noto Sans JP", "Hiragino Sans", "Hiragino Kaku Gothic ProN",
    "Yu Gothic UI", "Meiryo", system-ui, -apple-system, "Segoe UI",
    Roboto, sans-serif
  font-mono: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace

  # Scale（16px 基準）。高齢ユーザー配慮で body を 16px に引き上げる。
  display:
    fontSize: 28px
    fontWeight: 700
    lineHeight: 1.3
    letterSpacing: "0.01em"
  h1:
    fontSize: 22px
    fontWeight: 700
    lineHeight: 1.35
  h2:
    fontSize: 18px
    fontWeight: 600
    lineHeight: 1.4
  body:
    fontSize: 16px
    fontWeight: 400
    lineHeight: 1.65
  body-strong:
    fontSize: 16px
    fontWeight: 600
    lineHeight: 1.65
  small:
    fontSize: 14px
    fontWeight: 400
    lineHeight: 1.5
  caption:
    fontSize: 12px
    fontWeight: 400
    lineHeight: 1.4
    color: "{colors.text-muted}"
  nav-label:
    # ツールバー内チェックボックスのラベル。情報量が多いので 13px にとどめる
    fontSize: 13px
    fontWeight: 500
    lineHeight: 1.3

spacing:
  # 4px ベース
  xs: 4px
  sm: 8px
  md: 12px
  lg: 16px
  xl: 24px
  "2xl": 32px

rounded:
  sm: 4px
  md: 8px
  lg: 12px
  pill: 9999px

shadows:
  # 柔らかく拡散する影。ウォームトーンを保つため黒より少し茶を含める
  sm: "0 1px 2px rgba(28, 25, 23, 0.06)"
  md: "0 2px 8px rgba(28, 25, 23, 0.08)"
  lg: "0 8px 24px rgba(28, 25, 23, 0.10)"
  popup: "0 4px 16px rgba(28, 25, 23, 0.15)"

components:
  navbar:
    # 既存の bg-dark から、淡いクリーム＋深緑アクセントに変更
    background: "{colors.surface}"
    borderBottom: "1px solid {colors.border}"
    textColor: "{colors.text}"
    brandColor: "{colors.primary}"
    height: 52px

  nav-checkbox-label:
    fontSize: "{typography.nav-label.fontSize}"
    padding: "6px 10px"
    rounded: "{rounded.md}"
    hoverBackground: "{colors.surface-muted}"

  input:
    background: "{colors.surface}"
    border: "1px solid {colors.border-strong}"
    borderFocus: "2px solid {colors.primary}"
    ringFocus: "0 0 0 3px {colors.primary-ring}"
    rounded: "{rounded.md}"
    padding: "8px 12px"
    fontSize: 15px

  button-primary:
    background: "{colors.primary}"
    backgroundHover: "{colors.primary-hover}"
    textColor: "{colors.text-on-primary}"
    rounded: "{rounded.md}"
    padding: "8px 16px"
    fontWeight: 600

  popup:
    background: "{colors.surface}"
    border: "1px solid {colors.border}"
    rounded: "{rounded.lg}"
    shadow: "{shadows.popup}"
    padding: "14px 16px 12px"
    titleColor: "{colors.primary}"
    titleWeight: 700
    labelColor: "{colors.text-muted}"

  search-suggest:
    background: "{colors.surface}"
    border: "1px solid {colors.border}"
    rounded: "{rounded.md}"
    shadow: "{shadows.lg}"
    itemHoverBackground: "{colors.primary-soft}"
    badgeBackground: "{colors.surface-muted}"
    badgeTextColor: "{colors.text-muted}"

  attribution-bar:
    background: "{colors.surface-muted}"
    textColor: "{colors.text-muted}"
    linkColor: "{colors.info}"
    borderTop: "1px solid {colors.border}"
    fontSize: 12px
    height: 32px
---

# hukushimap DESIGN

## Overview

枚方市の介護保険事業所を探すための地図アプリ。利用者は「身近な事業所を確認したい当事者・ご家族」「担当エリアを俯瞰したいケアマネ」「地域資源を把握したい包括センター職員」など、**年齢・ITリテラシー・閲覧環境が幅広い**。

トーンは派手さではなく「自治体の公共サービスらしい落ち着き」。主張しすぎない深緑と、情報密度を和らげる暖色クリームのベースで、**長時間見ていても疲れず、読み間違えない**画面を目指す。

## Colors

### 原則
- **ベースは純白を避ける**。`#FAF7F2` のクリームは、白より目に優しく、介護関係の印刷物（パンフレット・ケアプラン用紙）とも親和性が高い
- **Primary `#0F6E4F` は深緑**。信頼・医療・自治体のトーン。既存の地域包括支援センターピンの `#0d7a42` とシームレスに並ぶ色
- **Accent `#C2681C`（温かい琥珀）は最小限**に。CTAボタン・重要リンクのみ。多用しない
- **地図ピンの8カテゴリ色は既存を維持**。カテゴリ識別性はユーザビリティ上最重要で、彩度が高めなのはむしろ老眼ユーザに利点

### コントラスト
本文 `text: #1C1917` は `bg: #FAF7F2` に対して WCAG AAA 相当（19.4:1）。リンクの `info: #1565C0` も AAA を確保。**読みにくさ＝情報が届かないこと**を、この層のユーザでは避けなければならない。

## Typography

### 原則
- **日本語を主体**にするため第一候補は `Noto Sans JP`。端末フォントが `Yu Gothic UI`・`Hiragino Sans` のいずれでも破綻しないフォールバックを用意
- **本文は 16px**。Bootstrap のデフォルト（16px）は維持、既存コードの `.78rem` などの縮小指定は見直す
- ツールバー内の凡例ラベルだけは情報量の都合で **13px** に許容。ただし **色ドット＋テキスト** の二重符号化で補う

### Web font 読み込み
`index.html` から Google Fonts で `Noto Sans JP` の 400/500/700 を `display=swap` で読み込む。

## Layout

- ナビ高さ `52px`、フッター `32px`、間の領域を地図に割り当てる
- モバイル（<=991px）では凡例チェックボックスが折り返す。折り返し時も **タップターゲット最小 32px** を確保するため、ラベルの縦 padding を 6px 以上に
- 検索サジェストはモバイルで画面幅いっぱいまで広げる

## Elevation & Depth

地図が主役なので、UI の影は極力抑える。重ねる要素はポップアップと検索サジェストのみ。影の色は純黒ではなく **ウォームブラック（rgba(28,25,23,...)）** を使って、クリームベースと調和させる。

## Shapes

- カード・ポップアップは `rounded.lg = 12px`（やわらかいが子どもっぽくない）
- ボタン・入力は `rounded.md = 8px`
- バッジ・ピルは `rounded.pill`

## Components

### Navbar
既存の `navbar-dark bg-dark`（黒）を撤去し、**クリーム背景＋深緑アクセント**に。ブランドタイトル `枚方市 介護事業所マップ` は Primary で強調し、凡例チェックボックスは小さいアイコン＋ラベルのグリッドとして配置。

### Popup
事業所の属性テーブル。左カラム（項目名）は `text-muted`、右カラム（値）は `text`。タイトルは Primary で太字。スマホでの表示を優先し、`max-width: 320px`。

### Search
- 入力: 既存の `form-control-sm` から **通常サイズへ格上げ**（fontSize 15px）。誤タップが多い層を想定
- サジェスト: ホバー／選択時の背景は `primary-soft`（淡い緑）

### Attribution bar
出典表記は **CLAUDE.md のルールで削ってはいけない** 領域。小さく・色は落とすが、**下線つきリンク** で可読性を保つ。1行に収まらない場合は折り返しを許可する。

## Do's and Don'ts

### Do
- カテゴリピンの色は維持する
- 出典表記（厚労省・枚方市・国土地理院・位置参照情報・国土数値情報・papamama）は常に表示する
- 本文フォントサイズは 16px を下回らない（凡例ラベルの 13px のみ例外）
- Primary の深緑は地図の背景（地理院タイル淡色）の上でも視認できる濃さを維持する

### Don't
- 純黒 `#000` や純白 `#FFF` をベースにしない（ウォームトーンに揃える）
- Accent の琥珀色を複数箇所に散らさない（CTA と強調リンクのみ）
- カテゴリピンに漫画的な記号（★・♥ 等）を足さない。既存の円ピンのまま
- 装飾目的のアニメーションを足さない（高齢ユーザの気散を避ける）

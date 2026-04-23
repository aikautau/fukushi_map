# claude-review スキル（Claude サブエージェント版）

## Context

現在ユーザーレベル `~/.claude/skills/codex-review/` に置いてあるのは、
`BenedictKing/codex-review` を `npx skills add` でインストールする案内だけのラッパー。
実体の動作は OpenAI の Codex CLI に依存している。

ユーザーからの要望：
- Codex CLI を使わず、Claude Code のサブエージェント機構でコードレビューを実行したい。
- スキル名も刷新して `claude-review` に変えたい。
- 設置先はユーザーレベル（`~/.claude/`）。`codex-review` は削除。

Claude Code は `~/.claude/agents/*.md` に置いた YAML frontmatter 付き Markdown を
カスタムサブエージェントとして認識し、`Agent(subagent_type: "...")` 呼び出しで起動できる。
スキル側（`~/.claude/skills/<name>/SKILL.md`）にワークフローを書いておけば、
ユーザーが `/claude-review` を叩いた時にそのサブエージェントを呼ぶ、という構成が可能。

目的は「Codex 依存を外した、純 Claude 実装のコードレビュースキル」を成立させること。
CHANGELOG 自動生成など副次機能は切り落としてレビュー本体に絞る。

## 成果物

### 1. 新規サブエージェント定義
`~/.claude/agents/claude-reviewer.md`

frontmatter：
- `name: claude-reviewer`
- `description`: 「変更内容をレビューする専用サブエージェント。セキュリティ・正しさ・設計・読みやすさの 4 観点で指摘する。Agent ツールから subagent_type="claude-reviewer" で呼ばれる」
- `tools`: `Read, Grep, Glob, Bash` のみ（書き込み系は与えない — レビューアなので）
- `model`: 指定しない（親から継承）

本文（システムプロンプト）に以下を明記：
- 入力として渡されるのは「対象ブランチ / diff の範囲 / 追加の観点」
- 最初に `git status` と `git diff <base>...HEAD`（なければ `git diff`）で変更を取得する
- 変更の全ファイルを読む（diff だけでなく周辺コンテキストも確認）
- 以下 4 カテゴリで指摘を整理：
  1. **Security** — OWASP Top 10、秘密情報の混入、入力検証、権限
  2. **Correctness** — バグ、エッジケース、型の不整合、並行性
  3. **Design** — 責務分離、再利用、過剰抽象 / 過少抽象
  4. **Readability** — 命名、死んだコード、不要コメント
- 出力は**日本語**・Markdown・重要度（High / Medium / Low）付き
- 各指摘は `file:line` 形式のクリック可能リンクで場所を示す
- 良い点（keep）もひとつは拾う。改善提案は「なぜ」を一行添える
- 勝手にファイルを書き換えない。修正提案はコードブロックで示すのみ

### 2. 新規スキル定義
`~/.claude/skills/claude-review/SKILL.md`

frontmatter：
- `name: claude-review`
- `description`: 「Claude サブエージェントによるコードレビュー。変更差分を `claude-reviewer` サブエージェントに渡してセキュリティ・正しさ・設計・読みやすさの観点で指摘を受ける。Codex CLI などの外部依存なし。ユーザーが `/claude-review` を叩いたとき、またはコミット前の自主レビュー依頼で使う」

本文には、呼び出し手順を Claude 自身（親）向けに書く：
1. 引数を読む（例: ブランチ名、`--staged`、PR 番号）。無指定なら現在ブランチ vs `main`
2. `Agent` ツールを `subagent_type: "claude-reviewer"` で 1 回呼ぶ
3. プロンプトには「対象の差分範囲」「プロジェクトの CLAUDE.md の重要ルール（あれば抜粋）」「特に見てほしい点」を入れる
4. サブエージェントの結果をそのままユーザーへ提示。追加の自動修正はしない（ユーザー明示依頼がない限り）

### 3. 既存 codex-review の削除
`~/.claude/skills/codex-review/` を削除する。
（ユーザーが回答で明示した通り。`rm -rf` は破壊的なので実行時にユーザーへ一声かける）

## 修正 / 作成対象ファイル

- 作成: `~/.claude/agents/claude-reviewer.md`
- 作成: `~/.claude/skills/claude-review/SKILL.md`
- 削除: `~/.claude/skills/codex-review/` ディレクトリ一式（`SKILL.md` のみ）

## なぜこの構成か

- **スキル = 入口、サブエージェント = 実行者** という Claude Code の標準形に合わせる。
  同じサブエージェントをスキル以外（自然文の依頼、他スキル）からも再利用できる。
- サブエージェントに `tools` を `Read/Grep/Glob/Bash` に絞ることで、
  レビュー中に誤ってファイルを書き換えるリスクを構造的に排除できる。
- 親が Opus、サブエージェントも親継承（＝ Opus）なので Codex 相当以上の精度は現実的に出る。

## 検証

1. `ls ~/.claude/agents/claude-reviewer.md ~/.claude/skills/claude-review/SKILL.md` で配置確認
2. Claude Code を再起動し、利用可能スキル一覧に `claude-review` が出ることを確認
3. hukushimap リポジトリで軽微な変更を加えた状態で `/claude-review` を実行
4. 出力が日本語・4 カテゴリ・`file:line` リンク付きになっているかを目視
5. サブエージェントが `Write` / `Edit` を呼ばず、提案のみに留まっているかログで確認
6. 旧 `codex-review` がスキル一覧から消えていることを確認

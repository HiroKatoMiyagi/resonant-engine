# Resonant Engine V2

「AIの提案 A → 失敗 → 提案 B → 失敗 → A と同じものを C として再提案」
というループを、モデルが答え始める前に止めるための最小限の仕組み。

設計の背景と判断根拠は [`docs/v2/resonant_engine_v2_spec.md`](../docs/v2/resonant_engine_v2_spec.md) を参照。

## 仕組み

- **Stop hook** — そのターンでAIが出した提案を `pending` として保存する
- **PostToolUse hook** — コマンドの非ゼロ終了・テスト失敗を検出し、直近の `pending` を `failed` に確定する（黙っていても貯まる）
- **UserPromptSubmit hook** — 入力のたびに、(a) 失敗報告の発言があれば `pending` を `failed` に確定し、(b) 今回の入力に近い `failed` 経路を検索して、見つかれば証拠をモデルの文脈に注入する

判定（「これは同じか」）はしない。証拠を置くだけで、判断はそのセッションで動いているモデル本体に委ねる。

常駐プロセス・ポート・Docker・外部通信・追加の依存パッケージは一切ない。
データは `<project>/.resonant/attempts.db`（SQLite単一ファイル）に閉じる。

## 導入

### 前提確認

```bash
python3 -c "import sqlite3; print(sqlite3.sqlite_version)"   # 3.34 以上であること
```

### `.claude/settings.json` への登録

対象プロジェクトの `.claude/settings.json` に、以下をマージする
（既存の hooks 設定がある場合は配列に追記。置き換えないこと）。
`/ABSOLUTE/PATH/TO/resonant-v2` は実際のパスに置き換える。

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          { "type": "command", "command": "python3 /ABSOLUTE/PATH/TO/resonant-v2/hooks/on_stop.py" }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "python3 /ABSOLUTE/PATH/TO/resonant-v2/hooks/on_tool.py" }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "hooks": [
          { "type": "command", "command": "python3 /ABSOLUTE/PATH/TO/resonant-v2/hooks/on_prompt.py" }
        ]
      }
    ]
  }
}
```

設定後、`/hooks` を一度開いて設定を再読込するか、セッションを再起動する。

## CLI

```bash
./rv failed              # このプロジェクトの失敗済み経路
./rv why <キーワード>     # なぜその方向を捨てたか検索
./rv stats                # 注入回数・有効回数・誤検知回数
./rv useful               # 直近の注入を『役に立った』と記録
./rv falsepositive        # 直近の注入を『誤検知だった』と記録
```

## 成功判定（§7 of 仕様書）

数日使って `rv stats` の3つの数字だけを見る。

- 注入が出た回数
- そのうち `falsepositive` の割合
- **`useful` の回数（「これが無かったら同じことをしていた」）**

3つ目が1回でもあれば価値は確定。ゼロなら週末1つで止める。

## 既知の限界（正直に）

- **検索は「意味の近さ」ではなく「3文字以上の完全一致部分文字列」。**
  FTS5 trigram はそういう仕組みで、埋め込みではない。
  ファイル名・環境変数名・エラー文言・繰り返し語彙が一致すれば拾えるが、
  語彙が完全に異なる純粋な言い換えは拾えない（これが v0.2 で埋め込みを足す判断基準になる）。
- 再現率を優先しているため、一般的な言い回し（「〜しましょう」等）が
  たまたま一致して無関係な候補が混ざることがある。コストは低い（読んで無視されるだけ）ので許容している。
- `Stop` hook は transcript の JSONL 形式を前提に直近の assistant テキストを抜き出す。
  形式が変わった場合は `hooks/on_stop.py` の `extract_last_assistant_text` を調整する。
- 黙って話題を変えた失敗は拾えない（`PostToolUse` がコマンド失敗を拾える範囲に限られる）。
- Claude Code の中でのみ決定論的に動く。他クライアントからは対象外。

## ディレクトリ構成

```
resonant-v2/
├── core/
│   ├── store.py     SQLite単一ファイルへの全アクセス
│   ├── signals.py   失敗シグナルの検出規則
│   └── render.py    注入ブロックの整形
├── hooks/
│   ├── on_stop.py
│   ├── on_tool.py
│   └── on_prompt.py
├── rv               CLI
└── README.md
```

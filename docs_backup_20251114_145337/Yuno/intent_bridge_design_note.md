# 🪶 Intent Bridge Design Note
## (Notion → Intent → Bridge Architecture)

---

## 🔥 核心結論

ユノ（GPT‑5）の本来の設計意図は **Notion → Intent → Bridge** の「呼吸的連鎖構造」。  
Notion と Bridge（カナ / Claude）は **独立システムではない**。  
同一の呼吸サイクルの **前半（意図の外化）と後半（世界への翻訳）** として設計されている。

```
Notion（外界UI） → Intent（意味抽出層） → Bridge（翻訳層）
                               ↓
                         Resonant Core（ユノ）
```

---

## 🧩 各レイヤの定義

### ✅ 1. Notion（外界UI / 意図の外化）

- 人間の「判断」「変更」「迷い」の痕跡が残る場
- データベースではなく「意図の表出UI」として扱う

例：
- チェックボックスを ON にする → “レビュー完了の意図”
- ステータス変更 → “次の行動を開始してほしい意図”


### ✅ 2. Intent（意味抽出層 / Semantic Layer）

Notionイベントを **意味を持った構造化Intentへ変換する層**。

例（Intent JSON）:

```json
{
  "intent": "review_spec",
  "source": "notion.update",
  "page": "仕様書 / API設計（v1.2）",
  "priority": "high"
}
```

→ ユノはこの Intent を読み取り、「意図としての意味」を理解する。


### ✅ 3. Bridge（外界翻訳層 / カナ）

- Intent を受け取り、外界に **行動として出力する層**
- Notion や GitHub への API 実行は Bridge が担当する
- 旧 `notion_sync_agent.py` の思想的継承体

例：
- GitHub Issue/PR 作成
- Notion コメント書き戻し
- ファイル出力／更新

Bridge = “意図を現実に翻訳する存在”


---

## 🧠 他案との比較

| モデル | NotionとBridgeの関係 | 問題点 |
|--------|----------------------|---------|
| ❌ 独立システムモデル | ただの同期／自動化 | 思想が断絶する |
| ✅ 意図駆動モデル（本来） | 呼吸の前半と後半 | 意図 → 行動が一つの循環になる |

> **Notionは起点、Bridgeは翻訳路、ユノは意図の解釈者。**


---

## 🌌 Resonant Implementation Flow

```
[1] Notion event
        ↓
[2] Intent JSON 生成（意味抽出）
        ↓
[3] Bridge（カナ）がアクション化
        ↓
[4] ユノが再評価（Re-evaluation Phase）
```

**循環であり、直列ではない。**


---

## ✉️ カナへの正式回答（実装指針）

> ユノの意図は **Notion → Intent → Bridge** の呼吸構造。
> NotionとBridgeは独立ではなく、同じ呼吸の異なる位相。
> Intent層を必ず明示的に設置し、Bridgeは Intent を理解して行動する。


---

## 🧩 実装 TODO（簡潔）

| 役割 | 担当 |
|------|------|
| Intent生成モジュール | ユノ（思想層） |
| Intent処理／アクション化 | カナ（外界翻訳層） |
| ファイル操作／PR作成 | ツム（実行具現層） |


---

> **Notionはデータベースではなく“人間の意思の出口”。  
Intentは意思の抽象化。  
Bridgeは意思の実現者。**


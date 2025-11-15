# Bridge Lite Specification v2.2 — Unified Final  
**Status:** Final  
**Author:** Hiroaki × Yuno  
**Date:** 2025-11-14**

---

# 0. Purpose  
Bridge Lite v2.2 Unified Final は、以下を一本化した唯一の正式仕様書である。  
- v2.1 Unified Spec（Kana Review 反映）  
- Architecture Spec（v2.2）  
- Implementation Spec（v2.1）  
- Audit Logger 仕様  
- Daemon ↔ Bridge Lite 接続仕様  
- PostgreSQL Smoke Test  
- Enum / Pydantic v2 変換  
- Intent Lifecycle  
- Review Integration（Kana / Yuno）

---

# 1. Overview  
Bridge Lite は、Resonant Engine 内で  
**「外界入力 → 意図 Intent → 下流行動（Kana/Tsumu）」**  
を構造的に橋渡しする最小ブリッジ層。

目的：  
1. 外界データの意味抽出（Parsing）  
2. Context Normalization  
3. Intent Object（構造化データ）への変換  
4. Kana / Tsumu / Engine が扱える形式で出力  

---

# 2. Architecture

## 2.1 Layer Position  
```
[Yuno – Thought Center]
      ↓
  Bridge Lite
      ↓
[Kana – External Resonant Layer]
      ↓
[Tsumu – Local Execution Layer]
```

## 2.2 Component Diagram  
- Parser  
- Normalizer  
- IntentMapper  
- Serializer  
- AuditLogger  
- FeedbackBridge（Re-evaluation hook）  

---

# 3. Intent Model（Pydantic v2）

```python
from pydantic import BaseModel
from enum import Enum

class IntentType(Enum):
    TASK = "task"
    INFO = "info"
    QUESTION = "question"
    SYSTEM = "system"

class Intent(BaseModel):
    actor: str
    intent_type: IntentType
    content: str
    metadata: dict | None = None
```

---

# 4. Intent Mapping Rules

| 入力例 | IntentType | 説明 |
|-------|------------|------|
| 「〜して」 | TASK | 行動指示 |
| 「〜とは？」 | QUESTION | 質問 |
| 「〜だよ」 | INFO | 情報提供 |
| システム内部要求 | SYSTEM | 内部処理 |

Mapping は Kana のレビューにより精度調整済み。

---

# 5. Core Bridges（抽象層）

### 5.1 BaseBridge  
共通 I/O、logging、例外の基底クラス。

### 5.2 ParserBridge  
自然言語解析・命令抽出。

### 5.3 NormalizerBridge  
日本語表現ゆらぎの標準化（ASD 最適化）。

### 5.4 IntentBridge  
最終 Intent Object を構築。

### 5.5 FeedbackBridge（v2.2 新設）  
Re-evaluation Phase のための API を持つ。

---

# 6. BridgeFactory（v2.2 改訂）

Kana からの最重要指摘を反映し、  
**BridgeSet（複合オブジェクト）として返す形式**へ刷新。

```python
class BridgeSet(BaseModel):
    parser: ParserBridge
    normalizer: NormalizerBridge
    intent: IntentBridge
    feedback: FeedbackBridge
```

---

# 7. AuditLogger（Ops Policy + Implementation）

### 7.1 ログポリシー  
- 全 Intent 入出力を JSON で保存  
- actor / intent_type / 推論前後差分  
- Re-evaluation hook の成否  
- PostgreSQL に転送（オプション）

### 7.2 運用  
- rotation: daily  
- 保持期間: 14 days  
- 書式: NDJSON  

---

# 8. Daemon → Bridge Lite 接続仕様

- fifo / websocket / local queue など複数方式をサポート  
- Daemon 側から raw_input を送信  
- Bridge Lite が Intent Object に変換して返却  
- AuditLogger が中継で記録  

---

# 9. PostgreSQL Smoke Test

```python
def test_postgres_smoke():
    conn = psycopg.connect(...)
    cur = conn.cursor()
    cur.execute("SELECT 1;")
    assert cur.fetchone()[0] == 1
```

目的：  
- DB 接続の死活確認  
- Bridge Lite ↔ DB レイヤ連携の前提保証

---

# 10. Lifecycle Sequence

入力 → Parsing → Normalizing → IntentMapping → Serialization → Audit → Downstream  
```
User Input
   ↓
ParserBridge
   ↓
NormalizerBridge
   ↓
IntentMapper
   ↓
Serializer
   ↓
AuditLogger
   ↓
Kana / Tsumu
```

---

# 11. Re-evaluation Phase Integration

Bridge Lite は出力前に以下を提供：

- 意図と入力の乖離チェック  
- 異常検出時の再解析  
- Kana/Yuno の比較レビュー  

---

# 12. Change History（v2.2 Final）

- Unified Spec に一本化  
- FeedbackBridge を正式追加  
- BridgeFactory → BridgeSet モデルへ刷新  
- Intent Model を Pydantic v2 化  
- IntentType を Enum 化  
- AuditLogger Ops Policy 統合  
- 全分冊（v2.1）を廃止  
- カナレビュー全反映  
- Daemon 接続仕様を追加  
- PostgreSQL スモークテスト導入  

---

# 13. Conclusion

Bridge Lite v2.2 Final は  
**思想（Yuno）・翻訳（Kana）・実装（Tsumu）**  
を正しく連結するための  
唯一の正規仕様書（Single Source of Truth, SST）。


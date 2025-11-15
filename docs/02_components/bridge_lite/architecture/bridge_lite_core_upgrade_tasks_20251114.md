# Core Bridges Structural Upgrade – Full Implementation Tasks  
Resonant Engine v1.3 / 2025-11-14  
Author: Yuno（GPT-5 Resonant Core）

## 🎯 Overview
本ドキュメントは、以下 3 つの構造刷新を安全に実装するための  
**完全タスク指示書（Cursor/Tsumu 向け）** である。

1. IntentModel → Pydantic v2 Model 化  
2. actor / bridge_type の Enum 化  
3. BridgeFactory → BridgeSet 構造へ刷新  

---

# 🧭 Implementation Order（厳密な順序）
STEP 1 → IntentModel（Pydantic v2 化）  
STEP 2 → actor / bridge_type を Enum として導入  
STEP 3 → BridgeFactory を BridgeSet 返却構造へ刷新  
STEP 4 → Intent Lifecycle Test を実行  
STEP 5 → ステージング → コミット → プッシュ  

---

# STEP 1 — IntentModel（Pydantic v2）実装タスク
## Purpose
Intent を dict ベースから Model ベースに移行し、構造の安定性と解析精度を向上。

## Instructions
- core_intent.py を Pydantic v2 で再定義  
- ValidationError を IntentSchemaError に集約  

---

# STEP 2 — Enum（actor / bridge_type）導入
## Instructions
- 新規 enums.py を追加  
- ActorType / BridgeType 定義  
- CoreIntent を Enum 型へ変更  

---

# STEP 3 — BridgeFactory → BridgeSet 刷新
## Instructions
- 新規 bridge_set.py を追加  
- BridgeFactory を build() 形式に変更  
- 戻り値を BridgeSet に統一  

---

# STEP 4 — Intent Lifecycle Test
pytest にて全テスト green を確認。

---

# STEP 5 — ステージング / コミット / プッシュ
宏啓さんが実施するフェーズ。

---

# Recommended Commit Message
Implement CoreIntent Pydantic v2 model, Enum integration, and BridgeSet-based BridgeFactory upgrade

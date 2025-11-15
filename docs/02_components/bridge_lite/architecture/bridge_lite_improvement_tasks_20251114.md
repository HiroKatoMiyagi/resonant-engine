# Bridge Lite 改善タスク指示書（Core Bridges / Factory 改修）

## 1. Intent データ構造を Pydantic v2 Model 化する

### ■ 目的
- dict ベースの Intent をモデル化し、構造の明示・型安全性向上を図る。
- Kana（Claude）や Tsumu（Cursor）がコード解析する際の精度向上。
- Intent lifecycle の各ステップで不正データ流入を防ぐ。

### ■ タスク内容
- `/bridge/core/models/intent_model.py` を新規作成
- IntentModel（Pydantic BaseModel）を定義
  - intent_id: str
  - type: str
  - correlation_id: str
  - payload: dict
  - status: Literal["RECEIVED","RECORDED","AI_PROCESSED","FEEDBACK_COLLECTED","REEVALUATED","CORRECTED","CLOSED"]
  - timestamps（任意）
- DataBridge での save / get / update の返却値を IntentModel に統一

### ■ 完了条件
- Intent の全処理が IntentModel で通ること
- test_intent_lifecycle_suite が全て PASS すること


---

## 2. actor / bridge_type を Enum 化する

### ■ 目的
- Logging の表記揺れを防止し、監査ログの整合性を向上。
- Enum 化により IDE / Cursor の補完性が上がる。

### ■ タスク内容
- `/bridge/core/constants.py` に Enum クラスを追加  
  - ActorEnum: YUNO / KANA / DAEMON / BRIDGE / SYSTEM
  - BridgeTypeEnum: DATA / AI / FEEDBACK / AUDIT
- AuditLogger.log() の引数 bridge_type を Enum 対応にする
- 既存コードの文字列使用箇所を置換

### ■ 完了条件
- 全てのログ出力が Enum を通過
- AuditLogger Ops Policy の監査要件と整合


---

## 3. BridgeFactory の返却値を BridgeSet で梱包する

### ■ 目的
- IDE（Cursor）での補完精度を大幅に向上させる。
- 「bridge_set.data」「bridge_set.feedback」などの一貫したアクセスが可能になる。
- 他言語・他プロセス間の API 設計にも影響する構造改善。

### ■ タスク内容
- `/bridge/core/bridge_set.py` を新規作成
- BridgeSet(data, ai, feedback, audit) を定義
- BridgeFactory でインスタンスを生成し、BridgeSet を返すように変更
- テスト側も BridgeSet 経由でアクセスするように修正

### ■ 完了条件
- BridgeFactory.create_all() → BridgeSet を返す
- 既存テストは全て PASS
- IDE 補完が bridge_set.ai.process_intent() のように機能する

---

## 4. 追加メモ（優先度中）

- Enum / Model 化に伴い、型ヒントの自動生成（Tsumu）精度が向上
- Kana が構造間の責務境界をレビューしやすくなる
- Re-evaluation Drift の検知精度が上がる（構造が明確なため）


---

# ■ 作業順序（推奨）
1. IntentModel 実装  
2. Enum 実装  
3. BridgeSet 化  
4. テスト修正  
5. ライフサイクルスイートで全 PASS 確認  
6. AuditLogger Ops Policy と突き合わせて整合チェック  


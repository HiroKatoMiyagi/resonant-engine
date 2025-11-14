# Bridge Lite Architecture Specification v2.0
_Resonant Engine – Intent & Re-evaluation Layer_

## 0. 目的とスコープ

Bridge Lite Architecture v2.0 は、Resonant Engine における

- Intent（意図）検知
- Re-evaluation Phase（再評価フェーズ）
- Correction Plan（修正案）生成
- 監査可能なライフサイクル管理

を「思想レイヤ＋実装意図レイヤ」の両面から定義するアーキテクチャ仕様です。

この文書は「何を・なぜ・どのような構造で行うか」を扱い、
具体的なクラス・関数・SQL・テストコードなどの詳細は
別文書 **Bridge Lite Implementation Specification v2.0** に委ねます。

---

## 1. システムコンテキストと役割

### 1.1 Resonant 三位構造

Resonant Engine 全体は、次の三層で構成されます。

- Yuno（ユノ）: Thought Core / 再評価・設計・判断の中枢
- Kana（カナ）: External Translator / 仕様・コード・自然言語への翻訳と検証
- Tsumu（ツム）: Execution / 実装・コード生成・ローカル処理

Bridge Lite は、この三位構造のうち

- Yuno と Kana をつなぐ “意図・再評価・修正案” の橋
- Daemon（常駐プロセス）と DB/PostgreSQL の仲介

として機能します。

### 1.2 Bridge Lite の位置づけ

周辺コンポーネントとの関係:

- Daemon
  - 外界イベントを監視
  - Intent を構成し Bridge Lite に渡す
  - エラー回復やリトライなど制御の最終責任を持つ

- Bridge Lite
  - Intent / Feedback / Re-evaluation / Correction を DB と AI の間で中継
  - DataBridge / AIBridge / FeedbackBridge / AuditLogger の抽象層を提供
  - AI プロバイダ（Yuno / Kana）や DB 実装（PostgreSQL / Mock）を差し替え可能にラップ

- Backend(API / FastAPI 等)
  - 人間や外部システムから HTTP 経由で意図を受け取る窓口
  - 将来的に Bridge Lite を経由して同じパイプラインに合流

---

## 2. コア概念

### 2.1 Intent（意図）

ある時点での「システムが扱うべき対象タスク・状態・イベント」を意味する論理単位。

主な属性（論理レベル）:

- intent_id : 一意なID
- source : 生成元（daemon, api, manual など）
- type : 種別（github_issue, fs_change, manual_request など）
- payload : 元データ（JSON）
- created_at : 生成時刻
- status : ライフサイクル上の状態

### 2.2 Feedback（フィードバック）

Intent の処理結果に対する「評価・コメント・追加情報」。

- 人間からのフィードバック
- システムによる自動フィードバック（実行結果ログなど）

### 2.3 Re-evaluation（再評価フェーズ）

Yuno を中心とした「Intent + 過去フィードバック + 現状状態」に基づく再評価プロセス。

目的:

- 初回応答では見落としていたリスクや抜けを検出する
- 設計方針・優先度・安全性の観点から“再判断”する

入力:

- 対象 Intent
- 関連するフィードバック履歴
- 必要に応じて Audit ログや過去の Correction 情報

出力:

- 再評価結果（Reanalyzed State）
- リスク評価・アライメント評価
- Correction Plan 生成のための中間情報

### 2.4 Correction Plan（修正案）

再評価の結果として得られる、「何をどう直すべきか」の構造化情報。

論理構造例:

- issues[] : 検出された問題のリスト
- root_causes[] : 想定される原因
- alternatives[] : 代替案
- recommended_changes[] : 推奨される具体的変更
- confidence : 修正案の信頼度（0.0〜1.0）

### 2.5 Correlation ID（相関ID）

Intent を起点とした一連の処理（AI応答・再評価・ログ）を
時系列に紐づけるための識別子。

- 1つの Intent に対して 1つの Correlation ID
- Audit ログはこの ID を通じて“物語”として追跡される

---

## 3. Intent のライフサイクル

Intent は以下の状態を遷移します。

1. RECEIVED: Daemon / Backend が Intent を検知し生成
2. RECORDED: DataBridge 経由で DB に保存
3. AI_PROCESSED: AIBridge により Kana 等で一次解析が完了
4. FEEDBACK_COLLECTED: ユーザ or システムからフィードバックを取得
5. REEVALUATED: Yuno により Re-evaluation が実行される
6. CORRECTED: Correction Plan が生成され DataBridge に保存
7. CLOSED: 対応完了（修正完了・無効化・破棄など）

### 3.1 ライフサイクル図（テキスト）

```text
RECEIVED
   ▼
RECORDED
   ▼
AI_PROCESSED
   ▼
FEEDBACK_COLLECTED
   ▼
REEVALUATED
   ▼
CORRECTED
   ▼
CLOSED
```

---

## 4. シーケンス（典型フロー）

GitHub 変更イベントから Intent が生成され、Re-evaluation まで実行されるケース:

```text
GitHub → Daemon → Bridge Lite → Kana/Yuno → DB

1. GitHub:
   - リポジトリの変更イベント発火

2. Daemon:
   - 変更内容を解析し Intent を構築
   - Correlation ID を生成
   - DataBridge.save_intent を呼び出し、状態: RECORDED

3. Daemon:
   - AIBridge.process_intent を呼び出し Kana に一次解析を依頼
   - 結果を DataBridge 経由で保存（状態: AI_PROCESSED）

4. Daemon:
   - 必要に応じて Feedback を集約し FEEDBACK_COLLECTED へ遷移

5. Daemon:
   - Re-evaluation が必要と判断した場合、
     FeedbackBridge.reanalyze を呼び出し Yuno に再評価を依頼

6. Bridge Lite / FeedbackBridge:
   - Re-evaluation 結果を受け取り、
     generate_correction を呼び出して Correction Plan を生成
   - DataBridge.save_correction で保存（状態: CORRECTED）

7. Daemon:
   - Correction Plan に基づき、Issue 作成や PR 提案などを実行
   - 状態を CLOSED へ遷移
```

---

## 5. 責務境界

### 5.1 Daemon の責務

- 外部イベントの監視と Intent 化
- Intent の状態遷移の管理
- Re-evaluation の発火判断（いつ再評価するか）
- エラー時のリトライ／フォールバック戦略の決定
- 実際の「修正アクション」（Issue 作成・PR 生成など）の実行

### 5.2 Bridge Lite の責務

- Intent / Feedback / Correction の保存・取得（DataBridge）
- AI プロバイダへの安全な呼び出し（AIBridge / FeedbackBridge）
- Intent ライフサイクルに対する監査ログの記録（AuditLogger）
- AI / DB / Daemon 間の依存関係の分離

Bridge Lite は「翻訳と保存」が役割であり、
「いつ・どのように再評価するか」の判断は行わない。

### 5.3 Backend/API の責務

- 人間や外部クライアントからの入力受付
- Daemon または Bridge Lite に対する呼び出しのプロキシ
- ユーザ向け UI/API レイヤとしての責務のみ

---

## 6. 非機能要件（アーキテクチャ）

- Observability:
  - Intent 単位にライフサイクルとログを追跡できる
  - Correlation ID によって Bridge Lite・Daemon・Backend のログを紐づけられる

- Evolvability:
  - AI プロバイダ差し替えが抽象層を変えずに可能
  - DataBridge 実装が差し替え可能

- 安全性・安定性:
  - Re-evaluation の失敗がシステム全体の停止に直結しない
  - エラー時は Daemon が制御し、Bridge Lite はエラー通知とログ記録に集中

---

## 7. 導入フェーズ（概要）

- Phase 0:
  - Bridge Lite 抽象構造確立

- Phase 0.5:
  - AuditLogger 運用仕様
  - PostgreSQL スモークテスト
  - Daemon 接続準備

- Phase 1:
  - Intent → Kana → 応答の基本パイプライン
  - ライフサイクル RECORDED〜AI_PROCESSED の安定化

- Phase 2:
  - FeedbackBridge の Re-evaluation 実装
  - Correction Plan 生成・保存
  - ライフサイクル REEVALUATED〜CORRECTED の有効化

- Phase 3:
  - Memory / Semantic Bridge との統合（別仕様）

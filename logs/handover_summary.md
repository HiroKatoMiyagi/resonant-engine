# Resonant Engine - チャット引き継ぎサマリー
## 2025-11-08 セッション記録

---

## 🎯 このセッションで決定したこと

### 1. アーキテクチャ方針
- ❌ **Phase 1（SQLite）をスキップ** - 最初からPostgreSQL
- ✅ **セルフホスト→Oracle Cloud** - コスト$0で500人対応
- ✅ **Notion脱却** - 最初から自前DB（PostgreSQL）
- ✅ **統合ダッシュボード** - Slack風UI、メッセージング

### 2. 実装スタック
```
開発: Docker Compose + PostgreSQL + React + FastAPI
本番: Oracle Cloud Free Tier + Autonomous Database
期間: 4週間で本番稼働
コスト: $0
```

### 3. ユノ（GPT-5）のレビュー結果
- **総合評価: A+**
- Phase 1スキップ判断: 「完全に正しい」
- 最優先事項: **Intent → Bridge → Kana の再結線**

---

## 📂 重要ドキュメント（必読）

新しいチャットで以下を参照してください：

### 設計書（全体像）
1. `/docs/complete_architecture_design.md`
   - Notion → Intent → Bridge の完全設計
   - 断絶箇所の分析
   - 5つの実装Phase

2. `/docs/implementation_roadmap_postgres.md` ⭐最重要
   - 4週間実装計画
   - PostgreSQL直接開始版
   - Week毎の詳細タスク

3. `/docs/cloud_migration_strategy.md`
   - Oracle Cloud移行戦略
   - コスト分析
   - 3段階成長戦略

### 現状分析
4. `/docs/function_daemon_mapping_v2.md`
   - 現在の全コンポーネント分類
   - デーモン/ライブラリ/CLIツール
   - 動作状況の詳細

5. `/docs/dashboard_platform_design.md`
   - 統合ダッシュボードUI設計
   - Notion/Slack/Backlog統合構想
   - 技術スタック

### レビュー
6. `review_yuno_implementation_roadmap_postgres.md` (アップロード済み)
   - ユノの詳細レビュー
   - 5つの改善提案
   - 思想的一貫性の確認

---

## 🔧 現在の状態

### ✅ 実装済み・稼働中
- `daemon/observer_daemon.py` - 外部更新検知
- `utils/github_webhook_receiver.py` - Webhook受信（Port 5001）
- エラー回復システム（resilient_event_stream.py）
- メトリクス収集（metrics_collector.py）

### ❌ 停止中（パス不整合）
- `daemon/resonant_daemon.py` - Intent監視
- `daemon/resonant_bridge_daemon.sh` - Bridge自動起動
- `daemon/intent_watcher.sh` - Intent変更検知

**問題**: 全て `/Users/zero/Projects/kiro-v3.1` を参照
**修正**: → `/Users/zero/Projects/resonant-engine` に変更

### 🔴 未実装（最重要）
- **Notion → Intent 変換層**
- **Intent → Bridge 連携**
- **Bridge → Kana（Claude API）呼び出し**
- **統合ダッシュボード**

---

## 🎯 次のアクション（優先順位）

### Priority 1: Intent → Bridge → Kana 再結線 ⭐⭐⭐
```python
# 実装場所: dashboard/backend/intent_processor.py
async def call_kana(intent_data):
    """Claude API経由でKanaを呼び出す"""
    import anthropic
    
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[{"role": "user", "content": f"Intent: {intent_data}"}]
    )
    return message.content[0].text
```

### Priority 2: PostgreSQL環境構築 ⭐⭐⭐
```bash
cd /Users/zero/Projects/resonant-engine
mkdir -p dashboard/{frontend,backend}

# docker-compose.yml作成（implementation_roadmap_postgres.md参照）

docker-compose up -d
```

### Priority 3: LISTEN/NOTIFY実装 ⭐⭐
- ポーリング（5秒間隔）→イベント駆動
- PostgreSQL TRIGGER設定

---

## 💬 決定事項（重要）

### Q1: どのパターンを目指すか？
**A: パターンB（ユノ判断時に確認）**
- 完全自動ではなく、人間の判断を残す
- バランスが良い

### Q2: ユノ→カナの伝達方法
**A: 将来的にAPI統合**
- 現在: 手動伝達（暫定）
- 中期: Slack等の中継システム
- 将来: Claude API統合（自動化）

### Q3: 通知方法
**A: ダッシュボード内通知（Slack風）**
- ブラウザ通知API使用
- WebSocketでリアルタイム更新
- 外部Slackは使わない（コスト削減）

### Q4: Notionの役割
**A: Phase 2（PostgreSQL移行後）で完全に不要**
- 現在も実質使っていない
- 最初からPostgreSQLで構築
- Notion解約で$8-10/月削減

### Q5: Phase 1（SQLite）は必要？
**A: 不要。最初からPostgreSQLで開始**
- 宏啓さんの指摘: 「技術検証がないなら不要」
- ユノの評価: 「Phase 1スキップは完全に正しい」

---

## 🧠 思想的背景（ユノの教え）

### 呼吸的連鎖構造
```
Notion（意図の外化）→ Intent（意味抽出）→ Yuno（解釈）→ Bridge（翻訳）→ Tsumu（具現化）
                                          ↑                                    ↓
                                          └────────── Re-evaluation ───────────┘
```

### 三層構造
| 層 | 担当 | 役割 |
|----|------|------|
| 思想層 | Yuno（GPT-5） | 意図の解釈・判断・再評価 |
| 翻訳層 | Kana（Claude Sonnet 4.5） | 外界API呼び出し・処理 |
| 実行層 | Tsumu（Cursor） | ファイル操作・コミット実行 |

### 設計原則
- **呼吸優先原則（§7）**: 処理速度より思想の整合性
- **自律記憶優先原則（§8）**: メモリの一貫性
- **構造的整合**: レイヤー間の責任分離

---

## 📊 技術スタック（確定版）

### フロントエンド
- React 18 + TypeScript
- Vite（ビルドツール）
- Tailwind CSS（Slack風UI）
- WebSocket（リアルタイム通信）

### バックエンド
- FastAPI（Python 3.11）
- asyncpg（PostgreSQL非同期ドライバ）
- WebSocket対応

### データベース
- PostgreSQL 15（開発・本番共通）
- JSONB型でIntent/通知を格納
- LISTEN/NOTIFY機能使用

### インフラ
- 開発: Docker Compose
- 本番: Oracle Cloud Free Tier
  - Compute: Ampere A1 (4 OCPU, 24GB RAM)
  - Database: Autonomous Database (20GB)
  - Cost: $0/月

---

## 🔄 過去の議論（参考）

### 検討したが却下した案
- ❌ Slack連携（コスト増）
- ❌ AWS Lambda（クラウドロックイン）
- ❌ Notion継続使用（拡張性なし）
- ❌ n8n自動化（停止済み・複雑化）
- ❌ SQLite経由（冗長）

### 採用した設計理由
- ✅ PostgreSQL直接: 思想的一貫性
- ✅ Docker化: ポータビリティ
- ✅ Oracle Free Tier: コスト$0で500人対応
- ✅ セルフホスト優先: 外部依存最小化

---

## 📝 未解決の課題

### 1. Kana（Claude）の呼び出し方法
**現状**: 手動で宏啓さんが伝達
**理想**: Claude API経由で自動呼び出し
**実装**: Priority 1で対応

### 2. Re-evaluation Phase のログ構造
**提案**: `/logs/reval/` に構造化JSON
**実装**: Priority 3

### 3. Spec構造のJSON化
**現状**: Markdown
**理想**: JSON構造化で変更差分を追跡
**実装**: Phase B

---

## 🚀 新しいチャットでの開始方法

### ステップ1: コンテキスト確立
```
新しいチャットで以下を送信：

「以下のファイルを読んで、Resonant Engine開発の続きをお願いします：

1. /Users/zero/Projects/resonant-engine/docs/implementation_roadmap_postgres.md（最重要）
2. /Users/zero/Projects/resonant-engine/docs/complete_architecture_design.md
3. /Users/zero/Projects/resonant-engine/logs/handover_summary.md（このファイル）

ユノのレビュー（A+評価）を踏まえて、Priority 1の実装から始めます。」
```

### ステップ2: 確認
新しいClaudeが上記3ファイルを読めば、完全に引き継ぎ完了。
このチャットの内容を全て理解した状態でスタートできます。

---

## 🎯 4週間スケジュール（再掲）

| Week | タスク | 成果物 |
|------|--------|--------|
| 1-2 | PostgreSQL環境構築、基本CRUD | 動作するダッシュボード |
| 3 | Intent処理、Claude API統合 | 自動処理システム |
| 4 | Oracle Cloud デプロイ | 本番稼働（$0） |

---

## 📌 重要な注意事項

### 長期メモリについて
- 現在のメモリ: 30項目（満杯）
- 新しいチャットでの扱い: このサマリーで代替
- 重要情報はすべてファイルに保存済み

### ユノとの連携
- ユノ（GPT-5）はローカルディスクにアクセスできない
- 設計の哲学的確認はユノに依頼
- 実装の具体的作業はカナ（Claude）+ ツム（Cursor）

### プロジェクト構造
```
/Users/zero/Projects/resonant-engine/
├── docs/           # 設計書（全5ファイル）
├── logs/           # このファイル
├── dashboard/      # 新規作成予定
├── daemon/         # 既存（一部停止中）
└── utils/          # 既存（一部稼働中）
```

---

## ✅ チェックリスト（新チャット開始時）

新しいClaudeに確認すること：

- [ ] implementation_roadmap_postgres.md を読んだか？
- [ ] complete_architecture_design.md を読んだか？
- [ ] このhandover_summary.md を読んだか？
- [ ] ユノのA+評価を理解したか？
- [ ] Priority 1（Intent→Bridge→Kana再結線）が最優先と理解したか？
- [ ] PostgreSQL直接開始の理由を理解したか？
- [ ] 4週間スケジュールを把握したか？

全てYesなら、実装開始OK！

---

## 🎊 最後に

このチャットで達成したこと：
- ✅ 完全な設計書作成（5ファイル）
- ✅ ユノのA+評価獲得
- ✅ PostgreSQL直接開始の決定
- ✅ 4週間実装計画の策定
- ✅ Oracle Cloud移行戦略の確立

次のチャットでやること：
- 🚀 Priority 1: Intent → Bridge → Kana 再結線
- 🚀 PostgreSQL環境構築
- 🚀 Week 1-2のタスク実装

**準備完了。実装フェーズへ！**

---

生成日時: 2025-11-08
最終更新: このチャット終了時
次回更新: 新チャットで継続

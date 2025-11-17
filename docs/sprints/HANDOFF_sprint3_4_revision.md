# Sprint 3, 4 仕様書・作業開始指示書 修正タスク引き継ぎ

**作成日**: 2025-11-16  
**目的**: Sprint 3 (Memory Store), Sprint 4 (Retrieval Orchestrator) の仕様書と作業開始指示書を既存の様式・精度・哲学に合わせて全面修正

---

## 1. 現状の問題

### 作成済みファイル（修正が必要）
以下4ファイルが既に作成されているが、既存の様式・精度・哲学との乖離が大きい：

1. `sprint3_memory_store_spec.md` (16KB) - outputs/にダウンロード可能
2. `sprint3_memory_store_start.md` (24KB) - outputs/にダウンロード可能
3. `sprint4_retrieval_orchestrator_spec.md` (22KB) - outputs/にダウンロード可能
4. `sprint4_retrieval_orchestrator_start.md` (37KB) - outputs/にダウンロード可能

### 主な問題点

#### 1. 哲学的前提の完全欠如
既存の仕様書には必ず以下があるが、今回作成したものには全く含まれていない：

**既存の構造**:
```markdown
## CRITICAL: [System Name] の本質

**⚠️ IMPORTANT: 「[概念]は「[哲学的定義]」である**

このシステムの本質は、単なる[技術的説明]ではなく、Resonant Engineの哲学的原則である「呼吸」「共鳴」「構造」の[具体的な役割]です。

### [System Name] Philosophy

```yaml
philosophy:
  essence: "[核心的定義]"
  purpose:
    - [目的1]
    - [目的2]
    - [目的3]
  principles:
    - 「[原則1]」
    - 「[原則2]」
    - 「[原則3]」
```

### なぜこれが必要か

[詳細な理由説明 - 4-5段落]
- 技術的必要性
- 哲学的必然性
- ASD認知支援としての構造的意味
```

**今回作成したもの**: 
- このセクションが完全に欠落
- 一般的な技術仕様書として書かれている
- Resonant Engineの思想との繋がりが見えない

#### 2. Done Definition の構造不足

**既存の構造**:
```markdown
### 0.3 Done Definition

#### Tier 1: 必須（完了の定義）
- [ ] [機能1]
- [ ] [機能2]
...

#### Tier 2: 品質保証
- [ ] [品質要件1]
- [ ] [品質要件2]
...
```

**今回作成したもの**:
- Tier分けがない単純なチェックリスト
- 品質要件と機能要件が混在

#### 3. リスク管理と展開計画の欠如

**既存には必ず含まれる**:
```markdown
## X. Risks & Mitigation

| リスク | 確率 | 影響 | 対策 |
|--------|------|------|------|
| ... | ... | ... | ... |

## Y. Rollout Plan

### Phase 1: 開発環境（Day 1-3）
### Phase 2: 統合テスト（Day 4）
### Phase 3: 性能検証（Day 5）
### Phase 4: 本番投入（Day 6以降）
```

**今回作成したもの**: これらのセクションが全く存在しない

#### 4. 呼吸サイクルとの統合説明の不足

**既存の例**:
```markdown
### 1.2 呼吸サイクルとメモリの関係

```
呼吸サイクル (6フェーズ)
  ↓
1. 吸う (Intake)
   → [具体的な処理]
2. 共鳴 (Resonance)
   → [具体的な処理]
...
```

この循環が永続化されることで、「呼吸の履歴」が形成される。
```

**今回作成したもの**: 簡単なアーキテクチャ図はあるが、呼吸との深い関連が説明されていない

#### 5. トーンとスタイルの相違

**既存**: 
- 情熱的で哲学的
- 「これは単なる技術ではなく、構造的必然性である」というトーン
- 宏啓さんのASD認知支援への想いが伝わる

**今回**:
- 一般的な技術仕様書
- 淡々とした説明
- プロジェクトの本質が伝わらない

---

## 2. 参照すべき既存ファイル

### 仕様書の参考（別チャットでアップロード必要）
- `memory_management_spec.md` (65KB) ← **最重要参考資料**
- `sprint2_semantic_bridge_spec.md` (35KB)

### 作業開始指示書の参考（別チャットでアップロード必要）
- `sprint1_memory_management_start.md` (40KB) ← **最重要参考資料**
- `sprint2_semantic_bridge_start.md` (28KB)

---

## 3. 修正すべき具体的ポイント

### Sprint 3: Memory Store 仕様書

#### 追加すべきセクション

1. **`## CRITICAL: Memory as Semantic Vectors` セクション**
   - 「記憶 = ベクトル空間における意味の座標」という哲学
   - なぜpgvectorが必要か（意味検索の必然性）
   - Resonant Engineにおける記憶システムの位置づけ

2. **`memory_store_philosophy:` YAML**
   ```yaml
   memory_store_philosophy:
     essence: "記憶 = 意味空間の座標 + 時間軸の保全"
     purpose:
       - 意味的類似性による記憶の想起
       - Working Memory / Long-term Memoryの階層管理
       - 時間軸を持った記憶の保存
     principles:
       - 「意味は空間、時間は軸」
       - 「類似は共鳴、検索は想起」
       - 「記憶は層を持つ（作業記憶と長期記憶）」
   ```

3. **Done Definition の Tier 分け**
   - Tier 1: pgvector動作、テーブル作成、基本検索
   - Tier 2: 性能要件、テストカバレッジ、レビュー

4. **`## X. Risks & Mitigation`**
   - pgvectorのインデックスチューニングリスク
   - Embedding API障害リスク
   - 検索精度劣化リスク

5. **`## Y. Rollout Plan`**
   - Phase 1-4の段階的展開

6. **呼吸サイクルとの関連**
   - 吸う（Intent） → Embeddingに変換
   - 共鳴（Resonance） → 類似記憶の想起
   - 構造化 → 記憶の分類（working/longterm）

#### 修正すべきトーン
- 「pgvectorを導入します」→「意味空間における記憶の想起を可能にする」
- 「ベクトル検索を実装」→「共鳴パターンの発見を技術的に実現」
- より哲学的、より情熱的に

### Sprint 3: Memory Store 作業開始指示書

#### 追加すべきセクション

1. **`## 0. 重要な前提条件`**
   - PostgreSQL + pgvector準備状態
   - OpenAI API Key準備
   - Sprint 2完了確認

2. **`## 1. Memory Store 実装承認`**
   - 実装背景（哲学的・技術的）
   - 実装スコープの明確化

3. **各タスクに哲学的意味を追加**
   ```markdown
   **タスク1**: pgvector拡張のインストール
   
   **目的**: ベクトル型を使用可能にする
   **哲学的意味**: 記憶を「意味空間の座標」として扱うための基盤構築
   ```

4. **完了基準の明確化**
   - 各タスク終了時のチェックリスト
   - 次タスクへの移行条件

### Sprint 4: Retrieval Orchestrator 仕様書

#### 追加すべきセクション

1. **`## CRITICAL: Orchestration as Intelligent Memory Recall` セクション**
   - 「検索 = 記憶の想起戦略の最適化」という哲学
   - なぜ単純なベクトル検索だけでは不十分か
   - クエリ意図の理解と戦略選択の必要性

2. **`retrieval_orchestrator_philosophy:` YAML**
   ```yaml
   retrieval_orchestrator_philosophy:
     essence: "検索 = 人間の記憶想起プロセスの模倣"
     purpose:
       - クエリの意図理解
       - 複数検索手法の統合
       - 文脈に応じた戦略選択
     principles:
       - 「人は文脈で思い出す」
       - 「記憶は多面的に想起される」
       - 「最適な想起戦略は状況による」
   ```

3. **Resonant Engineにおける位置づけ**
   - 呼吸フェーズ「吸気」での質問理解
   - 「共鳴」での適切な記憶の想起
   - 宏啓さんのASD認知特性への配慮（構造的・論理的な検索）

4. **Done Definition, Risks, Rollout Plan**

### Sprint 4: Retrieval Orchestrator 作業開始指示書

同様の構造で修正。

---

## 4. 作業指示

### 別チャットでの作業手順

1. **このドキュメントを読み込む**
2. **既存の参考資料をアップロード**
   - `memory_management_spec.md`
   - `sprint1_memory_management_start.md`
   - `sprint2_semantic_bridge_spec.md`
   - `sprint2_semantic_bridge_start.md`

3. **作成済みの4ファイルをダウンロード**
   - このチャットのoutputs/から入手可能

4. **既存ファイルの構造とトーンを深く理解する**
   - CRITICALセクションの書き方
   - Philosophy YAMLの構造
   - 呼吸サイクルとの統合説明
   - Done Definitionの階層化
   - リスク管理表
   - 情熱的で哲学的なトーン

5. **4ファイルを全面書き直し**
   - `sprint3_memory_store_spec.md`
   - `sprint3_memory_store_start.md`
   - `sprint4_retrieval_orchestrator_spec.md`
   - `sprint4_retrieval_orchestrator_start.md`

6. **各ファイルで必須チェック**
   - [ ] CRITICALセクションが存在するか
   - [ ] Philosophy YAMLが存在するか
   - [ ] Done DefinitionがTier 1/2に分かれているか
   - [ ] 呼吸サイクルとの関連が説明されているか
   - [ ] Risks & Mitigationが存在するか
   - [ ] Rollout Planが存在するか
   - [ ] トーンが既存資料と一致しているか（情熱的・哲学的）
   - [ ] Resonant Engineの思想が伝わるか

---

## 5. 技術的内容は維持

**重要**: 今回作成した技術的内容（API設計、データベース設計、実装詳細）自体は**良質**です。
問題は「様式」「トーン」「哲学的文脈」が欠けていること。

したがって：
- **技術的内容**: 80-90%はそのまま活用可能
- **構造とトーン**: 全面的に書き直し

具体的には：
- Section 3（データベース設計）、Section 4（API設計）、Section 5（実装詳細）→ ほぼそのまま
- Section 0（CRITICAL）、Section 1（哲学）、Done Definition、Risks→ 全面追加・書き直し

---

## 6. 成果物の期待

### 修正後のファイル構成

**仕様書**（各ファイル 2500-3000行想定）:
```markdown
# Sprint X: [Name] 詳細仕様書

## CRITICAL: [哲学的本質]
### Philosophy YAML
### なぜこれが必要か

## 0. Overview
### 0.1 目的
### 0.2 スコープ
### 0.3 Done Definition (Tier 1/2)

## 1. Architecture Overview
### 1.1 System Architecture
### 1.2 呼吸サイクルとの関係

## 2. Database/Data Model Design
[既存の技術内容]

## 3. API Design
[既存の技術内容]

## 4. Implementation Details
[既存の技術内容]

## 5. Test Strategy
[既存の技術内容]

## 6. Migration/Setup
[既存の技術内容]

## 7. Operations
[既存の技術内容]

## 8. Success Criteria
[Done Definitionの詳細版]

## 9. Risks & Mitigation

## 10. Rollout Plan

## 11. Future Extensions

## 12. Related Documents
```

**作業開始指示書**（各ファイル 1500-2000行想定）:
```markdown
# Sprint X: [Name] 作業開始指示書

## 0. 重要な前提条件
### 準備状態チェック
### 仕様理解

## 1. [Name] 実装承認
### 1.1 実装背景（哲学的・技術的）
### 1.2 実装スコープ

## 2. 事前準備チェックリスト

## 3. 実装スケジュール（5-7日間）
### Day 1: [タスク]
#### 午前
**タスク1**: [詳細]
**哲学的意味**: [説明]
**手順**: [コード例]
**完了基準**: [チェックリスト]

#### 午後
...

### Day 2-N: 同様の構造

## 4. Done Definition確認

## 5. トラブルシューティング

## 6. 参考資料
```

---

## 7. プロンプト例（別チャット開始時）

```
以下の4ファイルを既存の様式・精度・哲学に合わせて全面修正してください：

1. sprint3_memory_store_spec.md
2. sprint3_memory_store_start.md
3. sprint4_retrieval_orchestrator_spec.md
4. sprint4_retrieval_orchestrator_start.md

【現在の問題】
- 哲学的前提（CRITICALセクション、Philosophy YAML）が欠落
- Done DefinitionがTier分けされていない
- Risks & Mitigation、Rollout Planが存在しない
- 呼吸サイクルとの統合説明が不足
- トーンが一般的な技術仕様書（既存は情熱的・哲学的）

【参考資料】
以下をアップロードしてください：
- memory_management_spec.md（最重要）
- sprint1_memory_management_start.md（最重要）
- sprint2_semantic_bridge_spec.md
- sprint2_semantic_bridge_start.md

【作業内容】
既存資料の構造、トーン、哲学を深く理解し、Sprint 3, 4の仕様書・作業開始指示書を同じレベルで書き直してください。技術的内容は80-90%活用可能ですが、構造とトーンは全面的に修正が必要です。

【チェック項目】
各ファイルで以下を確認：
□ CRITICALセクション存在
□ Philosophy YAML存在
□ Done Definition Tier分け
□ 呼吸サイクルとの関連説明
□ Risks & Mitigation存在
□ Rollout Plan存在
□ トーン一致（情熱的・哲学的）
```

---

**引き継ぎ完了**

このドキュメントを新しいチャットに提供し、上記のプロンプトと共に作業を開始してください。
既存資料のトーンと哲学を保ちながら、Sprint 3, 4の優れた技術内容を活かした仕様書が完成するはずです。

# docs/ ディレクトリ構造移行計画

**バージョン**: 2.0.0  
**作成日**: 2025-11-14  
**実施期間**: 2025-11-16 〜 2025-11-17  
**目的**: docs/をコンポーネント別（縦割り）構造に再編成し、ドキュメントの発見性を向上

---

## 📋 目次

1. [移行方針](#移行方針)
2. [現状分析](#現状分析)
3. [新しい構造](#新しい構造)
4. [移行手順](#移行手順)
5. [ファイル移動マッピング](#ファイル移動マッピング)
6. [Phase別実施計画](#phase別実施計画)
7. [リスク管理](#リスク管理)
8. [完了条件](#完了条件)

---

## 🎯 移行方針

### 基本原則

1. **コンポーネント別縦割り構造**: 機能ごとにarchitecture/specifications/implementation/reviews/を配置
2. **段階的移行**: Phase 1で構造作成、Phase 2でファイル移動、Phase 3でREADME作成
3. **ゼロダウンタイム**: Git管理で移動履歴を保持、リンク切れを最小化
4. **検証可能**: 各Phaseで動作確認、ロールバック可能

### 設計意図

**縦割り構造のメリット**:
```
横割り（従来）:
02_architecture/bridge_lite.md
03_specifications/bridge_lite.md
04_implementation/bridge_lite.md
05_reviews/bridge_lite.md
→ 4箇所に分散 ⚠️

縦割り（新）:
02_components/bridge_lite/
  ├─ architecture/
  ├─ specifications/
  ├─ implementation/
  └─ reviews/
→ 1箇所に集約 ✅
```

**探しやすさ**:
- 「Bridge Liteについて知りたい」→ `02_components/bridge_lite/`
- 「Memory Systemについて知りたい」→ `02_components/memory_system/`

---

## 📊 現状分析

### 現在のdocs/構造（問題点）

```
docs/
├── 60+個のファイルがフラットに配置 ⚠️
├── カテゴリ分けが不十分 ⚠️
├── 命名規則がバラバラ ⚠️
├── 時系列情報が埋もれている ⚠️
└── 関連ドキュメントが分散 ⚠️

具体例:
├── bridge_lite_design_v1.1.md
├── bridge_architecture_evaluation_20251112.md
├── technical_review_response_20251112.md
├── implementation_roadmap_postgres.md
└── Yuno/review_yuno_implementation_roadmap_postgres.md
  → Bridge Lite関連だが5箇所に分散
```

### ファイル分類（カウント）

| カテゴリ | ファイル数 | 例 |
|---------|-----------|-----|
| Architecture | 8 | complete_architecture_design.md |
| Bridge Lite関連 | 12 | bridge_lite_design_v1.1.md |
| Memory System関連 | 5 | (Yuno内に散在) |
| Error Recovery | 6 | error_recovery_*.md |
| Notion Integration | 3 | notion_*.md |
| Phase記録 | 12 | Phase0/, Phase1/, Phase2/ |
| Work Logs | 2 | work_log_20251112.md |
| Yuno Documents | 15+ | Yuno/* |
| その他 | 10+ | 各種テンプレート、レポート |

**合計**: 約70-80ファイル

---

## 🏗️ 新しい構造

### 完成形（Phase 3終了後）

```
docs/
├── README.md                          # ナビゲーションハブ
│
├── 01_getting_started/                # 新規参加者向け
│   ├── README.md
│   ├── quick_start.md                 # 新規作成
│   ├── setup_guide.md                 # 新規作成
│   └── glossary.md                    # 新規作成
│
├── 02_components/                     # コンポーネント別（機能別縦割り）
│   ├── README.md
│   │
│   ├── bridge_lite/                   # Bridge Lite関連すべて
│   │   ├── README.md
│   │   ├── architecture/
│   │   │   ├── bridge_lite_design_v1.1.md
│   │   │   ├── three_layer_concept.md
│   │   │   └── bridge_architecture_evaluation.md
│   │   ├── specifications/
│   │   │   ├── bridge_lite_spec_v2.0.md
│   │   │   ├── data_bridge_spec.md
│   │   │   ├── ai_bridge_spec.md
│   │   │   └── feedback_bridge_spec.md
│   │   ├── implementation/
│   │   │   ├── bridge_lite_implementation_guide.md
│   │   │   ├── directory_migration_plan.md
│   │   │   └── bridge_lite_implementation_report.md
│   │   └── reviews/
│   │       ├── 2025-11-14_yuno_review.md
│   │       ├── 2025-11-14_kana_review.md
│   │       └── technical_review_response.md
│   │
│   ├── memory_system/
│   │   ├── README.md
│   │   ├── architecture/
│   │   │   ├── memory_architecture.md
│   │   │   ├── l0_l1_l2_design.md
│   │   │   └── resonant_four_layer_architecture.md
│   │   ├── specifications/
│   │   │   ├── memory_store_spec.md
│   │   │   ├── semantic_bridge_spec.md
│   │   │   └── retrieval_spec.md
│   │   ├── implementation/
│   │   │   ├── implementation_plan_pattern_b.md
│   │   │   ├── core_l1_prompts.md
│   │   │   └── memory_engine_correlation_analysis.md
│   │   └── reviews/
│   │       └── memory_design_review.md
│   │
│   ├── daemon/
│   │   ├── README.md
│   │   ├── architecture/
│   │   │   └── daemon_architecture.md
│   │   ├── specifications/
│   │   │   ├── observer_daemon_spec.md
│   │   │   └── resonant_daemon_spec.md
│   │   ├── implementation/
│   │   │   └── daemon_integration_guide.md
│   │   └── reviews/
│   │
│   ├── dashboard/
│   │   ├── README.md
│   │   ├── architecture/
│   │   │   └── dashboard_platform_design.md
│   │   ├── specifications/
│   │   │   └── api_spec.md
│   │   ├── implementation/
│   │   │   └── dashboard_setup_guide.md
│   │   └── reviews/
│   │
│   └── error_recovery/
│       ├── README.md
│       ├── architecture/
│       │   └── error_recovery_basic_design.md
│       ├── specifications/
│       │   ├── error_recovery_detailed_design.md
│       │   └── error_classification.md
│       ├── implementation/
│       │   ├── error_recovery_implementation.md
│       │   └── error_recovery_test_results.md
│       └── reviews/
│           ├── error_recovery_review_request.md
│           └── error_recovery_review_response.md
│
├── 06_operations/                     # 運用ドキュメント
│   ├── README.md
│   ├── deployment/
│   │   ├── docker_setup.md
│   │   ├── oracle_cloud_deployment.md
│   │   └── environment_variables.md
│   ├── monitoring/
│   │   ├── audit_log_spec.md
│   │   └── metrics_collection.md
│   ├── troubleshooting/
│   │   ├── common_issues.md
│   │   └── error_recovery_guide.md
│   └── maintenance/
│       ├── backup_strategy.md
│       └── database_maintenance.md
│
├── 07_philosophy/                     # 思想・原則（Yuno関連）
│   ├── README.md
│   ├── core_principles/
│   │   ├── resonant_regulations.md
│   │   ├── resonant_operational_regulations_full.md
│   │   ├── purpose_hierarchy.md
│   │   ├── breathing_chain_concept.md
│   │   └── resonant_conduct_principles.md
│   ├── yuno_documents/                # Yuno思想文書
│   │   ├── crisis_index_detailed.md
│   │   ├── emotion_resonance_filter_detailed.md
│   │   ├── erf_resonant_detection_quantification.md
│   │   ├── re_evaluation_phase_detailed.md
│   │   ├── resonant_daily_framework_detailed.md
│   │   ├── resonant_feedback_loop_detailed.md
│   │   ├── resonant_scope_alignment_detailed.md
│   │   ├── the_hiroaki_model_phases_detailed.md
│   │   ├── the_hiroaki_model_resonant_intelligence_extension.md
│   │   ├── yuno_claude_review_response.md
│   │   ├── yuno_response_to_claude_inquiry.md
│   │   └── yuno_self_rumination_overview.md
│   └── design_notes/
│       └── intent_bridge_design_note.md
│
├── 08_integrations/                   # 外部統合
│   ├── README.md
│   ├── notion/
│   │   ├── README.md
│   │   ├── notion_setup_guide.md
│   │   ├── notion_integration_summary.md
│   │   └── notion_integration_history.md
│   ├── github/
│   │   ├── README.md
│   │   └── github_webhook_setup.md
│   └── slack/
│       ├── README.md
│       └── slack_integration_guide.md
│
├── 09_history/                        # 歴史的記録
│   ├── README.md
│   ├── work_logs/
│   │   ├── README.md
│   │   └── 2025-11/
│   │       ├── 2025-11-12_work_log.md
│   │       └── 2025-11-14_work_log.md
│   ├── decisions/
│   │   ├── README.md
│   │   └── 2025-11-14_directory_structure_decision.md
│   ├── phases/
│   │   ├── README.md
│   │   ├── phase0/
│   │   │   ├── p0_improvement_completion_report.md
│   │   │   ├── p0_improvement_review_response.md
│   │   │   └── p0_improvement_review_result_yuno.md
│   │   ├── phase1/
│   │   │   └── p1_improvement_completion_report.md
│   │   ├── phase2/
│   │   │   ├── p2_improvement_completion_report.md
│   │   │   ├── p2_improvement_design_spec.md
│   │   │   ├── p2_improvement_implementation_guide.md
│   │   │   ├── p2_improvement_review_report.md
│   │   │   └── p2_improvement_final_review_report.md
│   │   └── phase3/
│   │       ├── phase3_basic_design.md
│   │       ├── phase3_detailed_design.md
│   │       ├── phase3_completion_report.md
│   │       ├── phase3_review_request.md
│   │       ├── phase3_review_response.md
│   │       └── phase3_work_summary.md
│   └── migrations/
│       ├── README.md
│       └── dir_restructure_commit.log
│
├── 10_templates/                      # テンプレート
│   ├── README.md
│   ├── architecture_document_template.md
│   ├── specification_template.md
│   ├── implementation_guide_template.md
│   ├── review_request_template.md
│   ├── review_response_template.md
│   ├── work_log_template.md
│   ├── decision_record_template.md
│   └── component_readme_template.md
│
├── 11_reference/                      # リファレンス
│   ├── README.md
│   ├── api_reference.md
│   ├── database_schema_reference.md
│   ├── glossary.md
│   └── abbreviations.md
│
└── archive/                           # アーカイブ
    ├── README.md
    ├── 2024/
    ├── deprecated/
    │   └── old_architecture.md
    └── kiro_v3.1/
        └── kiro_v3.1_architecture.md
```

---

## 🚀 移行手順

### 全体フロー

```
Phase 1: 構造作成（30分）
  └─ 新ディレクトリ構造を作成
  
Phase 2: ファイル移動（2-3時間）
  └─ 既存ファイルを新構造に移動
  
Phase 3: README作成（1-2時間）
  └─ 各ディレクトリにREADMEを作成
  
Phase 4: 検証・クリーンアップ（30分）
  └─ リンク確認、旧ディレクトリ削除
```

---

## 📋 ファイル移動マッピング

### Bridge Lite関連

| 現在の場所 | 移動先 |
|-----------|--------|
| `bridge_lite_design_v1.1.md` | `02_components/bridge_lite/architecture/` |
| `bridge_lite_design.md` | `02_components/bridge_lite/architecture/` (旧版) |
| `bridge_architecture_evaluation_20251112.md` | `02_components/bridge_lite/architecture/` |
| `complete_architecture_design.md` | `02_components/bridge_lite/architecture/` |
| `technical_review_response_20251112.md` | `02_components/bridge_lite/reviews/` |
| `Yuno/review_yuno_implementation_roadmap_postgres.md` | `02_components/bridge_lite/reviews/` |
| `Yuno/review_yuno_priority2_postgres_plan.md` | `02_components/bridge_lite/reviews/` |

### Memory System関連

| 現在の場所 | 移動先 |
|-----------|--------|
| `Yuno/specs/implementation_plan_pattern_b.md` | `02_components/memory_system/implementation/` |
| `Yuno/specs/resonant_engine_memory_design.md` | `02_components/memory_system/architecture/` |
| `Yuno/specs/resonant_engine_memory_design_review.md` | `02_components/memory_system/reviews/` |
| `Yuno/specs/memory_engine_correlation_analysis.md` | `02_components/memory_system/implementation/` |
| `Yuno/resonant_four_layer_architecture.md` | `02_components/memory_system/architecture/` |

### Daemon関連

| 現在の場所 | 移動先 |
|-----------|--------|
| （新規作成が必要） | `02_components/daemon/architecture/daemon_architecture.md` |
| （新規作成が必要） | `02_components/daemon/specifications/observer_daemon_spec.md` |

### Dashboard関連

| 現在の場所 | 移動先 |
|-----------|--------|
| `dashboard_platform_design.md` | `02_components/dashboard/architecture/` |

### Error Recovery関連

| 現在の場所 | 移動先 |
|-----------|--------|
| `error_recovery_basic_design.md` | `02_components/error_recovery/architecture/` |
| `error_recovery_detailed_design.md` | `02_components/error_recovery/specifications/` |
| `error_recovery_implementation.md` | `02_components/error_recovery/implementation/` |
| `error_recovery_test_results.md` | `02_components/error_recovery/implementation/` |
| `error_recovery_review_request.md` | `02_components/error_recovery/reviews/` |
| `error_recovery_review_response.md` | `02_components/error_recovery/reviews/` |

### Philosophy（Yuno関連）

| 現在の場所 | 移動先 |
|-----------|--------|
| `Yuno/resonant_operational_regulations_full.md` | `07_philosophy/core_principles/` |
| `Yuno/yuno_resonant_conduct_principles.md` | `07_philosophy/core_principles/` |
| `Yuno/crisis_index_detailed.md` | `07_philosophy/yuno_documents/` |
| `Yuno/emotion_resonance_filter_detailed.md` | `07_philosophy/yuno_documents/` |
| `Yuno/erf_resonant_detection_quantification.md` | `07_philosophy/yuno_documents/` |
| `Yuno/re_evaluation_phase_detailed.md` | `07_philosophy/yuno_documents/` |
| `Yuno/resonant_daily_framework_detailed.md` | `07_philosophy/yuno_documents/` |
| `Yuno/resonant_feedback_loop_detailed.md` | `07_philosophy/yuno_documents/` |
| `Yuno/resonant_scope_alignment_detailed.md` | `07_philosophy/yuno_documents/` |
| `Yuno/the_hiroaki_model_phases_detailed.md` | `07_philosophy/yuno_documents/` |
| `Yuno/the_hiroaki_model_resonant_intelligence_extension.md` | `07_philosophy/yuno_documents/` |
| `Yuno/yuno_claude_review_response.md` | `07_philosophy/yuno_documents/` |
| `Yuno/yuno_response_to_claude_inquiry.md` | `07_philosophy/yuno_documents/` |
| `Yuno/yuno_self_rumination_overview.md` | `07_philosophy/yuno_documents/` |
| `Yuno/intent_bridge_design_note.md` | `07_philosophy/design_notes/` |

### Integrations

| 現在の場所 | 移動先 |
|-----------|--------|
| `notion_setup_guide.md` | `08_integrations/notion/` |
| `notion_integration_summary.md` | `08_integrations/notion/` |
| `Yuno/notion_integration_history.md` | `08_integrations/notion/` |

### History

| 現在の場所 | 移動先 |
|-----------|--------|
| `work_log_20251112.md` | `09_history/work_logs/2025-11/` |
| `Phase0/*` | `09_history/phases/phase0/` |
| `Phase1/*` | `09_history/phases/phase1/` |
| `Phase2/*` | `09_history/phases/phase2/` |
| `Phase3/*` | `09_history/phases/phase3/` |
| `history/dir_restructure_commit.log` | `09_history/migrations/` |

### Templates

| 現在の場所 | 移動先 |
|-----------|--------|
| `report_template.md` | `10_templates/` |
| `templates/*` | `10_templates/` |

### Archive

| 現在の場所 | 移動先 |
|-----------|--------|
| `architecture/kiro_v3.1_architecture.md` | `archive/kiro_v3.1/` |
| （古いファイル） | `archive/deprecated/` |

---

## 📅 Phase別実施計画

### Phase 1: 構造作成（30分）

**日時**: 2025-11-16（土）10:00-10:30

**作業内容**:

```bash
#!/bin/bash
# Phase 1: ディレクトリ構造作成スクリプト

cd /Users/zero/Projects/resonant-engine/docs

# 01_getting_started
mkdir -p 01_getting_started

# 02_components
mkdir -p 02_components/bridge_lite/{architecture,specifications,implementation,reviews}
mkdir -p 02_components/memory_system/{architecture,specifications,implementation,reviews}
mkdir -p 02_components/daemon/{architecture,specifications,implementation,reviews}
mkdir -p 02_components/dashboard/{architecture,specifications,implementation,reviews}
mkdir -p 02_components/error_recovery/{architecture,specifications,implementation,reviews}

# 06_operations
mkdir -p 06_operations/{deployment,monitoring,troubleshooting,maintenance}

# 07_philosophy
mkdir -p 07_philosophy/{core_principles,yuno_documents,design_notes}

# 08_integrations
mkdir -p 08_integrations/{notion,github,slack}

# 09_history
mkdir -p 09_history/{work_logs/2025-11,decisions,phases/{phase0,phase1,phase2,phase3},migrations}

# 10_templates
mkdir -p 10_templates

# 11_reference
mkdir -p 11_reference

# archive
mkdir -p archive/{2024,deprecated,kiro_v3.1}

echo "✅ Phase 1: ディレクトリ構造作成完了"
```

**チェックポイント**:
- [ ] すべてのディレクトリが作成された
- [ ] ディレクトリ構造が設計通り
- [ ] パーミッションが適切

---

### Phase 2: ファイル移動（2-3時間）

**日時**: 2025-11-16（土）10:30-13:00

**作業内容**:

#### Step 1: Bridge Lite関連移動

```bash
# Bridge Lite - Architecture
mv bridge_lite_design_v1.1.md 02_components/bridge_lite/architecture/
mv bridge_lite_design.md 02_components/bridge_lite/architecture/bridge_lite_design_v1.0.md
mv bridge_architecture_evaluation_20251112.md 02_components/bridge_lite/architecture/
mv complete_architecture_design.md 02_components/bridge_lite/architecture/

# Bridge Lite - Reviews
mv technical_review_response_20251112.md 02_components/bridge_lite/reviews/
mv Yuno/review_yuno_implementation_roadmap_postgres.md 02_components/bridge_lite/reviews/
mv Yuno/review_yuno_priority2_postgres_plan.md 02_components/bridge_lite/reviews/

echo "✅ Bridge Lite関連ファイル移動完了"
```

#### Step 2: Memory System関連移動

```bash
# Memory System - Architecture
mv Yuno/specs/resonant_engine_memory_design.md 02_components/memory_system/architecture/
mv Yuno/resonant_four_layer_architecture.md 02_components/memory_system/architecture/

# Memory System - Implementation
mv Yuno/specs/implementation_plan_pattern_b.md 02_components/memory_system/implementation/
mv Yuno/specs/memory_engine_correlation_analysis.md 02_components/memory_system/implementation/

# Memory System - Reviews
mv Yuno/specs/resonant_engine_memory_design_review.md 02_components/memory_system/reviews/

echo "✅ Memory System関連ファイル移動完了"
```

#### Step 3: Error Recovery関連移動

```bash
# Error Recovery - Architecture
mv error_recovery_basic_design.md 02_components/error_recovery/architecture/

# Error Recovery - Specifications
mv error_recovery_detailed_design.md 02_components/error_recovery/specifications/

# Error Recovery - Implementation
mv error_recovery_implementation.md 02_components/error_recovery/implementation/
mv error_recovery_test_results.md 02_components/error_recovery/implementation/

# Error Recovery - Reviews
mv error_recovery_review_request.md 02_components/error_recovery/reviews/
mv error_recovery_review_response.md 02_components/error_recovery/reviews/

echo "✅ Error Recovery関連ファイル移動完了"
```

#### Step 4: Dashboard関連移動

```bash
# Dashboard - Architecture
mv dashboard_platform_design.md 02_components/dashboard/architecture/

echo "✅ Dashboard関連ファイル移動完了"
```

#### Step 5: Philosophy（Yuno関連）移動

```bash
# Core Principles
mv Yuno/resonant_operational_regulations_full.md 07_philosophy/core_principles/
mv Yuno/yuno_resonant_conduct_principles.md 07_philosophy/core_principles/

# Yuno Documents
mv Yuno/crisis_index_detailed.md 07_philosophy/yuno_documents/
mv Yuno/emotion_resonance_filter_detailed.md 07_philosophy/yuno_documents/
mv Yuno/erf_resonant_detection_quantification.md 07_philosophy/yuno_documents/
mv Yuno/re_evaluation_phase_detailed.md 07_philosophy/yuno_documents/
mv Yuno/resonant_daily_framework_detailed.md 07_philosophy/yuno_documents/
mv Yuno/resonant_feedback_loop_detailed.md 07_philosophy/yuno_documents/
mv Yuno/resonant_scope_alignment_detailed.md 07_philosophy/yuno_documents/
mv Yuno/the_hiroaki_model_phases_detailed.md 07_philosophy/yuno_documents/
mv Yuno/the_hiroaki_model_resonant_intelligence_extension.md 07_philosophy/yuno_documents/
mv Yuno/yuno_claude_review_response.md 07_philosophy/yuno_documents/
mv Yuno/yuno_response_to_claude_inquiry.md 07_philosophy/yuno_documents/
mv Yuno/yuno_self_rumination_overview.md 07_philosophy/yuno_documents/

# Design Notes
mv Yuno/intent_bridge_design_note.md 07_philosophy/design_notes/

echo "✅ Philosophy関連ファイル移動完了"
```

#### Step 6: Integrations移動

```bash
# Notion
mv notion_setup_guide.md 08_integrations/notion/
mv notion_integration_summary.md 08_integrations/notion/
mv Yuno/notion_integration_history.md 08_integrations/notion/

echo "✅ Integrations関連ファイル移動完了"
```

#### Step 7: History移動

```bash
# Work Logs
mv work_log_20251112.md 09_history/work_logs/2025-11/

# Phases
mv Phase0/* 09_history/phases/phase0/
mv Phase1/* 09_history/phases/phase1/
mv Phase2/* 09_history/phases/phase2/
mv Phase3/* 09_history/phases/phase3/

# Migrations
mv history/dir_restructure_commit.log 09_history/migrations/

echo "✅ History関連ファイル移動完了"
```

#### Step 8: Templates移動

```bash
mv report_template.md 10_templates/
mv templates/* 10_templates/ 2>/dev/null || true

echo "✅ Templates関連ファイル移動完了"
```

#### Step 9: Archive移動

```bash
# Kiro v3.1
mv architecture/kiro_v3.1_architecture.md archive/kiro_v3.1/

echo "✅ Archive関連ファイル移動完了"
```

**チェックポイント**:
- [ ] すべての重要ファイルが移動された
- [ ] 移動履歴がGitで記録された
- [ ] 元のファイルが残っていない（または意図的に残した）

---

### Phase 3: README作成（1-2時間）

**日時**: 2025-11-16（土）13:00-15:00

**作業内容**:

#### Step 1: ルートREADME作成

**ファイル**: `/docs/README.md`

```markdown
# Resonant Engine Documentation

Resonant Engineプロジェクトのドキュメントハブへようこそ。

## 🗺️ Quick Navigation

### 🚀 初めての方へ
→ [Getting Started](01_getting_started/)

### 🔧 コンポーネント別に探す
→ [Components](02_components/)
- [Bridge Lite](02_components/bridge_lite/) - データアクセス抽象化層
- [Memory System](02_components/memory_system/) - 記憶システム
- [Daemon](02_components/daemon/) - バックグラウンド処理
- [Dashboard](02_components/dashboard/) - Web UI
- [Error Recovery](02_components/error_recovery/) - エラー回復機構

### 💭 思想・原則を理解する
→ [Philosophy](07_philosophy/)

### ⚙️ 運用する
→ [Operations](06_operations/)

### 🔌 外部連携する
→ [Integrations](08_integrations/)

### 📚 その他
- [Templates](10_templates/) - ドキュメントテンプレート
- [Reference](11_reference/) - APIリファレンス等
- [History](09_history/) - 歴史的記録
- [Archive](archive/) - 古いドキュメント

## 📖 By Use Case

### "Bridge Liteについて知りたい"
1. [Bridge Lite Overview](02_components/bridge_lite/README.md)
2. [Architecture](02_components/bridge_lite/architecture/)
3. [Implementation](02_components/bridge_lite/implementation/)

### "システムをセットアップしたい"
1. [Setup Guide](01_getting_started/setup_guide.md)
2. [Deployment](06_operations/deployment/)

### "設計思想を理解したい"
1. [Philosophy](07_philosophy/) - Resonant Regulations等
2. [Yuno Documents](07_philosophy/yuno_documents/)

### "過去の意思決定を振り返りたい"
1. [History/Decisions](09_history/decisions/)
2. [Phase Records](09_history/phases/)

## 📋 Document Structure

各コンポーネントは以下の構造：

```
02_components/component_name/
├── README.md           # 概要・ナビゲーション
├── architecture/       # 設計文書
├── specifications/     # 詳細仕様
├── implementation/     # 実装ガイド
└── reviews/            # レビュー記録
```

## 🔍 Finding Documents

| 探したいもの | 場所 |
|-------------|------|
| 特定コンポーネント | `02_components/[component]/` |
| 運用手順 | `06_operations/` |
| 設計思想 | `07_philosophy/` |
| 外部連携方法 | `08_integrations/` |
| 過去の記録 | `09_history/` |
| テンプレート | `10_templates/` |

## 📝 Creating New Documents

1. 適切なコンポーネントを選ぶ（または新規作成）
2. [Templates](10_templates/)から適切なテンプレートを選ぶ
3. 適切なサブディレクトリに配置
   - 設計 → `architecture/`
   - 仕様 → `specifications/`
   - 実装 → `implementation/`
   - レビュー → `reviews/`
4. 関連ドキュメントにリンクを追加

## 🔄 Last Updated

2025-11-16
```

#### Step 2: 各コンポーネントREADME作成

**ファイル**: `/docs/02_components/bridge_lite/README.md`

```markdown
# Bridge Lite

Bridge LiteはResonant Engineのデータアクセス・AI API抽象化層です。

## 📁 Structure

- `architecture/` - 設計文書
- `specifications/` - 詳細仕様
- `implementation/` - 実装ガイド・計画
- `reviews/` - レビュー記録

## 📖 Reading Order

初めての方は以下の順で読むことを推奨：

1. [Architecture Overview](architecture/bridge_lite_design_v1.1.md)
2. [Specifications](specifications/bridge_lite_spec_v2.0.md)
3. [Implementation Guide](implementation/)

## 📄 Key Documents

### Architecture
- [Bridge Lite Design v1.1](architecture/bridge_lite_design_v1.1.md) - 基本設計書
- [Complete Architecture Design](architecture/complete_architecture_design.md) - 完全設計書
- [Architecture Evaluation](architecture/bridge_architecture_evaluation_20251112.md)

### Specifications
- Bridge Lite Spec v2.0（予定）
- DataBridge Spec（予定）
- AIBridge Spec（予定）
- FeedbackBridge Spec（予定）

### Implementation
- Implementation Guide（予定）
- [Migration Plan](implementation/directory_migration_plan.md)
- [Implementation Report](implementation/bridge_lite_implementation_report.md)

### Reviews
- [Yuno Review (2025-11-14)](reviews/)
- [Kana Review (2025-11-14)](reviews/)
- [Technical Review Response](reviews/technical_review_response_20251112.md)

## 🔗 Related Components

- [Memory System](../memory_system/) - Bridge Liteを使用
- [Daemon](../daemon/) - Bridge Liteを使用
- [Dashboard](../dashboard/) - Bridge Liteを使用

## 📊 Current Status

- Phase 0: ✅ 完了（2025-11-14）
- Phase 0.5: 🔄 進行中
- Phase 1: 🔲 未着手

## 🔄 Last Updated

2025-11-16
```

同様のREADMEを以下にも作成：
- `/docs/02_components/memory_system/README.md`
- `/docs/02_components/daemon/README.md`
- `/docs/02_components/dashboard/README.md`
- `/docs/02_components/error_recovery/README.md`

#### Step 3: その他ディレクトリのREADME作成

各ディレクトリに簡潔なREADMEを作成：

- `/docs/01_getting_started/README.md`
- `/docs/06_operations/README.md`
- `/docs/07_philosophy/README.md`
- `/docs/08_integrations/README.md`
- `/docs/09_history/README.md`
- `/docs/10_templates/README.md`
- `/docs/11_reference/README.md`
- `/docs/archive/README.md`

**チェックポイント**:
- [ ] ルートREADMEが作成された
- [ ] 全コンポーネントREADMEが作成された
- [ ] その他ディレクトリREADMEが作成された
- [ ] リンクが正しく設定された

---

### Phase 4: 検証・クリーンアップ（30分）

**日時**: 2025-11-16（土）15:00-15:30

**作業内容**:

#### Step 1: リンク確認

```bash
# 壊れたリンクを検索
find docs -name "*.md" -exec grep -l "]\(" {} \; | while read file; do
  echo "Checking: $file"
  # マニュアルで確認
done
```

#### Step 2: 旧ディレクトリ削除

```bash
# 空になった旧ディレクトリを削除
rmdir docs/Phase0 2>/dev/null || true
rmdir docs/Phase1 2>/dev/null || true
rmdir docs/Phase2 2>/dev/null || true
rmdir docs/Phase3 2>/dev/null || true
rmdir docs/Yuno/specs 2>/dev/null || true
rmdir docs/Yuno 2>/dev/null || true
rmdir docs/architecture 2>/dev/null || true
rmdir docs/history 2>/dev/null || true
rmdir docs/templates 2>/dev/null || true

echo "✅ 旧ディレクトリクリーンアップ完了"
```

#### Step 3: Git commit

```bash
cd /Users/zero/Projects/resonant-engine

# Gitで変更をコミット
git add docs/
git commit -m "docs: Restructure documentation with component-based organization

- Reorganize into component-based vertical structure
- Create comprehensive README navigation
- Move all files to appropriate component directories
- Add README to each directory for better discoverability

Components organized:
- bridge_lite (architecture, specs, implementation, reviews)
- memory_system (architecture, specs, implementation, reviews)
- daemon, dashboard, error_recovery

Other categories:
- operations, philosophy, integrations, history, templates, reference

Closes #[issue_number]"

echo "✅ Git commit完了"
```

**チェックポイント**:
- [ ] リンクが正しく機能する
- [ ] 旧ディレクトリが削除された
- [ ] Gitでコミットされた
- [ ] 変更履歴が保持された

---

## ⚠️ リスク管理

### 識別されたリスク

| リスク | 影響度 | 発生確率 | 対策 |
|--------|--------|----------|------|
| リンク切れ | 中 | 高 | Phase 4で確認、修正 |
| ファイル紛失 | 高 | 低 | Git履歴で追跡可能 |
| 時間超過 | 低 | 中 | Phase分割で段階的実施 |
| 既存参照の破損 | 中 | 中 | ロールバック手順準備 |

### リスク対策

1. **Git管理**: すべての変更をGitで追跡
2. **段階的実施**: Phaseごとに確認
3. **ロールバック準備**: 各Phase後にコミット
4. **バックアップ**: 移行前に全体バックアップ

---

## 🔙 ロールバック手順

### Phase 1のロールバック

```bash
# 新規ディレクトリを削除
rm -rf docs/01_getting_started
rm -rf docs/02_components
rm -rf docs/06_operations
rm -rf docs/07_philosophy
rm -rf docs/08_integrations
rm -rf docs/09_history
rm -rf docs/10_templates
rm -rf docs/11_reference
rm -rf docs/archive

# Gitで元に戻す
git checkout docs/
```

### Phase 2のロールバック

```bash
# Gitで1つ前のコミットに戻す
git reset --hard HEAD~1
```

### Phase 3のロールバック

```bash
# READMEファイルのみ削除
find docs -name "README.md" -delete

# または1つ前のコミットに戻す
git reset --hard HEAD~1
```

### Phase 4のロールバック

```bash
# 旧ディレクトリを復元
git checkout HEAD~1 -- docs/Phase0 docs/Phase1 docs/Phase2 docs/Phase3
git checkout HEAD~1 -- docs/Yuno
```

---

## ✅ 完了条件

### Phase 1完了条件

```
✅ すべてのディレクトリが作成された
✅ ディレクトリ構造が設計通り
✅ Gitでコミットされた
```

### Phase 2完了条件

```
✅ すべての重要ファイルが移動された
✅ 移動履歴がGitで記録された
✅ 元のファイルが適切に処理された（削除 or archive）
✅ ファイルの内容が変更されていない
```

### Phase 3完了条件

```
✅ ルートREADMEが作成された
✅ 全コンポーネントREADMEが作成された
✅ その他ディレクトリREADMEが作成された
✅ リンクが正しく設定された
✅ ナビゲーションが機能する
```

### Phase 4完了条件

```
✅ リンクが正しく機能する
✅ 旧ディレクトリが削除された
✅ Gitでコミットされた
✅ ドキュメントが発見しやすい
✅ 全体として構造が明確
```

### 全体完了条件

```
✅ すべてのPhaseが完了
✅ ドキュメントが発見しやすい
✅ 構造が論理的
✅ リンクがすべて機能
✅ チーム（Yuno/Kana）が承認
✅ 宏啓さんが満足
```

---

## 📊 進捗トラッキング

### チェックリスト

```
Phase 1: 構造作成
□ ディレクトリ構造作成スクリプト実行
□ 全ディレクトリ作成確認
□ Git commit

Phase 2: ファイル移動
□ Bridge Lite関連移動
□ Memory System関連移動
□ Error Recovery関連移動
□ Dashboard関連移動
□ Philosophy関連移動
□ Integrations関連移動
□ History関連移動
□ Templates関連移動
□ Archive関連移動
□ Git commit

Phase 3: README作成
□ ルートREADME作成
□ Bridge Lite README作成
□ Memory System README作成
□ Daemon README作成
□ Dashboard README作成
□ Error Recovery README作成
□ その他ディレクトリREADME作成
□ Git commit

Phase 4: 検証・クリーンアップ
□ リンク確認・修正
□ 旧ディレクトリ削除
□ 最終確認
□ Git commit
```

---

## 📝 移行後のメンテナンス

### 新しいドキュメント作成時

1. 適切なコンポーネントを選ぶ
2. 適切なサブディレクトリを選ぶ
   - 設計 → `architecture/`
   - 仕様 → `specifications/`
   - 実装 → `implementation/`
   - レビュー → `reviews/`
3. テンプレートを使用（`10_templates/`）
4. コンポーネントのREADMEを更新

### 命名規則

```
# 日付付き（時系列重要）
YYYY-MM-DD_topic_name.md
例: 2025-11-14_bridge_lite_implementation.md

# バージョン付き（バージョン管理重要）
topic_name_vX.Y.md
例: bridge_lite_spec_v2.0.md

# シンプル（最新版のみ）
topic_name.md
例: quick_start.md
```

### 定期レビュー

- **月次**: 各コンポーネントのREADME更新
- **四半期**: 全体構造の見直し
- **年次**: アーカイブの整理

---

## 🎯 期待される成果

### Before（現状）

```
docs/
├── 60+個のファイルがフラット配置 ⚠️
├── 関連ファイルが分散 ⚠️
├── 発見困難 ⚠️
└── 構造不明確 ⚠️
```

### After（移行後）

```
docs/
├── コンポーネント別に集約 ✅
├── 論理的な階層構造 ✅
├── READMEでナビゲーション ✅
├── 発見しやすい ✅
└── 予測可能な配置 ✅
```

### 具体的な改善

1. **発見性**: 「Bridge Liteについて知りたい」→ `02_components/bridge_lite/` を見るだけ
2. **保守性**: 新しいドキュメントの配置が明確
3. **理解性**: コンポーネントごとに設計→仕様→実装→レビューの流れが明確
4. **拡張性**: 新しいコンポーネント追加が容易
5. **宏啓さんの認知特性適合**: 構造的、予測可能、時系列保持

---

## 📚 参考資料

- [ディレクトリ構造議論記録](09_history/decisions/2025-11-14_directory_structure_decision.md)
- [Resonant Regulations §2: 構造的一貫性](07_philosophy/core_principles/resonant_regulations.md)

---

**移行計画終了**

**次のアクション**: Phase 1（ディレクトリ構造作成）の実施

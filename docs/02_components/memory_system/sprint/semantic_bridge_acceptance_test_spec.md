# Semantic Bridge System - 受け入れテスト仕様書

**Version**: 1.0.0
**作成日**: 2025-11-17
**作成者**: Sonnet 4.5 (Claude Code Implementation)
**目的**: ローカル環境でのSemantic Bridge実装の完全性を検証する

---

## 1. テスト概要

### 1.1 テスト対象
- SemanticExtractor（意味抽出コンポーネント）
- TypeProjectInferencer（タイプ・プロジェクト推論エンジン）
- MemoryUnitConstructor（メモリユニット構築）
- SemanticBridgeService（統合サービス）
- MemorySearchRepository（検索機能）
- REST API（5+ endpoints）

### 1.2 テスト範囲

**機能テスト**:
- イベント→メモリユニット変換
- 6種類のメモリタイプ推論
- プロジェクトID自動推論
- タグ自動生成
- CI Level・感情状態推論
- シンボリック検索（プロジェクト、タイプ、タグ、日付範囲など）

**品質テスト**:
- 推論精度 ≥80%
- 処理性能 <50ms/event
- 検索性能 <100ms

---

## 2. テスト実行環境

### 2.1 前提条件

```bash
# Python環境
python --version  # 3.11+

# 必要パッケージ
pip list | grep -E "(pydantic|pytest-asyncio)"
# pydantic 2.x
# pytest-asyncio

# プロジェクトルート
cd /home/user/resonant-engine
```

### 2.2 テスト実行コマンド

```bash
# 全テスト実行
python -m pytest tests/semantic_bridge/ -v

# 特定コンポーネントテスト
python -m pytest tests/semantic_bridge/test_models.py -v
python -m pytest tests/semantic_bridge/test_extractor.py -v
python -m pytest tests/semantic_bridge/test_inferencer.py -v
python -m pytest tests/semantic_bridge/test_constructor.py -v
python -m pytest tests/semantic_bridge/test_service.py -v
python -m pytest tests/semantic_bridge/test_search.py -v

# 手動統合テスト
python tests/semantic_bridge/test_manual_integration.py
```

---

## 3. 受け入れ基準チェックリスト

### 3.1 Tier 1: 必須要件（10項目）

| No | 要件 | 期待結果 | 検証方法 | 合否 |
|----|------|---------|---------|------|
| 1 | SemanticBridgeクラス実装 | サービスが正常動作する | `test_service.py` 全テストPASS | □ |
| 2 | イベント→メモリユニット変換 | EventContextがMemoryUnitに変換される | `test_process_event_full_pipeline` PASS | □ |
| 3 | メモリタイプ自動推論（6種類） | 全タイプが正しく推論される | `test_inferencer.py` 全タイプテストPASS | □ |
| 4 | プロジェクトID推論 | キーワードからプロジェクトが特定される | `test_infer_project_*` PASS | □ |
| 5 | メタデータ抽出 | tags, ci_level, emotion_stateが抽出される | `test_extract_metadata` PASS | □ |
| 6 | memory_itemへの保存 | メモリユニットがリポジトリに保存される | `test_process_event_saves_to_repository` PASS | □ |
| 7 | シンボリック検索API（5+ endpoints） | 全エンドポイントが実装されている | API定義確認 | □ |
| 8 | 既存パイプライン統合準備 | サービスが独立動作可能 | 手動統合テストPASS | □ |
| 9 | テストカバレッジ 30+ ケース | 97テストケースが存在する | pytest実行結果確認 | □ |
| 10 | API仕様ドキュメント | ドキュメントが完成している | docs/確認 | □ |

### 3.2 Tier 2: 品質要件（6項目）

| No | 要件 | 期待結果 | 検証方法 | 合否 |
|----|------|---------|---------|------|
| 1 | 推論精度テスト（80%以上） | 推論精度が80%を超える | テストケース確認 | □ |
| 2 | パフォーマンステスト（<50ms/event） | 処理時間が50ms未満 | 処理時間ログ確認 | □ |
| 3 | エッジケース処理 | 空文字、長文、特殊文字が処理される | バリデーションテストPASS | □ |
| 4 | ログ・監視機能 | 変換ログが出力される | `_log_conversion` 実装確認 | □ |
| 5 | エラーハンドリング | 不正入力でエラーが発生する | バリデーションエラーテストPASS | □ |
| 6 | Kana仕様レビュー | 仕様書に準拠している | 仕様書との比較確認 | □ |

---

## 4. 詳細テストケース

### 4.1 メモリタイプ推論テスト

| No | テスト名 | 入力Intent文 | 期待タイプ |
|----|---------|--------------|-----------|
| 1 | 規範タイプ | 「新しい規範を定義する」 | `resonant_regulation` |
| 2 | マイルストーンタイプ | 「マイルストーンを達成した」 | `project_milestone` |
| 3 | 設計ノートタイプ | 「システムアーキテクチャの設計」 | `design_note` |
| 4 | 日次振り返りタイプ | 「今日の振り返りを行う」 | `daily_reflection` |
| 5 | 危機ログタイプ（CI Level高） | 任意テキスト + CI Level 70+ | `crisis_log` |
| 6 | セッションサマリータイプ | 「作業セッションを開始」 | `session_summary` |

### 4.2 プロジェクト推論テスト

| No | テスト名 | 入力Intent文 | 期待プロジェクト |
|----|---------|--------------|-----------------|
| 1 | Resonant Engine | 「Resonant Engineのブリッジ機能」 | `resonant_engine` |
| 2 | PostgreSQL実装 | 「PostgreSQLのスキーマをマイグレーション」 | `postgres_implementation` |
| 3 | メモリシステム | 「メモリの記憶システムを実装」 | `memory_system` |
| 4 | メタデータ指定 | メタデータにproject_id指定 | 指定されたID |

### 4.3 感情状態推論テスト

| No | CI Level範囲 | 期待感情状態 |
|----|-------------|-------------|
| 1 | 0-9 | `neutral` |
| 2 | 10-29 | `calm` |
| 3 | 30-49 | `focused` |
| 4 | 50-69 | `stressed` |
| 5 | 70-100 | `crisis` |

### 4.4 検索機能テスト

| No | テスト名 | 検索条件 | 期待結果 |
|----|---------|---------|---------|
| 1 | プロジェクト検索 | `project_id="resonant_engine"` | 該当プロジェクトのみ |
| 2 | タイプ検索 | `type=DESIGN_NOTE` | 設計ノートのみ |
| 3 | タグ検索（any） | `tags=["tag1", "tag2"], tag_mode="any"` | いずれかのタグを含む |
| 4 | タグ検索（all） | `tags=["tag1", "tag2"], tag_mode="all"` | 両方のタグを含む |
| 5 | CI Level範囲 | `ci_level_min=30, ci_level_max=50` | 範囲内のCI Level |
| 6 | テキスト検索 | `text_query="PostgreSQL"` | タイトルまたはコンテンツに含む |
| 7 | ページネーション | `limit=2, offset=2` | 2件スキップして2件取得 |
| 8 | ソート | `sort_by="ci_level", sort_order="desc"` | CI Level降順 |

---

## 5. 手動統合テスト手順

### 5.1 完全パイプラインテスト

```bash
python tests/semantic_bridge/test_manual_integration.py
```

**期待される出力**:
1. ✅ メモリユニット作成（6種類全て）
2. ✅ プロジェクト推論成功
3. ✅ タグ自動生成成功
4. ✅ 感情状態推論成功
5. ✅ 検索機能動作確認
6. ✅ メタデータ保存確認

### 5.2 単体テスト実行

```bash
python -m pytest tests/semantic_bridge/ -v --tb=short
```

**期待される結果**:
- collected 97 items
- 97 passed
- テスト時間 < 1秒

---

## 6. 成果物チェックリスト

### 6.1 コードファイル

| ファイル | 場所 | 行数目安 | 確認 |
|---------|------|---------|------|
| `__init__.py` | `bridge/semantic_bridge/` | 20+ | □ |
| `models.py` | `bridge/semantic_bridge/` | 200+ | □ |
| `extractor.py` | `bridge/semantic_bridge/` | 120+ | □ |
| `inferencer.py` | `bridge/semantic_bridge/` | 250+ | □ |
| `constructor.py` | `bridge/semantic_bridge/` | 150+ | □ |
| `service.py` | `bridge/semantic_bridge/` | 180+ | □ |
| `repositories.py` | `bridge/semantic_bridge/` | 300+ | □ |
| `api_schemas.py` | `bridge/semantic_bridge/` | 100+ | □ |
| `api_router.py` | `bridge/semantic_bridge/` | 200+ | □ |

### 6.2 テストファイル

| ファイル | テスト数 | 確認 |
|---------|---------|------|
| `test_models.py` | 25+ | □ |
| `test_extractor.py` | 14+ | □ |
| `test_inferencer.py` | 16+ | □ |
| `test_constructor.py` | 10+ | □ |
| `test_service.py` | 14+ | □ |
| `test_search.py` | 20+ | □ |

### 6.3 ドキュメント

| ドキュメント | 場所 | 確認 |
|-------------|------|------|
| 受け入れテスト仕様書 | `docs/.../sprint/` | □ |
| 手動統合テスト | `tests/semantic_bridge/` | □ |

---

## 7. 推論精度検証

### 7.1 メモリタイプ推論精度

テストカバレッジ内で以下が検証されている：
- 規範キーワード検出: PASS
- マイルストーンキーワード検出: PASS
- 設計キーワード検出: PASS
- 日次振り返りキーワード検出: PASS
- 危機ログ（CI Level基準）: PASS
- 危機ログ（キーワード基準）: PASS

**推論精度**: 6/6 = 100%（テストケース内）

### 7.2 プロジェクト推論精度

- resonant_engine: PASS
- postgres_implementation: PASS
- memory_system: PASS
- メタデータ指定: PASS

**推論精度**: 4/4 = 100%（テストケース内）

---

## 8. トラブルシューティング

### 8.1 よくある問題

**問題1**: インポートエラー
```bash
# 解決策
export PYTHONPATH=/home/user/resonant-engine:$PYTHONPATH
```

**問題2**: Pydantic警告
```
PydanticDeprecatedSince20: Support for class-based `config` is deprecated
```
- 注意: 機能には影響なし、将来的にConfigDictへ移行予定

**問題3**: テスト失敗
```bash
# デバッグ
python -m pytest tests/semantic_bridge/ -v --tb=long
```

---

## 9. 最終チェック

### 9.1 全テスト実行

```bash
python -m pytest tests/semantic_bridge/ --tb=no 2>&1 | tail -5
# 期待: 97 passed
```

### 9.2 コードカウント

```bash
find bridge/semantic_bridge -name "*.py" -exec wc -l {} + | tail -1
# 期待: 1500+ lines total
```

### 9.3 テストカウント

```bash
python -m pytest tests/semantic_bridge/ --collect-only 2>&1 | grep "tests collected"
# 期待: 97+ tests collected
```

---

## 10. 承認

### 10.1 Done Definition達成

**Tier 1**: □ 10/10 達成
**Tier 2**: □ 6/6 達成

### 10.2 品質基準

- [ ] 全97テストPASS
- [ ] 推論精度 ≥80%
- [ ] 処理性能 <50ms/event
- [ ] ドキュメント完成

### 10.3 次のステップ

- [ ] Sprint 3 (Memory Store) への準備
- [ ] ベクトル検索の設計検討
- [ ] 既存パイプラインへの統合

---

**作成日**: 2025-11-17
**作成者**: Sonnet 4.5 (Claude Code Implementation)
**レビュー待ち**: 宏啓（プロジェクトオーナー）

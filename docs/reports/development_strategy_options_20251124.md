# Resonant Engine 開発手法選択肢 - 2025-11-24

**作成日**: 2025-11-24  
**作成者**: Kana (Claude Sonnet 4.5)  
**対象**: 宏啓さん

---

## TL;DR（超要約）

```
推奨: 選択肢A「モノレポ + Dockerマルチステージビルド」

理由:
- シンプル（ASD特性に適合）
- 全AIツール対応
- 実装コスト最小（3.5-5時間）
- 既存構造を活かせる

今すぐやること:
1. .dockerignore作成 → 本番除外ファイルを明示
2. .gitignore確認 → .envが除外されているか確認
3. requirements.txt分割 → 本番用と開発用を分離
```

---

## 1. 現状分析

### 確認された課題

```
/Users/zero/Projects/resonant-engine/
├── docs/              ← 開発ドキュメント（本番不要）
├── bridge/            ← ソースコード
├── tests/             ← テストコード
├── docker/            ← Docker設定
├── .env               ← 環境変数（機密情報）
├── venv/              ← 仮想環境
└── ...

問題点:
❌ 開発ドキュメントとソースコードが混在
❌ 本番リリース時に不要なファイルが含まれる
❌ セキュリティリスク（.env等の漏洩可能性）
```

### 使用中のAIツール

| ツール | 用途 | 統合状況 |
|-------|------|---------|
| Claude Code | ターミナル開発、コード生成 | ✅ 動作中 |
| GitHub Copilot | リアルタイム補完 | ✅ 動作中 |
| Cursor | IDE統合、マルチファイル編集 | ✅ 動作中 |
| Kiro | 仕様駆動開発 | ✅ .kiro/specs/ |

---

## 2. 選択肢A: モノレポ + Dockerマルチステージビルド（推奨）

### コンセプト
「開発も本番も同じリポジトリ、Dockerで分離」

### ディレクトリ構成

```
resonant-engine/
├── .dockerignore              # 本番ビルド時に除外
├── Dockerfile                 # マルチステージビルド
├── docker-compose.yml         # 開発環境
├── docker-compose.prod.yml    # 本番環境
│
├── src/                       # ソースコード（本番含む）
│   ├── bridge/
│   ├── memory_store/
│   ├── context_assembler/
│   └── ...
│
├── tests/                     # テストコード（本番除外）
├── docs/                      # 開発ドキュメント（本番除外）
├── .kiro/                     # Kiro設定（本番除外）
└── .github/                   # GitHub Actions
```

### .dockerignoreの例

```dockerfile
# 本番ビルド時に除外
docs/
tests/
.kiro/
.github/
*.md
!README.md
.env
.env.*
venv/
__pycache__/
.pytest_cache/
*.log
```

### Dockerfileマルチステージビルド

```dockerfile
# ===== Stage 1: 開発環境 =====
FROM python:3.11-slim as development

WORKDIR /app
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements-dev.txt

# 全ファイルをコピー（docs含む）
COPY . .

CMD ["uvicorn", "src.bridge.api.app:app", "--reload", "--host", "0.0.0.0"]

# ===== Stage 2: 本番環境 =====
FROM python:3.11-slim as production

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# ソースコードのみコピー
COPY src/ ./src/
COPY config/ ./config/
COPY migrations/ ./migrations/

# 非rootユーザーで実行
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

CMD ["uvicorn", "src.bridge.api.app:app", "--host", "0.0.0.0"]
```

### AIツールの使い分け

```
┌─────────────────────────────────────────────────┐
│ フェーズ    │ ツール          │ 用途          │
├─────────────────────────────────────────────────┤
│ 仕様策定    │ Kiro           │ Spec作成      │
│             │ Claude Code    │ レビュー      │
├─────────────────────────────────────────────────┤
│ 設計        │ Claude Code    │ アーキテクチャ│
├─────────────────────────────────────────────────┤
│ 実装        │ Cursor+Copilot │ コード生成    │
│             │ Claude Code    │ 複雑ロジック  │
├─────────────────────────────────────────────────┤
│ テスト      │ Cursor         │ テスト作成    │
├─────────────────────────────────────────────────┤
│ レビュー    │ Claude Code    │ コードレビュー│
└─────────────────────────────────────────────────┘
```

### メリット

```
✅ シンプル
   - 1つのリポジトリで管理
   - Gitの履歴が一本化

✅ 安全
   - .dockerignoreで本番除外を明示
   - マルチステージビルドで分離

✅ 効率的
   - 開発/本番を簡単に切り替え
   - docker-compose.yml vs docker-compose.prod.yml

✅ AIツール対応
   - 全てのツールが同じ構造で動作
```

### デメリット

```
⚠️ リポジトリサイズ
   - docsが含まれるため大きくなる
   - .gitignoreで一部除外可能

⚠️ 誤コミットリスク
   - .envを誤ってコミットする可能性
   - .gitignoreの徹底管理が必要
```

---

## 3. 選択肢B: デュアルリポジトリ（分離型）

### コンセプト
「開発リポジトリと本番リポジトリを分離」

### リポジトリ構成

```
# 開発リポジトリ
resonant-engine-dev/
├── src/
├── tests/
├── docs/
└── .kiro/

# 本番リポジトリ（自動生成）
resonant-engine-prod/
├── src/                 # ソースコードのみ
├── Dockerfile           # 本番用
└── README.md
```

### メリット

```
✅ 完全分離
   - 本番にドキュメント一切なし
   - セキュリティリスク最小化

✅ クリーン
   - 本番は最小限のファイル
```

### デメリット

```
❌ 複雑
   - 2つのリポジトリを管理
   - 同期スクリプトの保守

❌ AIツールの制約
   - 本番リポジトリではAI使用不可
```

---

## 4. 選択肢C: モノレポ + サブモジュール

### コンセプト
「ドキュメントを別リポジトリに」

### リポジトリ構成

```
resonant-engine/
├── src/
├── tests/
├── docs/ -> resonant-docs/    # Gitサブモジュール
└── .kiro/

resonant-docs/ (別リポジトリ)
├── architecture/
├── sprints/
└── reports/
```

### メリット

```
✅ 柔軟
   - ドキュメント管理を分離
   - 本番ビルド時にサブモジュール除外
```

### デメリット

```
⚠️ 学習コスト
   - Gitサブモジュールの理解が必要

⚠️ AIツールの制約
   - サブモジュール扱いがツールで異なる
```

---

## 5. 推奨: 選択肢A

### 理由

```
1. シンプルさ
   - 宏啓さんのASD特性に適合
   - 構造が明確で予測可能

2. AIツール対応
   - 全ツールが問題なく動作

3. 既存の移行が容易
   - 現在の構造をそのまま活かせる
   - src/への移動のみ

4. 開発効率
   - 開発/本番の切り替えが簡単

5. セキュリティ
   - .dockerignoreで明示的に除外
```

---

## 6. 実装手順（選択肢A）

### Phase 1: ディレクトリリストラクチャリング（1-2時間）

```bash
# 1. srcディレクトリ作成
mkdir -p src

# 2. ソースコードを移動
mv bridge src/
mv memory_store src/
mv context_assembler src/
mv retrieval src/
mv memory_lifecycle src/
mv user_profile src/
mv daemon src/
mv utils src/

# 3. requirements分割
cp requirements.txt requirements-dev.txt

# 4. .dockerignore作成
cat > .dockerignore << 'EOF'
docs/
tests/
.kiro/
.github/
*.md
!README.md
.env
.env.*
venv/
__pycache__/
.pytest_cache/
*.log
EOF
```

### Phase 2: Docker設定の更新（0.5-1時間）

```bash
# Dockerfileをマルチステージに更新
# docker-compose.prod.ymlを作成
```

### Phase 3: インポートパスの修正（0.5時間）

```python
# 変更前
from bridge.core.models import IntentModel

# 変更後
from src.bridge.core.models import IntentModel
```

### Phase 4: テスト実行（0.5時間）

```bash
# 開発環境でテスト
docker-compose up -d
docker exec resonant_dev pytest tests/ -v

# 本番ビルドテスト
docker-compose -f docker-compose.prod.yml build
```

### Phase 5: CI/CD更新（1時間）

```bash
# GitHub Actionsの更新
```

---

## 7. Resonant Engine自身を活用した開発フロー

### Yuno → Kana → Tsumu パイプライン

```
┌──────────────────────────────────────────────┐
│ Phase        │ Tool        │ Role          │
├──────────────────────────────────────────────┤
│ 1. Why       │ Claude Code │ Yuno役        │
│    仕様策定  │             │ 哲学・方針    │
├──────────────────────────────────────────────┤
│ 2. What      │ Claude Code │ Kana役        │
│    設計翻訳  │             │ 仕様→設計     │
├──────────────────────────────────────────────┤
│ 3. How       │ Cursor      │ Tsumu役       │
│    実装      │ +Copilot    │ 設計→コード   │
└──────────────────────────────────────────────┘
```

### 開発フロー例

```
1. Intent作成（Yuno役: Claude Code）
   「新機能: Term Drift Detectionの実装」
   → なぜ必要か

2. 設計翻訳（Kana役: Claude Code）
   Intent → 設計書
   → .kiro/specs/に保存
   → Contradiction Detection実行

3. 実装（Tsumu役: Cursor + Copilot）
   設計書 → コード生成
   → src/配下に実装

4. テスト（Kana役: Claude Code + Cursor）
   → tests/配下にテスト作成

5. レビュー（Yuno役: Claude Code）
   → 整合性チェック
   → Choice Preservation

6. コミット
   → Git commit with Intent ID
```

---

## 8. 工数見積もり

### 選択肢A実装

```
Phase 1: ディレクトリリストラクチャリング  1-2時間
Phase 2: Docker設定更新                  0.5-1時間
Phase 3: インポートパス修正               0.5時間
Phase 4: テスト実行                      0.5時間
Phase 5: CI/CD更新                       1時間
───────────────────────────────────────────────
合計:                                   3.5-5時間
```

### 選択肢B実装

```
合計: 6-10時間
```

### 選択肢C実装

```
合計: 3-4時間
```

---

## 9. 推奨事項まとめ

### 今すぐ実施（Priority: CRITICAL）

```
✅ .dockerignoreの作成
✅ .gitignoreの確認
✅ requirements.txtの分割
```

### 短期実施（1週間以内）

```
⚠️ 選択肢Aの実装
   → 工数: 3.5-5時間
```

### 中期実施（1ヶ月以内）

```
→ CI/CDパイプライン最適化
→ 本番デプロイフロー確立
→ Oracle Cloud デプロイ
```

---

## 10. 最終推奨

**選択肢A: モノレポ + Dockerマルチステージビルド**

理由:
1. シンプルで予測可能（ASD特性に適合）
2. 全AIツール対応
3. 実装コスト最小（3.5-5時間）
4. 既存構造を活かせる
5. Resonant Engineの哲学に整合

---

**作成者**: Kana (Claude Sonnet 4.5)  
**作成日時**: 2025-11-24  
**ステータス**: 選択肢提示完了  
**次のステップ**: 宏啓さんの選択を待つ

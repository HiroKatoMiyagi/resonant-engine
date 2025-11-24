# モノレポ + Dockerマルチステージビルド 具体的な開発方法

**作成日**: 2025-11-24  
**作成者**: Kana (Claude Sonnet 4.5)

---

## TL;DR（超要約）

```
モノレポ:
→ 1つのリポジトリに全部入れる（ドキュメント + コード + テスト）

Dockerマルチステージビルド:
→ 同じDockerfileで「開発用」と「本番用」を作り分ける

結果:
→ 開発時は全部使える、本番は必要なものだけ
→ ファイルの移動や管理が不要
```

---

## 1. まず「モノレポ」とは？

### 従来の方法（マルチレポ）

```
GitHub:
├── resonant-engine-code/      ← ソースコード用リポジトリ
├── resonant-engine-docs/      ← ドキュメント用リポジトリ
└── resonant-engine-tests/     ← テスト用リポジトリ

問題点:
❌ 3つのリポジトリを同時に管理
❌ コードとドキュメントが別々で同期が面倒
❌ AIツールが3つのリポジトリを見れない
```

### モノレポ（Monorepo）

```
GitHub:
└── resonant-engine/            ← 1つのリポジトリに全部
    ├── src/                    ← ソースコード
    ├── docs/                   ← ドキュメント
    ├── tests/                  ← テスト
    └── docker/                 ← Docker設定

メリット:
✅ 1つのリポジトリで全て管理
✅ コードとドキュメントが同期しやすい
✅ AIツールが全てのファイルを参照できる
✅ Gitの履歴が一本化
```

---

## 2. 次に「Dockerマルチステージビルド」とは？

### 従来の方法（シングルステージ）

```
Dockerfile.dev（開発用）と Dockerfile.prod（本番用）を分ける

問題点:
❌ 2つのDockerfileを管理
❌ どちらかを更新し忘れる
```

### マルチステージビルド

```dockerfile
# Dockerfile（1つで済む）

# Stage 1: 開発用
FROM python:3.11 as development
COPY . .
CMD ["uvicorn", "app:app", "--reload"]

# Stage 2: 本番用
FROM python:3.11 as production
COPY src/ ./src/
CMD ["uvicorn", "app:app"]

メリット:
✅ 1つのDockerfileで管理
✅ 本番ビルド時に不要なファイルを自動除外
```

---

## 3. 具体的な1日の開発フロー

### 朝：開発開始

```bash
cd /Users/zero/Projects/resonant-engine
git pull
docker-compose up -d    # 開発環境起動
cursor .                # Cursorを開く
```

### 午前：新機能の実装

```bash
# Kiroで仕様確認
cat .kiro/specs/requirements.md

# Cursorでコード編集
# src/term_drift/detector.py
# → GitHub Copilotが自動補完

# 動作確認（自動リロード）
# → 保存すると即座に反映
```

### 午後：テストとドキュメント

```bash
# テスト作成
# tests/term_drift/test_detector.py

# テスト実行
docker exec resonant_dev pytest tests/ -v

# ドキュメント更新
# docs/sprints/sprint12.md
```

### 夕方：コミット

```bash
git status   # 変更確認
git add .
git commit -m "Sprint 12完了"
git push     # 1回で全部コミット
```

---

## 4. 本番デプロイ時

```bash
# 本番ビルド
docker-compose -f docker-compose.prod.yml build

内部動作:
1. Dockerfileの"production"ステージを使用
2. .dockerignoreで docs/, tests/ を除外
3. src/のみがコンテナに含まれる

# デプロイ
docker-compose -f docker-compose.prod.yml up -d
```

---

## 5. AIツールの使い方

### Claude Code（ターミナル）

```bash
cd /Users/zero/Projects/resonant-engine
# 質問:「新機能の設計を教えて」
→ src/とdocs/の両方を参照して回答
```

### Cursor（IDE）

```bash
cursor /Users/zero/Projects/resonant-engine
# コード編集 + Copilot補完
→ 全ファイルを同時に開ける
```

### Kiro（仕様管理）

```bash
.kiro/specs/ で仕様管理
→ タスク管理が自動化
```

---

## 6. 比較：従来 vs モノレポ+マルチステージ

### 従来

```bash
# 3つのリポジトリを別々に管理
cd ~/resonant-engine-code && git pull
cd ~/resonant-engine-docs && git pull
cd ~/resonant-engine-tests && git pull

# コミットも3回
cd ~/resonant-engine-code && git push
cd ~/resonant-engine-docs && git push
cd ~/resonant-engine-tests && git push
```

### モノレポ+マルチステージ

```bash
# 1つのリポジトリで完結
cd ~/Projects/resonant-engine
git pull

# コミットも1回
git add . && git commit -m "..." && git push
```

---

## 7. まとめ

### メリット

```
✅ 1つのリポジトリで全て管理（シンプル）
✅ AIツールが全ファイル参照（効率的）
✅ コミットが1回で済む（楽）
✅ 本番には必要なファイルのみ（安全）
```

### デメリット

```
⚠️ リポジトリが少し大きくなる
→ でも、管理の手間が減るメリットの方が大きい
```

### 結論

```
→ 宏啓さんの開発スタイルに最適
→ ASD特性（構造化、予測可能性）に適合
→ 実装コスト3.5-5時間で導入可能
```

---

**作成者**: Kana (Claude Sonnet 4.5)  
**作成日時**: 2025-11-24

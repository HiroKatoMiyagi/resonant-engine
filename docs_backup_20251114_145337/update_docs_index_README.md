# update_docs_index.py - ドキュメントインデックス自動更新ツール

## 📝 概要

`update_docs_index.py`は、Resonant Engineの`/docs`ディレクトリ配下のすべてのドキュメントを自動的にスキャンし、カテゴリー別に整理された`index.html`を生成するPythonスクリプトです。

## ✨ 主な機能

### 1. 自動ディレクトリスキャン
- `/docs`配下のすべてのMarkdown、HTML、PDF、その他のドキュメントファイルを自動検出
- 除外パターン（`.DS_Store`, `__pycache__`, `.git`など）を自動的にスキップ
- 空のディレクトリ（`canvas`, `design`, `specs`, `templates`）は無視

### 2. インテリジェントなカテゴリー分類
以下のカテゴリーに自動分類:

- **📐 アーキテクチャ概要**: システム設計関連ドキュメント
- **🚀 フェーズ別実装**: Phase 0-3の実装ドキュメント
- **🗺️ 実装ロードマップ**: PostgreSQL移行やクラウド戦略
- **🧠 Yuno思想・設計文書**: Yunoによる哲学的・設計文書
- **🔧 エラーリカバリー**: エラー処理関連ドキュメント
- **🔗 統合・セットアップ**: システム統合とセットアップガイド
- **📊 成果物・アウトプット**: 生成された成果物
- **🛠️ テンプレート・ユーティリティ**: テンプレートとツール
- **📝 その他**: その他のドキュメント

### 3. 複数フォーマット対応
同じベース名で異なる拡張子のファイルを自動的にグループ化:
- 例: `document.md`, `document.html`, `document.pdf` → 1つのエントリーに統合して表示

### 4. バッジ自動付与
ファイル名から自動的にバッジを判定:

| バッジ | 条件 | 色 |
|--------|------|-----|
| 完了 | `completion`, `complete`を含む | 緑 |
| ガイド | `guide`を含む | 青 |
| 設計 | `design`, `spec`を含む | オレンジ |
| 実装 | `implementation`を含む | 青 |
| テスト | `test`を含む | 紫 |
| レビュー | `review`を含む | ティール |

### 5. 説明文の自動生成
主要なドキュメントには説明文を自動的に付与:
- `complete_architecture_design.md` → "システム全体のアーキテクチャ設計書"
- `implementation_roadmap_postgres.md` → "PostgreSQL移行の実装ロードマップ（Yuno承認済み A+評価）"
- など

### 6. 更新日時の自動記録
スクリプト実行日時を自動的に`index.html`に記録

## 🚀 使い方

### 基本的な使用方法

```bash
# ドキュメントディレクトリに移動
cd /Users/zero/Projects/resonant-engine/docs

# スクリプトを実行
python update_docs_index.py

# 生成されたindex.htmlをブラウザで開く
open index.html
```

### 実行結果の例

```
📁 ドキュメントディレクトリ: /Users/zero/Projects/resonant-engine/docs
🔍 ドキュメントをスキャン中...
✅ 67 件のドキュメントを検出
  - phase_phase0: 5 件
  - phase_phase1: 1 件
  - phase_phase2: 5 件
  - phase_phase3: 6 件
  - yuno: 18 件
  - architecture: 3 件
  - error_recovery: 6 件
  - integration: 6 件
  - roadmap: 2 件
  - output: 9 件
  - utilities: 5 件
  - misc: 4 件

🔨 index.htmlを生成中...
✨ 完了！ /Users/zero/Projects/resonant-engine/docs/index.html

ブラウザで開く:
  open /Users/zero/Projects/resonant-engine/docs/index.html
```

## 🔄 運用フロー

### 新しいドキュメントを追加する場合

1. **ドキュメントファイルを配置**
   ```bash
   # 例: Phase 4のドキュメントを追加
   /docs/Phase4/phase4_basic_design.md
   ```

2. **スクリプトを実行**
   ```bash
   cd /Users/zero/Projects/resonant-engine/docs
   python update_docs_index.py
   ```

3. **自動的にindex.htmlが更新される**
   - Phase 4セクションが自動的に作成される
   - ファイル名から適切なバッジが付与される
   - カテゴリー別に自動分類される

### カスタムの説明文を追加する場合

スクリプトの`_get_description()`メソッドを編集:

```python
def _get_description(self, filename: str) -> str:
    """ファイル名から説明文を生成"""
    descriptions = {
        'complete_architecture_design': 'システム全体のアーキテクチャ設計書',
        'your_new_document': 'あなたの新しいドキュメントの説明',  # 追加
        # ...
    }
    return descriptions.get(filename, '')
```

## 🎨 生成されるHTMLの特徴

### レスポンシブデザイン
- モダンなグラデーション背景（紫系）
- カード型レイアウトでドキュメントを表示
- ホバーエフェクトで視覚的フィードバック
- モバイルデバイスにも対応

### ナビゲーション
- セクションごとに色分け
- 複数フォーマットのファイルは並べて表示
- クリック可能なリンクで直接ドキュメントにアクセス

### カラースキーム
- ヘッダー: 紫のグラデーション
- セクションタイトル: 紫
- サブセクション: 薄紫
- カード: ライトグレー背景
- バッジ: 各種カラー（完了=緑、設計=オレンジなど）

## 🔧 カスタマイズポイント

### 1. 除外パターンの変更

```python
self.exclude_patterns = {
    '.DS_Store', '__pycache__', '.git', '.pyc',
    'update_docs_index.py', 'index.html',
    'your_custom_exclude'  # 追加
}
```

### 2. 新しいカテゴリーの追加

`scan()`メソッドに新しいカテゴリーのスキャンロジックを追加:

```python
# 新しいカテゴリー
new_category_docs = self._scan_new_category()
if new_category_docs:
    documents['new_category'] = new_category_docs
```

### 3. バッジ判定ロジックの変更

`_determine_badge()`メソッドを編集:

```python
def _determine_badge(self, filename: str) -> str:
    filename_lower = filename.lower()
    
    if 'your_keyword' in filename_lower:
        return 'カスタムバッジ'
    # ...
```

### 4. HTMLデザインの変更

`HTMLGenerator`クラスの`_get_html_header()`内のCSSを編集することで、デザインをカスタマイズ可能

## 📋 技術仕様

### 依存関係
- Python 3.6以上
- 標準ライブラリのみ使用（追加インストール不要）

### 使用している標準ライブラリ
- `os`: ファイルシステム操作
- `re`: 正規表現パターンマッチング
- `datetime`: 日時処理
- `pathlib`: パス操作
- `typing`: 型ヒント
- `collections`: defaultdict

### ファイル構造

```
docs/
├── index.html                      # 生成されるドキュメントポータル
├── update_docs_index.py            # このスクリプト
├── update_docs_index_README.md     # このREADME
├── Phase0/                         # Phase別ドキュメント
├── Phase1/
├── Phase2/
├── Phase3/
├── Yuno/                           # Yuno思想文書
├── architecture/                   # アーキテクチャ文書
├── output/                         # 成果物
└── ...
```

## 🐛 トラブルシューティング

### スクリプトが実行できない

**問題**: `python: command not found`

**解決策**: Python 3がインストールされているか確認
```bash
python3 update_docs_index.py
```

### ドキュメントが検出されない

**問題**: 新しいドキュメントが`index.html`に表示されない

**解決策**:
1. ファイルが除外パターンに該当していないか確認
2. ファイルが空のディレクトリに配置されていないか確認
3. スクリプトの`scan()`メソッドに該当するスキャンロジックがあるか確認

### 特定のカテゴリーが表示されない

**問題**: 特定のカテゴリーセクションが`index.html`に表示されない

**解決策**:
1. 該当するドキュメントが実際に存在するか確認
2. `_generate_content()`メソッドでそのカテゴリーの生成ロジックが含まれているか確認

## 💡 ベストプラクティス

1. **定期的な実行**: ドキュメントを追加・更新したら必ずスクリプトを実行
2. **バージョン管理**: `index.html`もGitで管理して変更履歴を追跡
3. **カスタマイズの文書化**: スクリプトをカスタマイズした場合は、このREADMEも更新
4. **命名規則の統一**: ファイル名に一貫性を持たせることで自動分類が正確になる

## 🔮 今後の拡張案

- [ ] 検索機能の追加
- [ ] タグ機能でクロスカテゴリー分類
- [ ] ドキュメントの最終更新日時を表示
- [ ] ドキュメント内容のプレビュー機能
- [ ] JSONやYAMLでのメタデータ管理
- [ ] GitHub Actions との統合で自動更新

## 📞 サポート

質問や問題がある場合は、Resonant Engineのメインドキュメントを参照してください。

---

**最終更新**: 2025-11-08
**バージョン**: 1.0.0

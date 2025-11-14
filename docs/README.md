# docs/README.md

# Resonant Engine Documentation

## 🗺️ Quick Navigation

### 🚀 初めての方へ
→ [Getting Started](01_getting_started/)

### 🔧 コンポーネント別に探す
→ [Components](02_components/)
- [Bridge Lite](02_components/bridge_lite/) - データアクセス抽象化層
- [Memory System](02_components/memory_system/) - 記憶システム
- [Daemon](02_components/daemon/) - バックグラウンド処理
- [Dashboard](02_components/dashboard/) - Web UI

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

### "新しいコンポーネントを設計したい"
1. [Philosophy](07_philosophy/) - 設計思想を理解
2. [Templates](10_templates/) - テンプレートを使用
3. 該当する [Components](02_components/) に配置

### "過去の意思決定を振り返りたい"
1. [History/Decisions](09_history/decisions/)
2. [Reviews](02_components/*/reviews/)

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

## 🔄 Last Updated

2025-11-14
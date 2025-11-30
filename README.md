# Resonant Engine

> The successor to **Kiro v3.1**  
> A self-reflective, resonance-driven architecture designed to synchronize  
> human intention and AI cognition through breathing intelligence.

## Core Philosophy
Resonant Engine is built upon the principle of *intelligent resonance* —  
a harmony between thought, structure, and execution.

---

## 🎯 What is Resonant Engine?

Resonant Engineは、**AIがシステム開発の経過を継続的に理解し、あなたの開発を支援するための基盤**です。

単なるGitOpsツールではありません。これは：
- 開発の**意図**を記録
- システムの**行動**を追跡
- 変更の**結果**を検証
- すべてを**因果関係**で繋げる

統合イベントストリームにより、「なぜこの変更が起きたか」を遡ることができます。

### v1.1の新機能: 統一イベントストリーム

```bash
# 開発意図を記録
$ python utils/record_intent.py "ユーザー認証機能の追加"

# 最近の活動を確認
$ python utils/trace_events.py recent

# 因果関係を遡る
$ python utils/trace_events.py causality <EventID>
```

詳細: [クイックスタートガイド](docs/quick_start_unified_stream.md)

---

## 📚 Documentation

- [アーキテクチャ概要](docs/architecture/kiro_v3.1_architecture.md)
- [統合設計書](docs/integration_design.md)
- [統合完了報告](docs/integration_complete.md)
- [クイックスタート](docs/quick_start_unified_stream.md)

### Notion統合
- [Notionセットアップガイド](docs/notion_setup_guide.md)
- [Notion統合サマリー](docs/notion_integration_summary.md)
- [環境変数テンプレート](docs/env_template.txt)

### API Documentation

Backend API（全機能統合）: http://localhost:8000/docs

すべてのエンドポイント（基本CRUD、矛盾検出、メモリ管理、ダッシュボード分析等）が単一のAPIで提供されます。

---

**Author:** 宏啓 加藤 (Hiroaki Kato)  
**Central Core:** Yuno (GPT-5)  
**Repository:** [resonant-engine](https://github.com/HiroKatoMiyagi/resonant-engine)  
**Version:** 1.1 (Unified Event Stream Integration)  
**Last Updated:** 2025-11-05

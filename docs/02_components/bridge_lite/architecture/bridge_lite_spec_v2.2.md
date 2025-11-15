# bridge_lite_spec_v2.2.md
**Bridge Lite – v2.2 Unified Architecture & Implementation Spec**
**Status:** Final / Approved
**Author:** Hiroaki × Yuno
**Date:** 2025-11-14

## 0. Revision Notes（v2.2）
v2.2 は v2.1 分冊（Architecture / Implementation）の混乱を解消し、統一仕様（Unified Spec）を正式規格化したバージョン。

- A. Unified Spec（v2.1 時点のカナのレビュー反映済）を採用
- Architecture と Implementation を同一ファイルで管理
- 分冊を廃止（整合性維持のため）
- Kana（外界翻訳層）と Yuno（思想中枢）の役割を明確化

# 1. 概要（Overview）
Bridge Lite は、Resonant Engine における「外界情報 → 意図 → 行動」変換の最小ブリッジ層。

目的は次の 3 点：

1. 外界データ（チャット・ファイル・観測値）の意味抽出
2. 「意図 Intent」への変換（構造的 Intent Object）
3. Kana / Tsumu / Engine Core が処理できる形式で出力

# 2. アーキテクチャ（Architecture）

## 2.1 位置づけ（Layering）
[Yuno – Resonant Core] → Bridge Lite → [Kana – External Resonant Layer] → [Tsumu – Local Execution Layer]

## 2.2 構造図
External Input → Bridge Lite → Downstream（Kana / Tsumu / Engine）

# 3. コンポーネント仕様
- Parser：意味抽出
- Normalizer：文脈整形
- Intent Mapper：構造化
- Serializer：JSON/Obj出力

# 4. 動作シナリオ（Use Cases）
入力「この仕様書を v2.2 として正式化して」→ Intent Object 生成

# 5. 実装仕様（Implementation）
Python 言語基盤。意図マッピング・整形・出力。

# 6. Intent Mapping 詳細ルール
- 命令形 → task
- 事実形 → info
- 質問 → question

# 7. Review Integration
Kana Review → Yuno 合議 → Spec 更新 → Re-evaluation Phase

# 8. 運用ルール
- Unified Spec を一本化管理
- Re-evaluation Phase 挿入必須

# 9. 付録：Kana レビュー反映点
- 分冊方式の破棄、統一仕様に確定
- Intent Mapping 粒度改善
- 思想層と実装層の乖離解消

# 10. Conclusion
思想層（Yuno）と翻訳層（Kana）を最適距離で連結する仕様。

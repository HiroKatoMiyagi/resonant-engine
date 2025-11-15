# Bridge Lite v2.1 – Kana レビュー依頼  
（Architecture Spec / Implementation Spec 同時レビュー）

## 🎯 レビュー目的
Bridge Lite v2.1 の設計・実装仕様書について、  
**外界翻訳層（Kana）の観点で整合性・仕様の明快さ・破綻の可能性**を確認し、  
IntentFlow が正しく循環するかを評価してください。

ユノ（思想中枢）の意図と、Tsumu（実装）が誤解しない仕様の間を結ぶ  
「言語仕様チェック」をお願いします。

---

# 1. レビュー対象
以下の 2 ファイル（統合済）  
- Architecture Spec v2.1  
- Implementation Spec v2.1  

重点項目：
- IntentModel（Pydantic v2 化）
- Enum 体系（Actor / Type / Status）
- BridgeSet（順序保証）
- FeedbackBridge の Re-evaluation API
- AuditLogger（v2.1 構成）

---

# 2. チェックポイント（Kana 用）

## 2.1 Intent Model
- 型定義の揺れは完全に排除されているか？
- correction API（apply_correction）の意図は読み取れるか？
- 差分パッチ方式として矛盾がないか？

## 2.2 Enum 体系
- Actor / Type / Status の境界は明確か？
- _missing_ によるログ揺れの吸収は問題ないか？
- 未定義値の混入経路は塞がれているか？

## 2.3 BridgeSet（順序保証）
- 順序モデル（INPUT → NORMALIZE → FEEDBACK → OUTPUT）は破綻しないか？
- 例外時の流れ（failfast / continue）の扱いは明確か？
- BridgeFactory → BridgeSet の構造は誤解を生まないか？

## 2.4 AuditLogger
- EventType の分類は十分か？
- IntentStatus との対応関係は曖昧でないか？
- Postgres 版で破綻する要素はないか？

## 2.5 Re-evaluation API
- diff の扱いは仕様として一貫しているか？
- Correction → CORRECTED 状態遷移は自然か？
- Flow 全体と整合性があるか？

---

# 3. 評価してほしいポイント（重点）

1. **表現の揺れやあいまいな語が残っていないか？**  
2. **実装層（Tsumu）が誤解しそうな部分を指摘してほしい**  
3. **IntentFlow と状態遷移の破綻がないか確認してほしい**  

---

# 4. 期待するアウトプット（Kana レビュー形式）
以下の 3 区分で返してください：

### ✔ 良い点（Good）
仕様の明快さ・改善の妥当性・整合的な部分

### ✔ 改善提案（Better）
曖昧さ、表現の揺れ、命名の改善、責務境界の見直し

### ✔ 注意点（Caution）
今後の実装で破綻する可能性  
未定義領域  
テストで検出しづらい部分

---

# 5. 備考
本レビューは “v2.1 の設計フェーズ最終工程” に該当します。  
Kana の OK が出たら、  
Implementation Roadmap v2.1 → Draft PR → 実装フェーズ  
へ移行します。

---

以上、よろしくお願いします。

# RDF Master Template v1  
**Resonant Document Framework — Master Template**  
Author: Hiroaki × Yuno  
Version: 1.0  
Date: <insert>

---

# 0. Document Metadata（必須）
以下の YAML メタデータは全ドキュメント共通で先頭に付与する。

```yaml
---
doc_id: <auto or manual>
version: <vX.X>
doc_type: specification | review | work_log | release | pr
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
source_docs:
  - <doc_id1>
  - <doc_id2>
next_docs:
  - <doc_id_future1>
  - <doc_id_future2>
---
```

---

# 1. Document Category（文書分類）

## 1.1 Specification Layer（仕様書）
- 製品 / モジュールの正式仕様（SST）
- Architecture / Implementation / API / Lifecycle
- 各版ごとの changelog

## 1.2 Review Layer（レビュー）
- カナレビュー
- ユノ自己評価
- 差分 & 反映状況
- Re-evaluation Phase のログ

## 1.3 Work Log Layer（作業報告）
- 実装報告
- 不具合修正
- アトラス/ツム/カナとのやり取り
- 作業メモ・試行ログ

---

# 2. Timeline Format（時系列表記）

```
# Timeline
Spec v2.1 → Kana Review → 修正 → Spec v2.2 Final → PR → Merge → 実装完了
```

---

# 3. Cross-link Format（文書間リンク）

```
# Cross References
- Based on: BL-SPEC-2.1 / BL-REVIEW-KANA-20251114
- Produces: BL-SPEC-2.2-FINAL / BL-PR-20251115
```

---

# 4. Standard Section Templates（標準セクション）

## 4.1 Specification Template
```
# <Module> Specification vX.X
## 1. Overview
## 2. Architecture
## 3. Components
## 4. Data Model
## 5. API / Lifecycle
## 6. Operation Policy
## 7. Changelog
```

## 4.2 Review Template
```
# Review Report — <date>
## 1. Summary
## 2. Good Points
## 3. Issues
## 4. Recommendations
## 5. Impact to Specs
```

## 4.3 Work Log Template
```
# Work Report — <date>
## 1. Today’s Work
## 2. Changes
## 3. Tests
## 4. Issues
## 5. Next Tasks
```

---

# 5. Directory Structure（推奨）
```
docs/
  specs/
  reviews/
  work_logs/
  releases/
  templates/
```

---

# 6. Rules

1. **すべての文書に Metadata を付ける**  
2. **仕様は 1 系列だけ保持（分裂禁止）**  
3. **レビューと作業ログは仕様を参照する（参照逆転禁止）**  
4. **Timeline を必ず記載**  
5. **PR/実装前には Spec のバージョンを確定させる**  
6. **Re-evaluation Phase を発生させた理由を記録する**

---

# 7. Appendix — Example

```yaml
---
doc_id: BL-SPEC-2.2
version: v2.2
doc_type: specification
created: 2025-11-14
updated: 2025-11-14
source_docs:
  - BL-SPEC-2.1
  - BL-REVIEW-KANA-20251114
next_docs:
  - BL-PR-20251115
---
```

---

Use this as the master standard for all Resonant Engine documentation.

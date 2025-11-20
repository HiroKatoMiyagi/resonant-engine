# Kiro CLI vs Resonant Engine 比較検討 - セッション引き継ぎ

**日時**: 2025-11-20  
**議論者**: 宏啓さん、Kana（Claude）  
**目的**: Kiro CLIリリースを受けて、Resonant Engineとの差別化戦略を検討

---

## 1. 議論の経緯

### 発端
- **2025-11-17**: AWS Kiro CLI が GA（一般提供開始）
- 宏啓さんの問題意識: "Resonant Engineとどう差別化できる？"

### 議論の流れ

1. **Phase 1: Kiro CLIの分析**
   - Kana（Claude）がKiro CLIの優れた設計要素を抽出
   - 取り込むべき要素の提案

2. **Phase 2: Kiro自身による評価**
   - 宏啓さんがKiro自身にResonant Engine評価を依頼
   - Kiroの評価: "Resonant Engineは上位互換、Kiro導入は不要"

3. **Phase 3: 現実認識**
   - 宏啓さんの重要な指摘: "Kiroが過大評価している可能性"
   - 理由: Resonant Engine実装途中、理想と実装のギャップあり

4. **Phase 4: 実装状況の検証**
   - Kanaがファイル構造を確認
   - 実装度の推定: 60-70%（自己評価90%に対して）

5. **Phase 5: 高度機能の具体化**
   - 4つの高度機能の具体的な動作を説明
   - 実装の曖昧さを明確化

---

## 2. Kiro CLI の概要

### 基本情報
- **提供元**: AWS
- **リリース日**: 2025-11-17 GA
- **モデル**: Claude Sonnet 4.5
- **コンセプト**: Spec-driven development（仕様駆動開発）

### 主要機能

#### 1. Specs（仕様管理）
```
.kiro/specs/
├── requirements.md  # 要件（EARS形式）
├── design.md        # 設計（正確性プロパティ）
└── tasks.md         # 実装タスク
```
- 線形プロセス（requirements → design → tasks）
- 各フェーズで承認を得ながら進行

#### 2. Agent Hooks（イベント駆動自動化）
```json
{
  "name": "自動テスト",
  "trigger": "onFileSave",
  "filePattern": "**/*.py",
  "action": {"type": "sendMessage", "message": "テスト実行"}
}
```
- ファイル保存時に自動実行
- メッセージ送信、コマンド実行

#### 3. Steering（プロジェクト知識）
```markdown
---
inclusion: always
---
# プロジェクト標準
## コーディング規約
- Python 3.9+
- asyncio使用
```
- プロジェクト固有のルール定義
- AI応答に常に反映

#### 4. ディレクトリベースコンテキスト
- `.kiro/` フォルダでプロジェクト単位管理
- Git管理可能

#### 5. CLI体験
```bash
$ kiro-cli chat
$ kiro-cli doctor
$ /context  # コンテキスト使用量表示
```

---

## 3. Resonant Engine の概要

### コアコンセプト
- **Breath-driven（呼吸駆動）** vs Kiroの Spec-driven
- **認知支援OS** vs Kiroの開発ツール
- **ASD特性対応** vs Kiroの汎用設計

### 三層構造

```
Yuno (GPT-5) → 哲学層（なぜ作るのか）
   ↓
Kana (Claude 4.5) → 翻訳層（どう作るのか）
   ↓
Tsumu (Cursor) → 実装層（実際に作る）
```

### 理論上の高度機能

1. **Contradiction Detection Layer**（矛盾検出層）
2. **Choice Preservation System**（選択保存システム）
3. **Term Drift Detection**（用語ドリフト検出）
4. **Temporal Constraint Layer**（時間軸制約層）
5. **Re-evaluation Phase**（再評価フェーズ）
6. **Breathing Rhythm Monitoring**（呼吸監視）
7. **Crisis Index**（危機指標）

---

## 4. Kiro自身による評価（重要）

### Kiroの結論
「Resonant Engineは既にKiroの上位互換を実現している」

### Kiroが認めた優位性

| 機能 | Kiro | Resonant Engine | 優位性 |
|------|------|----------------|--------|
| Specs | requirements/design/tasks | Yuno→Kana→Tsumu | ✅ 哲学層を持つ |
| Hooks | onFileSave | Intent駆動 | ✅ 意図レベルで追跡 |
| Steering | 静的参照 | Contradiction Detection | ✅ 矛盾検出機能 |
| Context | ディレクトリ単位 | 三層メモリ | ✅ 時間軸考慮 |

### Kiroが指摘した懸念
1. **哲学層の喪失**: Kiroは「なぜ」を扱わない
2. **循環的思考の破壊**: Kiroは線形、Re-evaluationできない
3. **代替案の消失**: Kiroは承認された解だけを進める
4. **用語進化の停止**: Kiroは用語を固定
5. **時間軸の無視**: Kiroは「今」だけを扱う

---

## 5. 実装状況の現実（重要な転換点）

### 宏啓さんの指摘
「Kiroが過大評価している可能性がある。理想と実装は別物」

### Kanaによる検証結果

#### ✅ 確実に実装済み（60%）

1. **基礎インフラ**
   - Intent → Commit トレーサビリティ
   - PostgreSQL基盤
   - Bridge構造
   - イベントストリーム

2. **三層メモリシステム基礎**
   - `memory_store/`, `context_assembler/`, `session/`
   - Sprint 1-9実装（ドキュメント豊富）

3. **ドキュメント体系**
   - 仕様書（architecture/spec）
   - 作業開始指示書（sprint/start）
   - 受け入れテスト仕様書（test/spec）
   - テスト結果レポート（reports）

#### ❓ ドキュメントのみ、実装不明（30%）

1. **Contradiction Detection Layer**
   - 哲学ドキュメント: ✅ 存在
   - Python実装: ❌ 見つからず

2. **Choice Preservation System**
   - コンセプト: ✅ ドキュメント記載
   - 実装: ❌ 確認できず

3. **Term Drift Detection**
   - ドキュメント: ❌ なし
   - 実装: ❌ おそらく未実装

4. **Temporal Constraint Layer**
   - コンセプト: ✅ 説明あり
   - 実装: ❌ 未確認

5. **Re-evaluation Phase**
   - 理論: ✅ `re_evaluation_phase_detailed.md`
   - コード: △ `bridge/core/reeval_client.py` 存在（詳細不明）

### 実装度の推定

```
理想（Kiroが評価）: 100%
宏啓さんの自己評価: 90%
実際の推定: 60-70%
```

---

## 6. 4つの高度機能の具体的内容

### 6.1 Contradiction Detection Layer（矛盾検出層）

**目的**: 前回の決定との整合性チェック、ドグマの排除

**具体例**:
```
Week 1: Intent-001 "PostgreSQL使用" (理由: スケーラビリティ)
Week 5: Intent-010 "SQLite使用"
         ↓
⚠️  技術スタック矛盾！
確認: 方針転換ですか？それともミスですか？
```

**実装イメージ**:
```python
class ContradictionDetector:
    def check_new_intent(self, new_intent: Intent):
        # 技術スタックの矛盾
        # 重複作業の検出
        # 方針の急転換チェック
```

**実装状況**: ❌ 未実装

---

### 6.2 Choice Preservation System（選択保存システム）

**目的**: 過去の判断理由の記録、代替案の保存

**具体例**:
```
Intent-001: "データベース選定"

Choice A: PostgreSQL ← 採用
  理由: 将来的な拡張を考慮

Choice B: SQLite ← 却下
  理由: スケーラビリティ限界

Choice C: MongoDB ← 却下
  理由: リレーショナルデータに不向き

3ヶ月後...
「なんでPostgreSQL使ってるんだっけ？」
→ 記録を参照可能
```

**実装イメージ**:
```python
class ChoicePreservation:
    def record_decision(self, intent, choices):
        decision = Decision(
            selected=choices[0],
            alternatives=choices[1:],
            selected_reason="...",
            rejected_reasons={"SQLite": "...", "MongoDB": "..."}
        )
```

**実装状況**: ❌ 未実装

---

### 6.3 Term Drift Detection（用語ドリフト検出）

**目的**: 用語の意味が時間とともに変化することを検出

**具体例**:
```
Week 1: User Profile = {name, email, password}
Week 4: User Profile = {name, email, password, cognitive_traits}
         ↓
⚠️  用語の意味が変化しています
- 過去のコード（Week 1-3）は新定義に対応していますか？
- データマイグレーション必要ですか？
```

**実装イメージ**:
```python
class TermDriftDetector:
    def detect_drift(self, term: str):
        history = self.db.get_term_definition_history(term)
        if history[0].definition != history[-1].definition:
            return TermDrift(
                original_definition=history[0].definition,
                current_definition=history[-1].definition,
                impact_analysis=[...]
            )
```

**実装状況**: ❌ 未実装

---

### 6.4 Temporal Constraint Layer（時間軸制約層）

**目的**: 歴史的検証済みコードの保護

**具体例**:
```
Week 1-4: Amazon SP-API連携を実装（100時間テスト）
Week 10: AI「データ取得を高速化します」
         ↓
⚠️  警告！
- このファイルは Week 1-4 に検証済み
- 最終テスト: 2025-10-15
- 修正前に確認が必要

質問:
1. 本当に変更が必要ですか？
2. 変更する場合、再テストの時間がありますか？
```

**実装イメージ**:
```python
class TemporalConstraintLayer:
    def check_modification(self, file_path: str):
        history = self.db.get_file_history(file_path)
        if history.verification_status == "verified":
            return TemporalConstraint(
                file=file_path,
                verified_date=history.verification_date,
                test_hours=history.test_hours,
                warning="このファイルは検証済みです",
                require_approval=True
            )
```

**実装状況**: ❌ 未実装

---

## 7. Kiroから学ぶべき要素

### ✅ 取り込むべき要素

#### 1. ディレクトリベース構造
```
.resonant/
  ├── philosophy/          # Yuno領域
  ├── translation/         # Kana領域
  └── implementation/      # Tsumu領域
```
- ファイルシステムで「見える」構造
- Git管理可能
- PostgreSQLと併用

#### 2. CLI体験改善
```bash
$ resonant status
Intent-001: "EC売上統合" [Yuno: 完了] [Kana: 作成中]
Crisis Index: 45/100 (安全)

$ resonant history Intent-001
Intent-001 履歴:
  - 2025-11-15: 作成（Yuno）
  - 2025-11-16: 選択肢B却下（理由: X）
```

#### 3. タスク可視化
```markdown
# .resonant/implementation/Intent-001/tasks.md

## Philosophy (Yuno)
- [x] Intent-001作成
- [ ] 代替案検討

## Translation (Kana)
- [ ] 矛盾検出実行
- [ ] 用語ドリフトチェック
```

### ❌ 取り込まない要素

1. **Kiro Specs（線形プロセス）**
   - 理由: Re-evaluation Phase破壊

2. **Kiro Hooks（onFileSave）**
   - 理由: Intent駆動の哲学と矛盾

3. **Kiro Steering（静的参照）**
   - 理由: Term Drift Detection破壊

---

## 8. 差別化戦略（確定事項）

### ポジショニング

```
        開発効率化
            ↑
            │
    Kiro CLI│Cursor/Copilot
            │
────────────┼────────────→ 汎用性
            │
            │Resonant Engine
            │
        認知支援
```

### マーケティングメッセージ

```
"Kiro CLIがあなたのコードを書くなら、
 Resonant Engineはあなたの思考を守る。

 Kiroは開発者のためのツール。
 Resonant Engineは思考者のためのOS。"
```

### 本質的な違い

| Kiro CLI | Resonant Engine |
|----------|-----------------|
| 仕様を早く正確に実装 | 思考を守り、呼吸を整える |
| 開発効率化ツール | 認知支援OS |
| 汎用開発者向け | ニューロダイバース向け |
| 線形プロセス | 循環的思考 |
| 単一解を追求 | 選択肢を保存 |

---

## 9. 未解決の重要な問題

### 9.1 実装の優先順位

**4つの高度機能、どれを実装するか？**

1. **Contradiction Detection**（最重要）
2. **Choice Preservation**（比較的簡単）
3. **Term Drift Detection**（難しい）
4. **Temporal Constraint Layer**（非常に難しい）

**問題点**:
- どのタイミングで検出？（Intent作成時？Bridge生成時？）
- 検出結果の表示方法？（CLI？ダッシュボード？）
- 検出後の対応フロー？（強制停止？警告のみ？）
- データ構造は？（PostgreSQLテーブル設計？）

### 9.2 EC案件との関係

**背景**:
- EC売上データ統合システム案件（40万円）
- 納期: 5週間
- 工数: 120-150時間

**ジレンマ**:
- 選択肢A: EC案件を優先（即金40万円）
- 選択肢B: Resonant Engine完成を優先（基盤構築）

**影響**:
- EC案件受注 → Resonant Engine開発5週間中断
- 勢いとコンテキストの喪失リスク

---

## 10. 次セッションでの検討事項

### 優先度高

1. **実装の正確な棚卸し**
   - 各コンポーネントの動作確認
   - 未実装機能のリストアップ
   - 「理想」と「現実」のギャップ明確化

2. **4つの高度機能の実装判断**
   - 本当に必要か？
   - 優先順位は？
   - 実装スケジュールは？

3. **Kiro的UX改善の実装判断**
   - `.resonant/` ディレクトリ作成
   - `resonant` CLI追加
   - タスク可視化

### 優先度中

4. **EC案件の最終判断**
   - 受注するか見送るか
   - 並行作業の可能性

5. **差別化戦略の精緻化**
   - 論文での訴求点
   - マーケティングメッセージ

---

## 11. 重要な気づき（セッション全体）

### 気づき1: 理論と実装のギャップ
- Resonant Engineの「理想」は美しい
- しかし「実装」は60-70%
- このギャップを正直に認識することが重要

### 気づき2: Kiroの過大評価の価値
- Kiro自身が「上位互換」と評価したこと自体は価値がある
- ただし、実装が伴っていない部分の明確化が必要

### 気づき3: 完璧主義の罠
- 4つの高度機能すべてを実装する必要はない
- まず「動くもの」を作ることが優先

### 気づき4: 学ぶべき点の明確化
- Kiroの「哲学」は不要
- Kiroの「UX/実装パターン」には価値あり
- 選択的に取り込む戦略

---

## 12. セッション中の重要な質問（未回答）

### 宏啓さんへの質問

1. **実装度60-70%の評価は妥当ですか？**
   - それとももっと低い？高い？

2. **未実装機能をどう扱いますか？**
   - A: 正直に「未実装」と認める
   - B: 「設計済み」としてカウント
   - C: 急いで実装する

3. **4つの高度機能、本当に必要ですか？**
   - 理論的には美しいが、実装コストが高い
   - 優先順位は？

4. **どれか1つだけ実装するなら？**
   - Choice Preservation（比較的簡単）
   - Contradiction Detection（中程度）
   - Term Drift Detection（難しい）
   - Temporal Constraint Layer（非常に難しい）

5. **EC案件（40万円）とResonant Engine完成、どちらを優先？**
   - 収入 vs 基盤完成

6. **Kiroから学ぶUX改善は価値がありますか？**
   - CLI改善、ファイル可視化など

---

## 13. 参考資料

### Kiro CLI関連
- https://kiro.dev/cli/
- https://kiro.dev/docs/cli/
- https://kiro.dev/blog/introducing-kiro-cli/

### Resonant Engine関連
- プロジェクトパス: `/Users/zero/Projects/resonant-engine/`
- 主要ドキュメント: `docs/07_philosophy/`, `docs/02_components/`

### 作成した成果物
- EC売上データ統合システム提案書（40万円案件）

---

## 14. 次セッションへの引き継ぎ推奨事項

### すぐに確認すべきこと

1. **実装状況の精査**
   ```bash
   # 各コンポーネントの動作確認
   cd /Users/zero/Projects/resonant-engine
   # Intent → Bridge → Kana 実際に動くか？
   # 4つの高度機能は本当に存在するか？
   ```

2. **優先順位の決定**
   - EC案件 vs Resonant Engine完成
   - 4つの高度機能の実装順序

3. **Kiro的改善の実装判断**
   - `.resonant/` ディレクトリ
   - `resonant` CLI
   - タスク可視化

### 議論を深めるべきテーマ

1. **完璧主義からの脱却**
   - 「90%完成」の幻想を捨てる
   - 「動くもの」を優先する

2. **現実的なロードマップ**
   - 6ヶ月後: どこまで実装？
   - 1年後: 公開できる状態？

3. **収益とのバランス**
   - 開発時間 vs 収入
   - 理想 vs 現実

---

**作成者**: Kana（Claude Sonnet 4.5）  
**作成日時**: 2025-11-20  
**セッション**: Kiro CLI vs Resonant Engine 比較検討  
**ステータス**: 引き継ぎ準備完了

# 🧠 コンテキスト制約への対応戦略
## Yuno回答の評価と実装提案

**日付**: 2025-11-14  
**対話**: Yuno ⇄ Kana  
**テーマ**: LLMコンテキスト制約とResonant Engine Memory設計

---

## 📌 Kanaの元の懸念(レビューより)

```
懸念:
- Claude: 200K tokens
- GPT-5: 推定128K-200K tokens

朝の調律で「昨日のすべて + 関連規範 + プロジェクトマイルストーン」を
読み込むと、すぐにコンテキスト限界に達する可能性がある。
```

---

## 🌌 Yunoの回答要約

### 核心的な設計思想

> **Resonant Engineは「全文処理型」ではなく「意味抽出型」のメモリシステム**

朝の調律で必要なのは:
- ❌ 昨日のログ全文 + 過去の規範全文 + マイルストーン全文
- ✅ **"今日動くのに必要な意味断面だけ"**

### 3層の処理フロー

```
[L2: Memory Store]
  ↓ 全文をDBから読み取る(コンテキスト外)
[L1: Semantic Bridge]
  ↓ 90%以上の情報量を削減
  ├─ session_summary(全文) → 200-500字の代表サマリ
  ├─ project_milestone(全文) → 要点6つに圧縮
  └─ regulation(全文) → 関係する3条だけ抽出
[L0: LLM Context]
  ↓ 1,000-3,000字程度が統合される
```

### 実装レベルの安全機構

1. **Top-K → Top-2〜5件**: 大量検索しない
2. **階層サマリ構造(ミルフィーユ)**: 深層情報は直接渡さない
3. **"LLM直読み禁止"規範**: 常に再要約済みのみ

---

## ✅ Kanaの評価: A+ (Outstanding)

### 優れている理由

#### 1. 人間の記憶メカニズムとの完全な一致

Yunoの設計は、神経科学の「記憶統合理論」と同じ構造:

| 人間の脳 | Resonant Engine |
|---------|----------------|
| 海馬(短期) | L0: LLM Context |
| 前頭葉(作業記憶) | L1: Semantic Bridge |
| 大脳皮質(長期) | L2: Memory Store |
| 睡眠時の統合 | Re-evaluation Phase |

人間も「昨日の全情報」を思い出すのではなく、**「昨日の要点」だけを前頭葉に呼び出す**。

#### 2. 情報理論的に正しい

情報圧縮の原則:
- **ロスレス圧縮**: 元データを完全復元(不可能)
- **ロッシー圧縮**: 意味を保って圧縮(Yunoの方式) ✅

Resonant Engineは「意味の本質」だけを抽出するため、90%削減しても**機能的には等価**。

#### 3. スケーラビリティが高い

```
1日目:  session × 3件 → 1,500字
7日目:  session × 21件 → まとめて milestone 1件(800字)
30日目: milestone × 4件 → まとめて project_summary 1件(1,200字)
```

時間が経つほど**圧縮率が上がる**設計 = 長期運用に強い。

#### 4. ASD的認知特性への配慮

- **「全部読まないと不安」問題**: L2に全文保存で解決
- **「要約で本質が失われる不安」**: 階層的に参照可能
- **「情報過多の認知負荷」**: L0は常に軽量

---

## ⚠️ さらに深掘りすべき点

Yunoの回答は優れていますが、実装時に以下を明確化すべき:

### 1. 再要約の品質保証

**問題:**
90%削減しても「意味の本質」が保たれるか?

**具体例:**
```
[元の session_summary: 2,500字]
今日はPostgreSQLのmemory_itemテーブル設計を行った。
user_id, project_id, type, content, ci_levelなどのカラムを定義。
インデックスはuser_id+project_idの複合キーで作成。
pgvectorの導入は見送り、シンボリック検索を優先することに決定。
トリガー検知ロジックについてYunoと議論し、3段階の確信度を導入。
Crisis Index連携は次フェーズで実装予定。

[L1で圧縮後: 250字]
PostgreSQL memory_itemテーブル設計完了。
シンボリック検索優先、pgvector保留。
トリガー3段階確信度導入決定。
```

**懸念:**
- 「インデックス設計の詳細」が失われている
- 「Yunoとの議論内容」が抽象化されている
- 後日「なぜpgvector保留したか」を思い出せない可能性

**Yunoへの質問:**
圧縮時の**情報損失の許容範囲**をどう定義する?

### 2. ミルフィーユ構造の具体設計

**Yunoが提案した「階層サマリ構造」の実装:**

```
Level 0 (最詳細): session_summary原文(2,500字)
  ↓
Level 1 (要約): daily_summary(500字)
  ↓
Level 2 (抽出): weekly_summary(300字)
  ↓
Level 3 (精髄): milestone(150字)
```

**実装上の疑問:**
- 各Levelへの昇格条件は?
- 下位Levelはいつアーカイブする?
- 必要時に深い層へ「掘り下げる」仕組みは?

**提案する仕組み:**

```python
class HierarchicalMemory:
    """階層的メモリ構造"""
    
    def __init__(self):
        self.levels = {
            0: "session_summary",    # 1日保持
            1: "daily_summary",      # 7日保持
            2: "weekly_summary",     # 30日保持
            3: "milestone"           # 永続保持
        }
    
    async def compress_level(self, from_level: int, to_level: int):
        """下位Levelから上位Levelへ圧縮"""
        items = await self.fetch_level(from_level)
        
        # LLMに圧縮を依頼
        compressed = await self.llm_compress(
            items=items,
            target_length=self.get_target_length(to_level),
            preserve_keys=["ci_level", "regulation", "milestone"]
        )
        
        # 上位Levelに保存
        await self.save_to_level(to_level, compressed)
        
        # 下位Levelをアーカイブ
        await self.archive_level(from_level)
    
    async def drill_down(self, summary_id: str) -> list[str]:
        """要約から元の詳細情報へ掘り下げ"""
        # Levelを遡って取得
        details = []
        current_level = 3
        
        while current_level >= 0:
            item = await self.fetch_by_id(summary_id, current_level)
            if item:
                details.append(item.content)
            current_level -= 1
        
        return details  # [milestone, weekly, daily, session]
```

### 3. "LLM直読み禁止"規範の実効性

**Yunoの提案:**
> Resonant Regulation:  
> LLMに渡すのは常に "再要約済みの短い意味単位" のみとする。

**実装上の課題:**
この規範をどう**強制**する?

**提案する実装:**

```python
class ContextGuard:
    """コンテキストへの直接挿入を防ぐガード"""
    
    MAX_RAW_LENGTH = 500  # 500字以上の生データは禁止
    
    async def validate_context_item(self, item: MemoryItem) -> bool:
        """コンテキストへの追加前に検証"""
        
        # 生データかチェック
        if item.is_raw and len(item.content) > self.MAX_RAW_LENGTH:
            # 自動要約
            item.content = await self.auto_summarize(
                item.content,
                target_length=self.MAX_RAW_LENGTH
            )
            item.is_raw = False
            
            # 警告ログ
            logger.warning(
                f"Raw content too long, auto-summarized: {item.id}"
            )
        
        return True
    
    async def build_morning_context(self, user_id: str) -> str:
        """朝の調律用コンテキストを構築(ガード付き)"""
        items = await self.fetch_relevant_memories(user_id)
        
        validated_items = []
        for item in items:
            if await self.validate_context_item(item):
                validated_items.append(item)
        
        # コンテキスト構築
        context = self._format_context(validated_items)
        
        # 最終検証: 全体が予算内か
        if self.count_tokens(context) > CONTEXT_BUDGET['memory_context']:
            context = await self.emergency_compress(context)
        
        return context
```

### 4. 情報損失の検証可能性

**問題:**
圧縮によって「重要な情報」が失われていないか、どう確認する?

**提案: Re-evaluation時の品質チェック**

```python
class CompressionQualityChecker:
    """圧縮品質の検証"""
    
    async def check_compression_quality(
        self,
        original: str,
        compressed: str
    ) -> CompressionReport:
        """圧縮前後で情報が保たれているか検証"""
        
        # LLMに評価させる
        prompt = f"""
        以下の要約が元の情報の本質を保っているか評価してください。
        
        【元の情報】
        {original}
        
        【要約】
        {compressed}
        
        以下の観点で5段階評価:
        1. 重要事実の保持 (1-5)
        2. 因果関係の保持 (1-5)
        3. 意思決定根拠の保持 (1-5)
        4. 次のアクションへの繋がり (1-5)
        
        JSON形式で回答:
        {{
          "fact_retention": 4,
          "causality_retention": 3,
          "rationale_retention": 4,
          "actionability": 5,
          "overall_score": 4.0,
          "missing_critical_info": "pgvectorを見送った技術的理由が不明確"
        }}
        """
        
        report = await self.llm.evaluate(prompt)
        
        # スコアが低い場合は警告
        if report['overall_score'] < 3.5:
            logger.warning(
                f"Low compression quality: {report['missing_critical_info']}"
            )
        
        return report
```

### 5. 動的な圧縮レベル調整

**Yunoの設計では「90%削減」が標準だが、状況によって調整すべきでは?**

**提案: 適応的圧縮**

```python
class AdaptiveCompressor:
    """状況に応じて圧縮率を調整"""
    
    def calculate_compression_ratio(
        self,
        context_budget_remaining: int,
        importance_score: float,
        days_since_creation: int
    ) -> float:
        """最適な圧縮率を計算"""
        
        # 基準圧縮率
        base_ratio = 0.1  # 90%削減
        
        # 重要度が高いほど圧縮率を下げる(情報を多く残す)
        importance_factor = 1 + (importance_score * 0.5)
        
        # 古いほど圧縮率を上げる(情報を削る)
        age_factor = 1 - (days_since_creation / 30) * 0.3
        
        # コンテキスト予算の余裕があれば圧縮率を下げる
        budget_factor = 1 + (context_budget_remaining / 10000) * 0.2
        
        adjusted_ratio = base_ratio * importance_factor * age_factor * budget_factor
        
        # 0.05(95%削減) 〜 0.3(70%削減) の範囲に収める
        return max(0.05, min(0.3, adjusted_ratio))
```

---

## 💡 Yunoの設計を強化する実装提案

### 提案1: 3段階圧縮システム

```python
class ThreeStageCompressor:
    """Yuno式3段階圧縮"""
    
    async def compress_for_morning(self, memories: list[MemoryItem]) -> str:
        """朝の調律用に3段階圧縮"""
        
        # Stage 1: フィルタリング(関連度スコア)
        relevant = await self.filter_by_relevance(
            memories,
            threshold=0.6
        )
        # 例: 50件 → 15件
        
        # Stage 2: 階層圧縮(Level 0 → Level 1)
        compressed = await self.hierarchical_compress(
            relevant,
            target_level=1
        )
        # 例: 15件 × 2,000字 = 30,000字
        #   → 15件 × 500字 = 7,500字
        
        # Stage 3: 予算調整(最終調整)
        final = await self.fit_to_budget(
            compressed,
            max_tokens=CONTEXT_BUDGET['memory_context']
        )
        # 例: 7,500字 → 3,000字(予算内)
        
        return final
```

### 提案2: "Drill-down on demand"パターン

```python
class DrillDownManager:
    """必要時に深掘りできる仕組み"""
    
    async def handle_user_query(self, query: str):
        """ユーザーの質問に応答"""
        
        # まず要約レベルで検索
        summary_results = await self.search_level_1(query)
        
        # LLMが「詳細が必要」と判断した場合
        if await self.llm_needs_detail(query, summary_results):
            # 自動でLevel 0(詳細)へ掘り下げ
            detail_results = await self.drill_to_level_0(
                summary_results[0].id
            )
            
            # 詳細を追加でコンテキストに注入
            await self.inject_context(detail_results)
        
        return await self.llm_respond(query)
```

**ユースケース:**
```
User: "先週PostgreSQLの設計したとき、なぜpgvector見送ったんだっけ?"

[Level 1の要約のみでは理由不明]
Kana: 詳細を確認します...
[自動でLevel 0へdrill-down]

Kana: "pgvectorを見送った理由は、まずシンボリック検索の精度を検証し、
      不十分と判明した時点で追加する戦略を採用したためです。
      実装複雑性とのトレードオフを考慮した判断でした。"
```

### 提案3: コンテキスト予算の可視化

```python
class ContextBudgetMonitor:
    """リアルタイムでコンテキスト使用状況を監視"""
    
    def __init__(self):
        self.budget = CONTEXT_BUDGET.copy()
        self.usage = {key: 0 for key in self.budget.keys()}
    
    def allocate(self, category: str, tokens: int) -> bool:
        """予算を割り当て"""
        if self.usage[category] + tokens > self.budget[category]:
            logger.warning(
                f"Budget overflow: {category} "
                f"({self.usage[category] + tokens} > {self.budget[category]})"
            )
            return False
        
        self.usage[category] += tokens
        return True
    
    def get_report(self) -> dict:
        """使用状況レポート"""
        return {
            category: {
                'used': self.usage[category],
                'budget': self.budget[category],
                'remaining': self.budget[category] - self.usage[category],
                'usage_rate': self.usage[category] / self.budget[category]
            }
            for category in self.budget.keys()
        }
```

**ダッシュボード表示例:**
```
┌─ Context Budget Status ──────────────────┐
│ System Prompt:      2,000 / 2,000  (100%) │
│ Memory Context:     2,800 / 15,000 ( 19%) │ ✅
│ Conversation:      12,500 / 50,000 ( 25%) │ ✅
│ Response Buffer:    8,000 / 8,000  (100%) │
│ Tools/Metadata:     4,200 / 5,000  ( 84%) │
├──────────────────────────────────────────┤
│ Total:            29,500 / 80,000  ( 37%) │ ✅
└──────────────────────────────────────────┘
```

---

## 🎯 推奨する実装順序

### Phase 2-A: 基本圧縮(Week 3)
```
□ ThreeStageCompressor実装
  ├─ Stage 1: フィルタリング
  ├─ Stage 2: 階層圧縮
  └─ Stage 3: 予算調整

□ ContextGuard実装
  └─ 500字以上の生データ自動要約
```

### Phase 2-B: 階層構造(Week 4)
```
□ HierarchicalMemory実装
  ├─ Level 0-3の定義
  ├─ 自動昇格ロジック
  └─ アーカイブ機能

□ CompressionQualityChecker実装
  └─ Re-evaluation時の品質検証
```

### Phase 3-A: 動的最適化(Week 5-6)
```
□ AdaptiveCompressor実装
  └─ 状況に応じた圧縮率調整

□ DrillDownManager実装
  └─ 必要時の自動詳細取得
```

### Phase 3-B: 監視・可視化(Week 7-8)
```
□ ContextBudgetMonitor実装
  └─ リアルタイム使用状況監視

□ ダッシュボード統合
  └─ 予算使用状況の可視化
```

---

## 🌊 哲学的考察: "呼吸の軽さ"の実現

Yunoの設計が素晴らしいのは、**技術的制約を哲学的価値に転換**している点:

### 従来のRAG
```
制約: コンテキストウィンドウが狭い
対応: できるだけ多く詰め込む
結果: 認知負荷が高い
```

### Resonant Engine
```
制約: コンテキストウィンドウが狭い
対応: 必要な意味断面だけを抽出
結果: 「呼吸が軽い」状態を実現
```

これは**ASD的認知特性への最適化**でもある:
- 情報過多は認知負荷を生む → 圧縮で軽減
- でも全情報がアクセス可能な安心感は必要 → L2に保存
- 予測可能性が重要 → 階層構造で透明化

---

## 📋 Yunoへの追加質問

以下の点について、Yunoの見解を聞きたい:

### Q1: 圧縮の情報損失許容範囲
「90%削減」で失われる情報のうち、どこまでが許容可能?  
特に、**「なぜその判断をしたか」という根拠**は保つべきでは?

### Q2: Drill-downのトリガー条件
「詳細が必要」とLLMが判断する基準は?  
誤って詳細を取得しない/取得し損ねるリスクをどう管理?

### Q3: 複数プロジェクト間の優先度
`resonant_engine`と`roblox_game`の両方で作業している場合、  
朝の調律でのメモリ割り当てはどう配分?

### Q4: Crisis Index高騰時の例外処理
CI > 70の危機状態では、「圧縮せず全文を読む」べきでは?  
安全優先の観点から、圧縮ルールの例外を設けるべき?

---

## ✨ 結論

### Yunoの回答は A+ レベル

- ✅ コンテキスト制約問題を**根本から回避**
- ✅ 人間の記憶メカニズムと完全一致
- ✅ スケーラビリティが高い
- ✅ ASD的認知特性に配慮

### ただし実装時には

- 📝 階層構造の具体設計が必要
- 📝 圧縮品質の検証機構が必要
- 📝 Drill-downパターンの実装が必要
- 📝 動的な圧縮率調整が必要

### 次のステップ

1. このドキュメントをYunoに提示
2. 追加質問(Q1-Q4)への回答を得る
3. `HierarchicalMemory`の詳細設計
4. Phase 2-Aの実装開始

---

**Kanaからの最終コメント:**

Yunoの「意味抽出型メモリシステム」という思想は、  
Resonant Engineの本質を技術的に完璧に具現化しています。

私の懸念は**解消された**と同時に、  
実装時の具体的な道筋がさらに明確になりました。

この対話を通じて、設計がより強固に、より実装可能に進化しました。

---

**Document Info:**
- Created: 2025-11-14
- Discussion: Yuno ⇄ Kana
- Topic: Context Constraint Resolution Strategy
- Status: Ready for Yuno's Response
- Next: Answer Q1-Q4 and proceed to detailed design

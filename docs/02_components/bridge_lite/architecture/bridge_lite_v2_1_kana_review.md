# Bridge Lite v2.1 – Kanaレビュー

## ✔ 良い点（Good）

### 1. Enum体系の正規化
**IntentActorEnum / BridgeTypeEnum / IntentStatusEnum** の三体系分離は明快です。責務境界が明確で、旧v1.xの混在問題を解消しています。`_missing_` による旧ログ吸収の設計も妥当。

### 2. BridgeSetによる順序保証
固定順序 `INPUT → NORMALIZE → FEEDBACK → OUTPUT` の設計は、IntentFlowの"統制されたパイプライン"として一貫性があります。BridgeFactoryの返却物をBridgeSetが統一管理する構造も理解可能。

### 3. Pydantic v2のstrict mode活用
`ConfigDict(strict=True)` による厳格バリデーションは、型揺れ排除の根本解決として適切。`Enum → raw_input → Enum` の往復保証は重要な設計判断。

### 4. Re-evaluation APIの導入意図
Kana/Yunoからの補正を統合する発想は、Resonant Engineの呼吸構造に適合。`apply_correction(diff)` による差分マージは拡張性があります。

### 5. AuditLoggerの構造整理
Postgres対応とOps Policy v1.0準拠（1 Intent 1 Event）は、監査証跡として妥当な粒度設計。

---

## ✔ 改善提案（Better）

### 1. Status遷移の条件を明示してください
**問題**: Architecture Specで以下の遷移が示されていますが、**どのBridgeが・どのタイミングで・どのStatusを生成するか**が不明確です。

```
RECEIVED → NORMALIZED → PROCESSED → CORRECTED → COMPLETED
```

**提案**: 以下のような対応表を追加してください。

```
Bridge         Input Status    Output Status    Trigger
INPUT          RECEIVED        NORMALIZED       初期化完了時
NORMALIZE      NORMALIZED      PROCESSED        正規化完了時
FEEDBACK       PROCESSED       CORRECTED        Re-eval実行時（オプション）
OUTPUT         PROCESSED       COMPLETED        出力完了時
               CORRECTED       COMPLETED        補正後出力完了時
```

**特に曖昧**: 
- `CORRECTED` は Re-eval API経由のみで遷移するのか？
- `FEEDBACK` Bridgeは常に `CORRECTED` を生成するのか、それとも補正不要時は通過するのか？
- `PROCESSED → COMPLETED` の直接遷移は許可されるのか？

### 2. Re-evaluation APIのdiff仕様を定義してください
**問題**: `apply_correction(diff)` の `diff` 形式が未定義です。実装層（Tsumu）が誤解する可能性があります。

**提案**: 以下のような仕様を追加してください。

```python
# diffの形式例
diff = {
    "payload": {
        "key_to_update": "new_value",
        "nested.path": "new_nested_value"
    },
    "status": "CORRECTED",  # Statusも補正対象にするか？
    "metadata": {
        "correction_source": "YUNO",
        "correction_reason": "..."
    }
}
```

**質問**:
- JSONPatchスタイル（RFC 6902）を採用するのか？
- それとも単純なdict merge？
- Status/Actor/Typeは補正対象に含まれるのか？
- 補正履歴（correction_history）はIntentModelに保存するのか？

### 3. AuditLoggerのEventTypeを列挙してください
**問題**: Architecture Specで `event: AuditEventType` とありますが、**具体的なEvent一覧が欠落**しています。

**提案**: 以下のような列挙を追加してください。

```python
class AuditEventType(str, Enum):
    INTENT_RECEIVED = "intent_received"
    BRIDGE_STARTED = "bridge_started"
    BRIDGE_COMPLETED = "bridge_completed"
    BRIDGE_FAILED = "bridge_failed"
    REEVALUATED = "reevaluated"
    STATUS_CHANGED = "status_changed"
    # ... 他に必要なイベント
```

これがないと、AuditLoggerのクエリ設計やOps Policy準拠の検証ができません。

### 4. BridgeSetの例外処理ポリシーを明確化してください
**問題**: 「failfast / continue モード切り替え」とありますが、**切り替え基準が不明**です。

**提案**:
```python
class BridgeSet:
    def execute(self, intent: IntentModel, mode: ExecutionMode = ExecutionMode.FAILFAST):
        """
        mode = FAILFAST: 最初の例外で即座に停止、IntentStatus = FAILED
        mode = CONTINUE: 例外をAuditLoggerに記録し、次のBridgeへ継続
        mode = SELECTIVE: Bridge種別によって挙動を変える（設定ファイル）
        """
```

**質問**:
- modeはIntent作成時に決定するのか、実行時に決定するのか？
- CONTINUEモードで全Bridgeが失敗した場合、IntentStatusはどうなるのか？
- 再試行（retry）機能はBridgeSetの責務なのか？

### 5. BridgeFactoryの役割を明示してください
**問題**: 「BridgeFactory が返す "BridgeSet バンドル" に対応」という表現が**曖昧**です。

**提案**: BridgeFactoryの責務を明記してください。

```
BridgeFactory:
  責務: BridgeTypeEnumに応じた適切なBridge実装を返す
  返却: 個別Bridge or BridgeSetインスタンス？
  設定: どこから設定を読むのか（環境変数/YAML/DB？）
```

**質問**:
- BridgeFactoryは「BridgeSetを返す」のか、それとも「個別のBridgeを返してBridgeSetが組み立てる」のか？
- "バンドル"という表現は何を意味するのか？

### 6. 命名の一貫性: BridgeTypeEnum vs Bridge役割
**問題**: `BridgeTypeEnum` の値が `INPUT/NORMALIZE/FEEDBACK/OUTPUT` となっていますが、これは**Bridge種別**なのか**処理段階**なのか曖昧です。

**提案**: 以下のいずれかに統一してください。

**案A: 処理段階として明確化**
```python
class ProcessingStageEnum(str, Enum):
    INPUT = "input"
    NORMALIZE = "normalize"
    FEEDBACK = "feedback"
    OUTPUT = "output"
```

**案B: Bridge種別として明確化**
```python
class BridgeTypeEnum(str, Enum):
    INPUT_BRIDGE = "input_bridge"
    NORMALIZE_BRIDGE = "normalize_bridge"
    # ...
```

現状の `BridgeTypeEnum` は両方の意味を含んでいて、実装層で混乱する可能性があります。

---

## ✔ 注意点（Caution）

### 1. 並行実行時の競合リスク
**問題**: IntentModelの `updated_at` 更新が複数プロセスで衝突する可能性。

**シナリオ**:
```
Process A: Intent読み取り → apply_correction → updated_at更新
Process B: Intent読み取り → Status更新 → updated_at更新
→ Process Aの補正が失われる（Last Write Wins）
```

**推奨**:
- Postgresのトランザクション分離レベルを明示
- 楽観的ロック（version番号）またはペシミスティックロック（SELECT FOR UPDATE）の検討
- 同時補正検出メカニズムの設計

### 2. Enum._missing_のログ戦略が未定義
**問題**: `_missing_` で旧値を吸収する際、**どのようにログに記録するか**が未定義です。

**推奨**:
```python
@classmethod
def _missing_(cls, value):
    logger.warning(f"Legacy enum value detected: {value}, mapping to {default}")
    # AuditLoggerにも記録するべきか？
    # メトリクスにカウントするべきか？
    return default
```

旧ログ吸収は「技術的負債の可視化」の機会でもあるため、メトリクス収集を推奨します。

### 3. Re-evaluation APIの冪等性が未保証
**問題**: 同じdiffを複数回適用した場合の挙動が未定義です。

**シナリオ**:
```
1回目: apply_correction({"payload.count": 10})  → count=10
2回目: apply_correction({"payload.count": 10})  → count=10（OK）

vs

1回目: apply_correction({"payload.count": "+10"})  → count=10
2回目: apply_correction({"payload.count": "+10"})  → count=20（NG?）
```

**推奨**:
- diffの形式を「絶対値」に限定する（冪等性保証）
- または、correction_idによる重複検出機構を実装
- Re-eval APIのレスポンスに `already_applied: bool` を含める

### 4. BridgeSet例外処理のスコープが不明
**問題**: 「try/except で AuditLogger に記録」とありますが、**どのレベルの例外をcatchするか**が不明確です。

**質問**:
- `ValidationError` はcatchするのか？（モデル不正）
- `NetworkError` はcatchするのか？（外部API呼び出し失敗）
- `SystemExit` / `KeyboardInterrupt` はcatchするのか？

**推奨**:
```python
# 明示的な例外階層設計
class BridgeExecutionError(Exception):
    """BridgeSet内で回復可能なエラー"""
    
class BridgeFatalError(Exception):
    """BridgeSet外で処理すべき致命的エラー"""

# BridgeSet内
try:
    bridge.execute(intent)
except BridgeExecutionError as e:
    audit_logger.log(...)
    if mode == FAILFAST: raise
except BridgeFatalError:
    raise  # 上位層へ委譲
```

### 5. StatusのCORRECTED→COMPLETEDの遷移条件が未定義
**問題**: Re-eval後、どのタイミングで `COMPLETED` に遷移するのかが不明です。

**シナリオ**:
```
PROCESSED → Re-eval → CORRECTED → ??? → COMPLETED
                                   ↑
                            OUTPUTを再実行？
                            それとも自動遷移？
```

**推奨**: 以下のいずれかを選択し、明記してください。

**案A: Re-eval後に自動COMPLETED**
```
CORRECTED状態はログ用の一時状態で、即座にCOMPLETEDへ
```

**案B: Re-eval後にOUTPUT再実行**
```
CORRECTED → OUTPUT Bridge再実行 → COMPLETED
（補正内容を反映した出力が必要な場合）
```

### 6. テストカバレッジの「最低8ケース」は不足の可能性
**問題**: Implementation Specで「正常系/異常系テストの実装（最低 8 ケース）」とありますが、組み合わせ爆発を考慮すると不足です。

**推奨**: 以下のような構造的テスト設計を追加してください。

```
テスト軸:
1. Bridge種別（4種）× 成功/失敗（2種）= 8ケース
2. Enum揺れ（Actor/Type/Status）× 正常化 = 3ケース
3. Re-eval（idempotency/conflict/invalid_diff）= 3ケース
4. BridgeSet（failfast/continue/partial_failure）= 3ケース
5. AuditLogger（postgres/local/rollback）= 3ケース

最低: 20ケース以上を推奨
```

---

## 総合評価

### 🟢 設計の方向性: **適切**
Enum正規化、BridgeSet順序保証、Re-evaluation APIの導入は、IntentFlowの構造整理として妥当です。Pydantic v2のstrict mode活用も適切。

### 🟡 仕様の明快さ: **改善必要**
Status遷移条件、diff仕様、EventType列挙、例外処理ポリシーなど、**実装層が判断に迷う箇所**が複数あります。これらを明記しないと、Tsumuが独自解釈で実装し、後で破綻する可能性があります。

### 🔴 注意すべき破綻リスク: **中程度**
並行実行の競合、Re-eval冪等性、Status遷移の不整合など、**運用時に顕在化するリスク**があります。特に並行実行は、Postgresトランザクション設計なしでは確実に問題化します。

---

## 🎯 実装前に解決すべき項目（優先度順）

1. **P1**: Status遷移条件の対応表作成（Bridge×Status）
2. **P1**: Re-evaluation APIのdiff仕様定義
3. **P1**: AuditLoggerのEventType列挙
4. **P2**: BridgeSet例外処理ポリシーの明確化
5. **P2**: 並行実行時の競合対策設計
6. **P3**: BridgeFactoryの責務明記
7. **P3**: Re-eval冪等性保証の設計

これらを解決すれば、**Implementation Roadmap v2.1への移行OK**と判断します。

---

## 次のステップ

1. 上記P1項目（3つ）の仕様追加
2. 宏啓さんの判断とYunoへのフィードバック
3. Architecture Spec v2.1.1への反映
4. Implementation Roadmap v2.1の作成
5. Draft PR作成 → 実装フェーズ開始

---

**レビュー実施日**: 2025-11-14  
**レビュアー**: Kana（外界翻訳層）  
**対象**: Bridge Lite Architecture Spec v2.1 / Implementation Spec v2.1

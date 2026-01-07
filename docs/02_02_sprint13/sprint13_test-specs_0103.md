# Sprint 13: フロントエンドUI統合テスト仕様書

**作成日**: 2026-01-03
**Sprint**: 13
**対象**: フロントエンドUI統合テスト
**関連仕様書**: sprint13_specs_0103.md

---

## 1. テスト概要

### 1.1 テストスコープ

| テストレベル | 対象 | ツール |
|-------------|------|--------|
| 単体テスト | コンポーネント | Vitest + React Testing Library |
| 統合テスト | API連携 | Vitest + MSW |
| E2Eテスト | ユーザーフロー | Playwright |

### 1.2 テスト対象機能

1. Contradiction Resolve UI
2. Dashboard Analytics Page
3. Choice Points Page
4. Memory Lifecycle Page
5. Term Drift Detection UI
6. Temporal Constraint UI
7. File Modification UI

---

## 2. 単体テスト仕様

### 2.1 Contradiction Resolve UI

#### 2.1.1 ContradictionResolveModal.test.tsx

```typescript
describe('ContradictionResolveModal', () => {
  const mockContradiction: Contradiction = {
    id: 'test-id-1',
    user_id: 'hiroki',
    new_intent_id: 'intent-1',
    new_intent_content: 'PostgreSQLを使用する',
    conflicting_intent_id: 'intent-2',
    conflicting_intent_content: 'SQLiteを使用する',
    contradiction_type: 'tech_stack',
    confidence_score: 0.85,
    detected_at: '2026-01-03T10:00:00Z',
    details: {},
    resolution_status: 'pending',
    resolution_action: null,
    resolution_rationale: null,
    resolved_at: null,
  };

  test('TC-CR-001: モーダルが正しく表示される', async () => {
    render(
      <ContradictionResolveModal
        contradiction={mockContradiction}
        isOpen={true}
        onClose={vi.fn()}
        onResolve={vi.fn()}
      />
    );

    expect(screen.getByText('矛盾の解決')).toBeInTheDocument();
    expect(screen.getByText('tech_stack')).toBeInTheDocument();
    expect(screen.getByText('85%')).toBeInTheDocument();
  });

  test('TC-CR-002: 解決アクション選択が機能する', async () => {
    const user = userEvent.setup();
    render(
      <ContradictionResolveModal
        contradiction={mockContradiction}
        isOpen={true}
        onClose={vi.fn()}
        onResolve={vi.fn()}
      />
    );

    const policyChangeRadio = screen.getByLabelText(/policy_change/i);
    await user.click(policyChangeRadio);

    expect(policyChangeRadio).toBeChecked();
  });

  test('TC-CR-003: 10文字未満の根拠でエラー表示', async () => {
    const user = userEvent.setup();
    render(
      <ContradictionResolveModal
        contradiction={mockContradiction}
        isOpen={true}
        onClose={vi.fn()}
        onResolve={vi.fn()}
      />
    );

    const rationaleInput = screen.getByPlaceholderText(/解決根拠/i);
    await user.type(rationaleInput, '短い');

    const submitButton = screen.getByRole('button', { name: /解決を確定/i });
    await user.click(submitButton);

    expect(screen.getByText(/10文字以上/i)).toBeInTheDocument();
  });

  test('TC-CR-004: 有効な入力で解決APIが呼ばれる', async () => {
    const user = userEvent.setup();
    const onResolve = vi.fn().mockResolvedValue(undefined);

    render(
      <ContradictionResolveModal
        contradiction={mockContradiction}
        isOpen={true}
        onClose={vi.fn()}
        onResolve={onResolve}
      />
    );

    await user.click(screen.getByLabelText(/policy_change/i));
    await user.type(
      screen.getByPlaceholderText(/解決根拠/i),
      'これは十分に長い解決根拠です。'
    );
    await user.click(screen.getByRole('button', { name: /解決を確定/i }));

    expect(onResolve).toHaveBeenCalledWith({
      resolution_action: 'policy_change',
      resolution_rationale: 'これは十分に長い解決根拠です。',
      resolved_by: expect.any(String),
    });
  });

  test('TC-CR-005: キャンセルでモーダルが閉じる', async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();

    render(
      <ContradictionResolveModal
        contradiction={mockContradiction}
        isOpen={true}
        onClose={onClose}
        onResolve={vi.fn()}
      />
    );

    await user.click(screen.getByRole('button', { name: /キャンセル/i }));

    expect(onClose).toHaveBeenCalled();
  });
});
```

#### 2.1.2 ContradictionItem.test.tsx（拡張）

```typescript
describe('ContradictionItem - Resolve機能', () => {
  test('TC-CI-001: 解決ボタンクリックでモーダル表示', async () => {
    const user = userEvent.setup();

    render(<ContradictionItem contradiction={mockContradiction} />);

    await user.click(screen.getByRole('button', { name: /解決/i }));

    expect(screen.getByText('矛盾の解決')).toBeInTheDocument();
  });

  test('TC-CI-002: 解決済み項目は解決ボタン非表示', () => {
    const resolvedContradiction = {
      ...mockContradiction,
      resolution_status: 'resolved',
    };

    render(<ContradictionItem contradiction={resolvedContradiction} />);

    expect(screen.queryByRole('button', { name: /解決/i })).not.toBeInTheDocument();
  });
});
```

---

### 2.2 Dashboard Analytics Page

#### 2.2.1 SystemOverview.test.tsx

```typescript
describe('SystemOverview', () => {
  const mockOverview: SystemOverview = {
    total_users: 12,
    active_sessions: 5,
    total_intents: 100,
    completed_intents: 85,
    pending_contradictions: 3,
    system_health: 'healthy',
    uptime_seconds: 86400,
    memory_usage_mb: 160,
    cpu_usage_percent: 40,
    last_updated: '2026-01-03T10:00:00Z',
  };

  test('TC-SO-001: ステータスカードが正しく表示される', () => {
    render(<SystemOverview data={mockOverview} />);

    expect(screen.getByText('12')).toBeInTheDocument(); // Users
    expect(screen.getByText('5')).toBeInTheDocument();  // Sessions
    expect(screen.getByText('85%')).toBeInTheDocument(); // Intent完了率
    expect(screen.getByText('3')).toBeInTheDocument();  // Pending
  });

  test('TC-SO-002: システムヘルスが色分け表示される', () => {
    render(<SystemOverview data={mockOverview} />);

    const healthIndicator = screen.getByTestId('health-indicator');
    expect(healthIndicator).toHaveClass('bg-green-500'); // healthy
  });

  test('TC-SO-003: warningステータスでオレンジ表示', () => {
    const warningOverview = { ...mockOverview, system_health: 'warning' as const };
    render(<SystemOverview data={warningOverview} />);

    const healthIndicator = screen.getByTestId('health-indicator');
    expect(healthIndicator).toHaveClass('bg-orange-500');
  });

  test('TC-SO-004: メモリ使用率バーが正しく表示される', () => {
    render(<SystemOverview data={mockOverview} />);

    const memoryBar = screen.getByTestId('memory-bar');
    // 160MB / 200MB = 80%
    expect(memoryBar).toHaveStyle({ width: '80%' });
  });
});
```

#### 2.2.2 TimelineChart.test.tsx

```typescript
describe('TimelineChart', () => {
  const mockTimeline: TimelineResponse = {
    entries: [
      {
        timestamp: '2026-01-03T10:00:00Z',
        event_type: 'intent_created',
        event_data: { intent_id: 'i-1' },
        user_id: 'hiroki',
        intent_id: 'i-1',
        session_id: 's-1',
      },
      {
        timestamp: '2026-01-03T11:00:00Z',
        event_type: 'contradiction_detected',
        event_data: { contradiction_id: 'c-1' },
        user_id: 'hiroki',
        intent_id: 'i-2',
        session_id: 's-1',
      },
    ],
    granularity: 'hour',
    start_time: '2026-01-03T00:00:00Z',
    end_time: '2026-01-03T23:59:59Z',
    total_count: 2,
  };

  test('TC-TC-001: タイムラインエントリが表示される', () => {
    render(<TimelineChart data={mockTimeline} />);

    expect(screen.getByText('intent_created')).toBeInTheDocument();
    expect(screen.getByText('contradiction_detected')).toBeInTheDocument();
  });

  test('TC-TC-002: granularity切り替えでコールバック呼び出し', async () => {
    const user = userEvent.setup();
    const onGranularityChange = vi.fn();

    render(
      <TimelineChart
        data={mockTimeline}
        onGranularityChange={onGranularityChange}
      />
    );

    await user.click(screen.getByRole('button', { name: /day/i }));

    expect(onGranularityChange).toHaveBeenCalledWith('day');
  });
});
```

#### 2.2.3 CorrectionsTable.test.tsx

```typescript
describe('CorrectionsTable', () => {
  const mockCorrections: CorrectionsResponse = {
    corrections: [
      {
        id: 'cor-1',
        correction_type: 'intent_update',
        original_value: { text: '古い値' },
        corrected_value: { text: '新しい値' },
        corrected_by: 'hiroki',
        correction_reason: 'バグ修正',
        corrected_at: '2026-01-03T10:00:00Z',
        intent_id: 'i-1',
        user_id: 'hiroki',
      },
    ],
    count: 1,
  };

  test('TC-CT-001: 修正履歴が表形式で表示される', () => {
    render(<CorrectionsTable data={mockCorrections} />);

    expect(screen.getByText('intent_update')).toBeInTheDocument();
    expect(screen.getByText('バグ修正')).toBeInTheDocument();
    expect(screen.getByText('hiroki')).toBeInTheDocument();
  });

  test('TC-CT-002: 空の場合は「修正履歴なし」表示', () => {
    render(<CorrectionsTable data={{ corrections: [], count: 0 }} />);

    expect(screen.getByText(/修正履歴なし/i)).toBeInTheDocument();
  });
});
```

---

### 2.3 Choice Points Page

#### 2.3.1 ChoicePointItem.test.tsx

```typescript
describe('ChoicePointItem', () => {
  const mockChoicePoint: ChoicePoint = {
    id: 'cp-1',
    user_id: 'hiroki',
    question: 'どのデータベースを使用するか？',
    choices: [
      { choice_id: 'c-1', choice_text: 'PostgreSQL' },
      { choice_id: 'c-2', choice_text: 'SQLite' },
      { choice_id: 'c-3', choice_text: 'MongoDB' },
    ],
    tags: ['design', 'db'],
    context_type: 'architecture',
    status: 'pending',
    selected_choice_id: null,
    decision_rationale: null,
    rejection_reasons: {},
    created_at: '2026-01-03T10:00:00Z',
    decided_at: null,
  };

  test('TC-CPI-001: 質問と選択肢が表示される', () => {
    render(<ChoicePointItem choicePoint={mockChoicePoint} />);

    expect(screen.getByText('どのデータベースを使用するか？')).toBeInTheDocument();
    expect(screen.getByText('PostgreSQL')).toBeInTheDocument();
    expect(screen.getByText('SQLite')).toBeInTheDocument();
    expect(screen.getByText('MongoDB')).toBeInTheDocument();
  });

  test('TC-CPI-002: タグが表示される', () => {
    render(<ChoicePointItem choicePoint={mockChoicePoint} />);

    expect(screen.getByText('#design')).toBeInTheDocument();
    expect(screen.getByText('#db')).toBeInTheDocument();
  });

  test('TC-CPI-003: pending状態で決定ボタン表示', () => {
    render(<ChoicePointItem choicePoint={mockChoicePoint} />);

    expect(screen.getByRole('button', { name: /決定/i })).toBeInTheDocument();
  });

  test('TC-CPI-004: decided状態で選択結果表示', () => {
    const decidedPoint = {
      ...mockChoicePoint,
      status: 'decided' as const,
      selected_choice_id: 'c-1',
      decision_rationale: 'PostgreSQLが最も適している',
    };

    render(<ChoicePointItem choicePoint={decidedPoint} />);

    expect(screen.getByText(/選択済み: PostgreSQL/)).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /決定/i })).not.toBeInTheDocument();
  });
});
```

#### 2.3.2 ChoicePointDecideModal.test.tsx

```typescript
describe('ChoicePointDecideModal', () => {
  test('TC-CPDM-001: 選択肢のラジオボタンが表示される', () => {
    render(
      <ChoicePointDecideModal
        choicePoint={mockChoicePoint}
        isOpen={true}
        onClose={vi.fn()}
        onDecide={vi.fn()}
      />
    );

    expect(screen.getByRole('radio', { name: /PostgreSQL/i })).toBeInTheDocument();
    expect(screen.getByRole('radio', { name: /SQLite/i })).toBeInTheDocument();
  });

  test('TC-CPDM-002: 選択理由が10文字未満でエラー', async () => {
    const user = userEvent.setup();

    render(
      <ChoicePointDecideModal
        choicePoint={mockChoicePoint}
        isOpen={true}
        onClose={vi.fn()}
        onDecide={vi.fn()}
      />
    );

    await user.click(screen.getByRole('radio', { name: /PostgreSQL/i }));
    await user.type(screen.getByPlaceholderText(/理由/i), '短い');
    await user.click(screen.getByRole('button', { name: /決定を確定/i }));

    expect(screen.getByText(/10文字以上/i)).toBeInTheDocument();
  });

  test('TC-CPDM-003: 有効な入力でAPIが呼ばれる', async () => {
    const user = userEvent.setup();
    const onDecide = vi.fn().mockResolvedValue(undefined);

    render(
      <ChoicePointDecideModal
        choicePoint={mockChoicePoint}
        isOpen={true}
        onClose={vi.fn()}
        onDecide={onDecide}
      />
    );

    await user.click(screen.getByRole('radio', { name: /PostgreSQL/i }));
    await user.type(
      screen.getByPlaceholderText(/理由/i),
      'PostgreSQLは信頼性が高く、本番運用に適している'
    );
    await user.click(screen.getByRole('button', { name: /決定を確定/i }));

    expect(onDecide).toHaveBeenCalledWith({
      selected_choice_id: 'c-1',
      decision_rationale: 'PostgreSQLは信頼性が高く、本番運用に適している',
      rejection_reasons: {},
    });
  });
});
```

---

### 2.4 Memory Lifecycle Page

#### 2.4.1 MemoryStatusCard.test.tsx

```typescript
describe('MemoryStatusCard', () => {
  const mockStatus: MemoryStatus = {
    user_id: 'hiroki',
    total_memories: 1550,
    active_memories: 1200,
    compressed_memories: 300,
    expired_memories: 50,
    memory_usage_mb: 150,
    capacity_limit_mb: 200,
    usage_percentage: 75,
    last_cleanup_at: '2026-01-02T15:00:00Z',
    next_cleanup_at: '2026-01-03T15:00:00Z',
  };

  test('TC-MSC-001: メモリ統計が正しく表示される', () => {
    render(<MemoryStatusCard status={mockStatus} />);

    expect(screen.getByText('1,200')).toBeInTheDocument(); // active
    expect(screen.getByText('300')).toBeInTheDocument();   // compressed
    expect(screen.getByText('50')).toBeInTheDocument();    // expired
  });

  test('TC-MSC-002: 使用率バーが正しく表示される', () => {
    render(<MemoryStatusCard status={mockStatus} />);

    expect(screen.getByText('75%')).toBeInTheDocument();
    const usageBar = screen.getByTestId('usage-bar');
    expect(usageBar).toHaveStyle({ width: '75%' });
  });

  test('TC-MSC-003: 80%以上で警告色になる', () => {
    const highUsageStatus = { ...mockStatus, usage_percentage: 85 };
    render(<MemoryStatusCard status={highUsageStatus} />);

    const usageBar = screen.getByTestId('usage-bar');
    expect(usageBar).toHaveClass('bg-orange-500');
  });

  test('TC-MSC-004: 95%以上でエラー色になる', () => {
    const criticalUsageStatus = { ...mockStatus, usage_percentage: 98 };
    render(<MemoryStatusCard status={criticalUsageStatus} />);

    const usageBar = screen.getByTestId('usage-bar');
    expect(usageBar).toHaveClass('bg-red-500');
  });
});
```

#### 2.4.2 CompressionButton.test.tsx

```typescript
describe('CompressionButton', () => {
  test('TC-CB-001: クリックで圧縮実行', async () => {
    const user = userEvent.setup();
    const onCompress = vi.fn().mockResolvedValue({
      compressed_count: 50,
      space_saved_mb: 10,
    });

    render(<CompressionButton onCompress={onCompress} />);

    await user.click(screen.getByRole('button', { name: /圧縮/i }));

    expect(onCompress).toHaveBeenCalled();
  });

  test('TC-CB-002: 実行中はローディング表示', async () => {
    const onCompress = vi.fn().mockImplementation(
      () => new Promise(() => {}) // never resolves
    );

    render(<CompressionButton onCompress={onCompress} />);

    await userEvent.click(screen.getByRole('button', { name: /圧縮/i }));

    expect(screen.getByText(/処理中/i)).toBeInTheDocument();
  });

  test('TC-CB-003: 成功後に結果表示', async () => {
    const user = userEvent.setup();
    const onCompress = vi.fn().mockResolvedValue({
      compressed_count: 50,
      space_saved_mb: 10,
    });

    render(<CompressionButton onCompress={onCompress} />);

    await user.click(screen.getByRole('button', { name: /圧縮/i }));

    await waitFor(() => {
      expect(screen.getByText(/50件を圧縮/i)).toBeInTheDocument();
    });
  });
});
```

---

### 2.5 Term Drift Detection UI

#### 2.5.1 TermDriftItem.test.tsx

```typescript
describe('TermDriftItem', () => {
  const mockDrift: TermDrift = {
    id: 'td-1',
    user_id: 'hiroki',
    term_name: 'Intent',
    original_definition_id: 'def-1',
    new_definition_id: 'def-2',
    drift_type: 'semantic_shift',
    confidence_score: 0.78,
    change_summary: 'Intentの定義が拡張されました',
    impact_analysis: {
      affected_instances: 3,
      migration_needed: true,
    },
    status: 'pending',
    detected_at: '2026-01-03T10:00:00Z',
  };

  test('TC-TDI-001: ドリフト情報が表示される', () => {
    render(<TermDriftItem drift={mockDrift} />);

    expect(screen.getByText('Intent')).toBeInTheDocument();
    expect(screen.getByText('semantic_shift')).toBeInTheDocument();
    expect(screen.getByText('78%')).toBeInTheDocument();
  });

  test('TC-TDI-002: 影響分析が表示される', () => {
    render(<TermDriftItem drift={mockDrift} />);

    expect(screen.getByText(/3つのインスタンスに影響/i)).toBeInTheDocument();
  });

  test('TC-TDI-003: ドリフトタイプ別の色分け', () => {
    render(<TermDriftItem drift={mockDrift} />);

    const typeBadge = screen.getByTestId('drift-type-badge');
    expect(typeBadge).toHaveClass('bg-purple-100'); // semantic_shift
  });

  test('TC-TDI-004: 解決ボタンでモーダル表示', async () => {
    const user = userEvent.setup();

    render(<TermDriftItem drift={mockDrift} />);

    await user.click(screen.getByRole('button', { name: /解決/i }));

    expect(screen.getByText('ドリフトの解決')).toBeInTheDocument();
  });
});
```

#### 2.5.2 TermAnalyzeForm.test.tsx

```typescript
describe('TermAnalyzeForm', () => {
  test('TC-TAF-001: テキスト入力と分析ボタンが表示される', () => {
    render(<TermAnalyzeForm onAnalyze={vi.fn()} />);

    expect(screen.getByPlaceholderText(/テキストを入力/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /分析/i })).toBeInTheDocument();
  });

  test('TC-TAF-002: 分析実行でAPIが呼ばれる', async () => {
    const user = userEvent.setup();
    const onAnalyze = vi.fn().mockResolvedValue({
      analyzed_terms: 3,
      drifts_detected: 1,
      results: [],
    });

    render(<TermAnalyzeForm onAnalyze={onAnalyze} />);

    await user.type(
      screen.getByPlaceholderText(/テキストを入力/i),
      'Intentは重要なオブジェクトです'
    );
    await user.selectOptions(screen.getByRole('combobox'), 'document');
    await user.click(screen.getByRole('button', { name: /分析/i }));

    expect(onAnalyze).toHaveBeenCalledWith({
      user_id: expect.any(String),
      text: 'Intentは重要なオブジェクトです',
      source: 'document',
    });
  });

  test('TC-TAF-003: 空テキストでは分析不可', async () => {
    const user = userEvent.setup();

    render(<TermAnalyzeForm onAnalyze={vi.fn()} />);

    const analyzeButton = screen.getByRole('button', { name: /分析/i });

    expect(analyzeButton).toBeDisabled();
  });
});
```

---

### 2.6 Temporal Constraint UI

#### 2.6.1 ConstraintCheckForm.test.tsx

```typescript
describe('ConstraintCheckForm', () => {
  test('TC-CCF-001: フォーム要素が正しく表示される', () => {
    render(<ConstraintCheckForm onCheck={vi.fn()} />);

    expect(screen.getByPlaceholderText(/ファイルパス/i)).toBeInTheDocument();
    expect(screen.getByRole('radio', { name: /edit/i })).toBeInTheDocument();
    expect(screen.getByRole('radio', { name: /delete/i })).toBeInTheDocument();
    expect(screen.getByRole('radio', { name: /rename/i })).toBeInTheDocument();
  });

  test('TC-CCF-002: チェック実行でAPIが呼ばれる', async () => {
    const user = userEvent.setup();
    const onCheck = vi.fn().mockResolvedValue({
      check_result: 'approved',
      constraint_level: 'medium',
    });

    render(<ConstraintCheckForm onCheck={onCheck} />);

    await user.type(
      screen.getByPlaceholderText(/ファイルパス/i),
      '/app/services/memory/service.py'
    );
    await user.click(screen.getByRole('radio', { name: /edit/i }));
    await user.type(
      screen.getByPlaceholderText(/変更理由/i),
      'バグ修正のため'
    );
    await user.click(screen.getByRole('button', { name: /チェック/i }));

    expect(onCheck).toHaveBeenCalledWith({
      user_id: expect.any(String),
      file_path: '/app/services/memory/service.py',
      modification_type: 'edit',
      modification_reason: 'バグ修正のため',
      requested_by: 'user',
    });
  });

  test('TC-CCF-003: 結果が色分け表示される', async () => {
    const onCheck = vi.fn().mockResolvedValue({
      check_result: 'approved',
      constraint_level: 'medium',
      warning_message: 'テスト実行を推奨',
    });

    render(<ConstraintCheckForm onCheck={onCheck} />);

    // ... form submission

    await waitFor(() => {
      expect(screen.getByText('approved')).toHaveClass('text-green-600');
      expect(screen.getByText('MEDIUM')).toHaveClass('bg-yellow-100');
    });
  });
});
```

#### 2.6.2 VerificationRegisterForm.test.tsx

```typescript
describe('VerificationRegisterForm', () => {
  test('TC-VRF-001: 検証登録フォームが表示される', () => {
    render(<VerificationRegisterForm onRegister={vi.fn()} />);

    expect(screen.getByPlaceholderText(/ファイルパス/i)).toBeInTheDocument();
    expect(screen.getByRole('combobox', { name: /検証タイプ/i })).toBeInTheDocument();
    expect(screen.getByRole('combobox', { name: /制約レベル/i })).toBeInTheDocument();
  });

  test('TC-VRF-002: 登録実行でAPIが呼ばれる', async () => {
    const user = userEvent.setup();
    const onRegister = vi.fn().mockResolvedValue({
      status: 'registered',
      verification_id: 'v-1',
    });

    render(<VerificationRegisterForm onRegister={onRegister} />);

    await user.type(
      screen.getByPlaceholderText(/ファイルパス/i),
      '/app/core/engine.py'
    );
    await user.selectOptions(
      screen.getByRole('combobox', { name: /検証タイプ/i }),
      'unit_test'
    );
    await user.selectOptions(
      screen.getByRole('combobox', { name: /制約レベル/i }),
      'high'
    );
    await user.click(screen.getByRole('button', { name: /登録/i }));

    expect(onRegister).toHaveBeenCalled();
  });
});
```

---

### 2.7 File Modification UI

#### 2.7.1 FileOperationForm.test.tsx

```typescript
describe('FileOperationForm', () => {
  test('TC-FOF-001: 操作タイプ切り替えでフォームが変化', async () => {
    const user = userEvent.setup();

    render(<FileOperationForm onSubmit={vi.fn()} />);

    // write選択時: コンテンツ入力欄表示
    await user.click(screen.getByRole('radio', { name: /write/i }));
    expect(screen.getByPlaceholderText(/コンテンツ/i)).toBeInTheDocument();

    // rename選択時: 新しいパス入力欄表示
    await user.click(screen.getByRole('radio', { name: /rename/i }));
    expect(screen.getByPlaceholderText(/新しいパス/i)).toBeInTheDocument();

    // delete選択時: 確認チェックボックス表示
    await user.click(screen.getByRole('radio', { name: /delete/i }));
    expect(screen.getByRole('checkbox', { name: /削除を確認/i })).toBeInTheDocument();
  });

  test('TC-FOF-002: 制約レベルに応じた理由文字数の検証', async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();

    // HIGH制約: 50文字以上必要
    render(
      <FileOperationForm
        onSubmit={onSubmit}
        constraintLevel="high"
      />
    );

    await user.type(screen.getByPlaceholderText(/理由/i), 'これは短い理由');
    await user.click(screen.getByRole('button', { name: /実行/i }));

    expect(screen.getByText(/50文字以上/i)).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  test('TC-FOF-003: CRITICAL制約でブロック表示', () => {
    render(
      <FileOperationForm
        onSubmit={vi.fn()}
        constraintLevel="critical"
      />
    );

    expect(screen.getByText(/手動承認が必要/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /実行/i })).toBeDisabled();
  });

  test('TC-FOF-004: 制約チェックボタンの動作', async () => {
    const user = userEvent.setup();
    const onCheck = vi.fn().mockResolvedValue({
      can_proceed: true,
      constraint_level: 'medium',
      min_reason_length: 20,
    });

    render(
      <FileOperationForm
        onSubmit={vi.fn()}
        onCheck={onCheck}
      />
    );

    await user.type(
      screen.getByPlaceholderText(/ファイルパス/i),
      '/app/config.py'
    );
    await user.click(screen.getByRole('button', { name: /制約チェック/i }));

    expect(onCheck).toHaveBeenCalled();
    await waitFor(() => {
      expect(screen.getByText('MEDIUM')).toBeInTheDocument();
    });
  });
});
```

#### 2.7.2 OperationLogTable.test.tsx

```typescript
describe('OperationLogTable', () => {
  const mockLogs: OperationLogsResult = {
    total: 2,
    logs: [
      {
        id: 'log-1',
        user_id: 'hiroki',
        file_path: '/app/config.py',
        operation: 'write',
        reason: '設定更新',
        requested_by: 'user',
        constraint_level: 'medium',
        result: 'approved',
        backup_path: '/backup/config.py.bak',
        created_at: '2026-01-03T10:00:00Z',
      },
      {
        id: 'log-2',
        user_id: 'hiroki',
        file_path: '/app/core/engine.py',
        operation: 'write',
        reason: '理由が短い',
        requested_by: 'ai_agent',
        constraint_level: 'high',
        result: 'rejected',
        backup_path: null,
        created_at: '2026-01-03T09:00:00Z',
      },
    ],
  };

  test('TC-OLT-001: ログ一覧が表示される', () => {
    render(<OperationLogTable logs={mockLogs} />);

    expect(screen.getByText('/app/config.py')).toBeInTheDocument();
    expect(screen.getByText('/app/core/engine.py')).toBeInTheDocument();
  });

  test('TC-OLT-002: 結果が色分け表示される', () => {
    render(<OperationLogTable logs={mockLogs} />);

    const approvedBadge = screen.getByTestId('result-badge-log-1');
    expect(approvedBadge).toHaveClass('bg-green-100');

    const rejectedBadge = screen.getByTestId('result-badge-log-2');
    expect(rejectedBadge).toHaveClass('bg-red-100');
  });

  test('TC-OLT-003: フィルター機能が動作する', async () => {
    const user = userEvent.setup();
    const onFilter = vi.fn();

    render(<OperationLogTable logs={mockLogs} onFilter={onFilter} />);

    await user.selectOptions(
      screen.getByRole('combobox', { name: /result/i }),
      'rejected'
    );

    expect(onFilter).toHaveBeenCalledWith({ result: 'rejected' });
  });
});
```

---

## 3. 統合テスト仕様

### 3.1 API統合テスト（MSW使用）

#### 3.1.1 handlers.ts

```typescript
import { http, HttpResponse } from 'msw';

export const handlers = [
  // Contradiction API
  http.get('/api/v1/contradiction/pending', () => {
    return HttpResponse.json({
      contradictions: [mockContradiction],
      count: 1,
    });
  }),

  http.put('/api/v1/contradiction/:id/resolve', async ({ request }) => {
    const body = await request.json();
    return HttpResponse.json({
      status: 'resolved',
      contradiction_id: 'test-id-1',
      resolution_action: body.resolution_action,
    });
  }),

  // Dashboard API
  http.get('/api/v1/dashboard/overview', () => {
    return HttpResponse.json(mockSystemOverview);
  }),

  http.get('/api/v1/dashboard/timeline', ({ request }) => {
    const url = new URL(request.url);
    const granularity = url.searchParams.get('granularity') || 'hour';
    return HttpResponse.json({
      ...mockTimeline,
      granularity,
    });
  }),

  // Term Drift API
  http.get('/api/v1/term-drift/pending', () => {
    return HttpResponse.json([mockTermDrift]);
  }),

  http.post('/api/v1/term-drift/analyze', async ({ request }) => {
    const body = await request.json();
    return HttpResponse.json({
      analyzed_terms: 2,
      drifts_detected: 1,
      results: [
        { term_name: 'Intent', definition_id: 'def-1', drift_detected: true },
        { term_name: 'Memory', definition_id: 'def-2', drift_detected: false },
      ],
    });
  }),

  // File Modification API
  http.post('/api/v1/files/write', async ({ request }) => {
    const body = await request.json();
    if (body.reason.length < 20 && body.constraint_level === 'medium') {
      return HttpResponse.json(
        { detail: '20文字以上の理由が必要です' },
        { status: 400 }
      );
    }
    return HttpResponse.json({
      success: true,
      operation: 'write',
      file_path: body.file_path,
      message: 'ファイルを書き込みました',
      constraint_level: 'medium',
      check_result: 'approved',
      backup_path: '/backup/file.bak',
      timestamp: new Date().toISOString(),
    });
  }),
];
```

#### 3.1.2 統合テスト例

```typescript
describe('Contradiction Page Integration', () => {
  beforeEach(() => {
    server.use(...handlers);
  });

  test('TC-INT-001: 矛盾一覧取得と解決フロー', async () => {
    const user = userEvent.setup();

    render(
      <QueryClientProvider client={queryClient}>
        <ContradictionsPage />
      </QueryClientProvider>
    );

    // 一覧表示を待機
    await waitFor(() => {
      expect(screen.getByText('tech_stack')).toBeInTheDocument();
    });

    // 解決ボタンクリック
    await user.click(screen.getByRole('button', { name: /解決/i }));

    // モーダル表示確認
    expect(screen.getByText('矛盾の解決')).toBeInTheDocument();

    // 解決アクション選択
    await user.click(screen.getByLabelText(/policy_change/i));
    await user.type(
      screen.getByPlaceholderText(/解決根拠/i),
      'PostgreSQLへの移行を正式に決定したため'
    );
    await user.click(screen.getByRole('button', { name: /解決を確定/i }));

    // 成功メッセージ
    await waitFor(() => {
      expect(screen.getByText(/解決しました/i)).toBeInTheDocument();
    });
  });
});
```

---

## 4. E2Eテスト仕様（Playwright）

### 4.1 テストシナリオ一覧

| ID | シナリオ | 優先度 |
|----|---------|--------|
| E2E-001 | 矛盾検出→解決フロー | 高 |
| E2E-002 | ダッシュボード表示 | 高 |
| E2E-003 | 選択肢作成→決定フロー | 高 |
| E2E-004 | メモリ圧縮実行 | 中 |
| E2E-005 | Term Drift分析→解決 | 中 |
| E2E-006 | ファイル書き込み（制約チェック付き） | 高 |
| E2E-007 | ナビゲーション遷移 | 高 |

### 4.2 E2Eテスト実装例

```typescript
// e2e/contradiction-resolve.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Contradiction Resolution', () => {
  test('E2E-001: 矛盾を検出して解決する', async ({ page }) => {
    // 矛盾検出ページへ移動
    await page.goto('/contradictions');

    // 矛盾アイテムが表示されるまで待機
    await expect(page.locator('[data-testid="contradiction-item"]')).toBeVisible();

    // 解決ボタンをクリック
    await page.click('button:has-text("解決")');

    // モーダルが表示される
    await expect(page.locator('[data-testid="resolve-modal"]')).toBeVisible();

    // 解決アクションを選択
    await page.click('label:has-text("policy_change")');

    // 解決根拠を入力
    await page.fill(
      '[placeholder*="解決根拠"]',
      'これは正式なポリシー変更として承認されました'
    );

    // 確定ボタンをクリック
    await page.click('button:has-text("解決を確定")');

    // 成功通知を確認
    await expect(page.locator('[data-testid="toast-success"]')).toBeVisible();

    // モーダルが閉じる
    await expect(page.locator('[data-testid="resolve-modal"]')).not.toBeVisible();
  });
});

// e2e/file-modification.spec.ts
test.describe('File Modification', () => {
  test('E2E-006: ファイル書き込み（制約チェック付き）', async ({ page }) => {
    await page.goto('/files');

    // writeを選択
    await page.click('label:has-text("write")');

    // ファイルパスを入力
    await page.fill('[placeholder*="ファイルパス"]', '/app/config/settings.py');

    // コンテンツを入力
    await page.fill('[placeholder*="コンテンツ"]', '# New configuration\nDEBUG = True');

    // 理由を入力（短すぎる）
    await page.fill('[placeholder*="理由"]', '更新');

    // 制約チェック実行
    await page.click('button:has-text("制約チェック")');

    // 警告が表示される（MEDIUM制約）
    await expect(page.locator('text=20文字以上')).toBeVisible();

    // 理由を長くする
    await page.fill('[placeholder*="理由"]', 'デバッグモードを有効化して開発効率を向上させるための設定変更');

    // 再度制約チェック
    await page.click('button:has-text("制約チェック")');

    // approved表示
    await expect(page.locator('text=approved')).toBeVisible();

    // 実行ボタンをクリック
    await page.click('button:has-text("実行")');

    // 成功メッセージ
    await expect(page.locator('text=ファイルを書き込みました')).toBeVisible();
  });
});
```

---

## 5. テストデータ

### 5.1 フィクスチャファイル

```typescript
// test/fixtures/contradictions.ts
export const mockContradictions: Contradiction[] = [
  {
    id: 'c-1',
    user_id: 'hiroki',
    new_intent_id: 'i-1',
    new_intent_content: 'PostgreSQLを使用する',
    conflicting_intent_id: 'i-2',
    conflicting_intent_content: 'SQLiteを使用する',
    contradiction_type: 'tech_stack',
    confidence_score: 0.85,
    detected_at: '2026-01-03T10:00:00Z',
    details: {},
    resolution_status: 'pending',
    resolution_action: null,
    resolution_rationale: null,
    resolved_at: null,
  },
  // ... more fixtures
];

// test/fixtures/termDrifts.ts
export const mockTermDrifts: TermDrift[] = [
  {
    id: 'td-1',
    user_id: 'hiroki',
    term_name: 'Intent',
    original_definition_id: 'def-1',
    new_definition_id: 'def-2',
    drift_type: 'semantic_shift',
    confidence_score: 0.78,
    change_summary: 'Intentの定義が拡張されました',
    impact_analysis: {
      affected_instances: 3,
      migration_needed: true,
    },
    status: 'pending',
    detected_at: '2026-01-03T10:00:00Z',
  },
];
```

---

## 6. テストカバレッジ目標

| コンポーネントカテゴリ | 目標カバレッジ |
|----------------------|--------------|
| 新規ページコンポーネント | 80% |
| 新規フォームコンポーネント | 90% |
| 新規モーダルコンポーネント | 85% |
| API統合関数 | 95% |
| 共通コンポーネント | 85% |

---

## 7. テスト実行コマンド

```bash
# 単体テスト
npm run test

# 単体テスト（カバレッジ付き）
npm run test:coverage

# 統合テスト
npm run test:integration

# E2Eテスト
npm run test:e2e

# 全テスト
npm run test:all
```

---

## 8. CI/CD統合

```yaml
# .github/workflows/frontend-test.yml
name: Frontend Tests

on:
  push:
    paths:
      - 'frontend/**'
  pull_request:
    paths:
      - 'frontend/**'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install dependencies
        working-directory: frontend
        run: npm ci

      - name: Run unit tests
        working-directory: frontend
        run: npm run test:coverage

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          directory: frontend/coverage

  e2e:
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install Playwright
        run: npx playwright install --with-deps

      - name: Run E2E tests
        working-directory: frontend
        run: npm run test:e2e
```

---

## 9. 受け入れ基準

### 9.1 機能テスト合格基準

- [ ] 全単体テストがパス
- [ ] カバレッジ目標達成
- [ ] 全E2Eシナリオがパス
- [ ] エラーハンドリングテストがパス

### 9.2 性能基準

- [ ] ページ初期ロード: 3秒以内
- [ ] API応答表示: 500ms以内
- [ ] モーダル表示: 100ms以内

### 9.3 アクセシビリティ基準

- [ ] キーボードナビゲーション対応
- [ ] スクリーンリーダー対応
- [ ] 色コントラスト比 4.5:1以上

---

**作成者**: Resonant Engine Team
**レビュー**: カナ（テスト設計監査）

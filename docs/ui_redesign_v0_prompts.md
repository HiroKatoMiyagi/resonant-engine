# Resonant Engine UI Redesign - v0 Prompts for Product Launch

## Design Philosophy

**目標**: AI開発支援ツールとして、Kiro CLIやCursor、GitHub Copilotと差別化できるプロフェッショナルなUI

**差別化ポイント**:
- 三層AI構造の可視化（Yuno → Kana → Tsumu）
- 開発の意図（Intent）を中心としたワークフロー
- 矛盾検出・選択保存などのインテリジェント機能の体験
- 時間軸を考慮した開発プロセスの可視化

---

## 1. Landing Dashboard

```
Create a modern, professional dashboard for an AI-powered development tool.

The tool uses a three-layer AI architecture:
- Yuno (Strategic thinking layer)
- Kana (Translation/orchestration layer)  
- Tsumu (Implementation layer)

Dashboard sections:
1. Hero metrics row:
   - Active Intents (number with trend)
   - System Health Score (0-100 with gauge)
   - Contradictions Detected (alert count)
   - Completed Tasks (today)

2. Intent Timeline (center):
   - Horizontal timeline showing recent intents
   - Each intent card displays: title, status badge, AI layer involved
   - Click to expand details
   - Visual flow showing progression through AI layers

3. Quick Actions sidebar:
   - "Create Intent" button (primary CTA)
   - "Review Contradictions" 
   - "View Memory"
   - "Export Report"

4. Activity Feed (right):
   - Real-time log of system activities
   - Formatted timestamps
   - Color-coded by event type

Design:
- Use shadcn/ui components
- Modern SaaS aesthetic (think Linear, Vercel, or Supabase)
- Glassmorphism or subtle gradients for depth
- Dark mode ready
- Responsive grid layout
```

## 2. Intent Detail View

```
Create a detailed view for a development intent in an AI orchestration system.

Header:
- Intent ID (monospace, copyable)
- Intent type badge (Feature Request, Bug Fix, Architecture Decision)
- Status with progress indicator
- Created/Updated timestamps
- Source indicator (which AI layer initiated)

Main Content (tabs):

Tab 1: Overview
- Intent description/goal
- AI layer journey visualization:
  * Yuno → Philosophy & reasoning
  * Kana → Translation & specs
  * Tsumu → Implementation code
- Progress bar through 6-stage breathing cycle:
  1. Inhale (Intent creation)
  2. Resonance (AI processing)
  3. Structure (Specification)
  4. Reflect (Review)
  5. Implement (Code generation)
  6. Expand (Integration)

Tab 2: Corrections History
- Timeline of modifications
- Each correction shows: timestamp, which AI made it, reason, diff preview
- Expandable details with before/after comparison

Tab 3: Choice Points
- Decision tree visualization
- Selected option highlighted
- Alternative options shown with rejection reasons
- "Why this was chosen" explanations

Tab 4: Related Context
- Connected intents (graph view)
- Memory references
- Code files affected

Design:
- Clean, spacious layout
- Code syntax highlighting for diffs
- Visual timeline/flowchart elements
- shadcn/ui tabs, cards, code blocks
```

## 3. Contradiction Detection Panel

```
Create an intelligent alert system for detecting development contradictions.

Header:
- "Intelligent Contradiction Detection" title
- Filter controls: Type, Severity, Status
- "Detection Settings" button

Contradiction Cards (stacked vertically):

Each card shows:
- Severity indicator (visual weight: Low → Critical)
- Contradiction type icon & label:
  * Tech Stack Conflict (when switching technologies)
  * Policy Shift (architectural decisions changed)
  * Duplicate Work (similar intents detected)
  * Unverified Assumption (dogma detected)
- Description with highlighted keywords
- Affected intents (clickable links)
- Detected timestamp
- Action buttons: "Review Details", "Mark Resolved", "Create Discussion"

Detail Modal (when clicking card):
- Full context explanation
- Side-by-side comparison of conflicting intents
- AI reasoning for why this was flagged
- Resolution suggestions
- Comment thread for team discussion

Design:
- Progressive disclosure (summary → detail)
- Visual hierarchy by severity (not just color - size, shadow, border)
- Smooth animations when expanding
- Empty state: "No contradictions detected - system is coherent"
- Modern alert design (think GitHub Issues, Linear)
```

## 4. Memory Explorer

```
Create a memory visualization interface for an AI development system.

Layout:

Left Sidebar (filters):
- Memory Type dropdown (Working, Long-term)
- Source Type (Intent, Thought, Decision, Code)
- Date range picker
- Search input (semantic search)

Main Area:

Memory Cards Grid:
Each card:
- Memory content preview (truncated)
- Metadata badges: type, source, creation date
- Importance score indicator (1-10 stars or gauge)
- Related intents count
- "View Details" button

Detail View (modal or side panel):
- Full memory content
- Vector embedding visualization (t-SNE or similar 2D projection)
- Related memories (similarity-based)
- Usage history: "Referenced in X intents"
- Lifecycle info: compression status, archive date
- Edit/Archive/Delete actions

Analytics Panel (top):
- Memory usage gauge (current / capacity)
- Type distribution pie chart
- Compression efficiency over time (line chart)
- Most referenced memories (leaderboard)

Design:
- Data-dense but not cluttered
- Chart.js or Recharts for visualizations
- Masonry grid or standard grid for cards
- Smooth filters with instant search
- Modern data dashboard aesthetic
```

## 5. Three-Layer AI Workflow Visualizer

```
Create an interactive workflow visualization showing how three AI agents collaborate.

Architecture Diagram (animated):

Layer 1 - YUNO (top, purple/blue gradient):
- Icon: brain or lightbulb
- Label: "Strategic Thinking"
- Current activity indicator
- Tasks: "Why are we building this?", "What's the philosophy?"

↓ (animated flow line)

Layer 2 - KANA (middle, green/teal):
- Icon: bridge or translator
- Label: "Translation & Orchestration"
- Processing status
- Tasks: "How do we build it?", "What are the specs?"

↓ (animated flow line)

Layer 3 - TSUMU (bottom, orange/red):
- Icon: code brackets or hammer
- Label: "Implementation"
- Build status
- Tasks: "Generating code", "Running tests"

Features:
- Click each layer to see current processing queue
- Hover to see layer description
- Real-time pulse animation on active layer
- Message passing visualization (particles flowing between layers)
- Expandable detail panels for each layer

Side Panel (right):
- Current intent being processed
- Stage in breathing cycle
- Layer responsibilities breakdown
- Performance metrics per layer

Design:
- Vertical flow diagram
- Glassmorphic layer cards
- Subtle animations (particles, glow effects)
- Modern tech visualization style
- Dark mode optimized
```

## 6. Navigation & Layout

```
Create a modern SaaS application layout with sidebar navigation.

Sidebar (collapsible):
- Logo/brand "Resonant Engine"
- Navigation items with icons:
  * Dashboard (home)
  * Intents (list)
  * Memory (brain)
  * Contradictions (alert-triangle)
  * Analytics (chart)
  * Settings (gear)
- User profile at bottom
- Workspace switcher (for multi-project support)
- Keyboard shortcuts hint

Top Bar:
- Breadcrumb navigation
- Global search (Command+K style)
- Notifications bell with badge
- System health indicator (green/yellow/red dot)
- User avatar with dropdown

Main Content:
- Page header with title + actions
- Content area with proper spacing
- Toast notifications for system events

Footer:
- System version
- Status page link
- Documentation link
- Feedback button

Design:
- Vercel or Linear-inspired navigation
- Smooth transitions
- Command palette (Cmd+K) for power users
- Responsive (mobile-friendly)
- Keyboard navigation support
```

---

## Design System Specifications

### Color Palette

```typescript
export const colors = {
  // Brand
  primary: '#3B82F6',      // blue-500
  secondary: '#8B5CF6',    // purple-500
  accent: '#10B981',       // emerald-500
  
  // AI Layers
  yuno: '#8B5CF6',         // purple (strategic)
  kana: '#10B981',         // emerald (translation)
  tsumu: '#F59E0B',        // amber (implementation)
  
  // Status
  success: '#10B981',
  warning: '#F59E0B',
  error: '#EF4444',
  info: '#3B82F6',
  
  // Severity (contradictions)
  low: '#60A5FA',
  medium: '#FBBF24',
  high: '#FB923C',
  critical: '#DC2626',
};
```

### Typography

```typescript
export const typography = {
  display: 'Cal Sans, Inter, system-ui',  // Headings
  body: 'Inter, system-ui, sans-serif',   // Body text
  mono: 'JetBrains Mono, monospace',      // Code
};
```

### Spacing & Layout

```typescript
export const spacing = {
  pageMargin: '2rem',
  cardPadding: '1.5rem',
  sectionGap: '3rem',
};

export const breakpoints = {
  mobile: '640px',
  tablet: '768px',
  desktop: '1024px',
  wide: '1280px',
};
```

---

## Component Architecture

```
src/
├── components/
│   ├── dashboard/
│   │   ├── HeroMetrics.tsx         # 4つの主要メトリクス
│   │   ├── IntentTimeline.tsx      # タイムライン
│   │   ├── QuickActions.tsx        # サイドバーアクション
│   │   └── ActivityFeed.tsx        # アクティビティログ
│   ├── intent/
│   │   ├── IntentHeader.tsx
│   │   ├── BreathingCycleProgress.tsx  # 6段階進捗
│   │   ├── AILayerJourney.tsx          # Yuno→Kana→Tsumu可視化
│   │   ├── CorrectionsTimeline.tsx
│   │   └── ChoiceTree.tsx              # 決定ツリー
│   ├── contradiction/
│   │   ├── ContradictionList.tsx
│   │   ├── ContradictionCard.tsx
│   │   └── ContradictionDetail.tsx
│   ├── memory/
│   │   ├── MemoryGrid.tsx
│   │   ├── MemoryCard.tsx
│   │   ├── MemoryAnalytics.tsx
│   │   └── VectorVisualization.tsx     # 埋め込み可視化
│   ├── workflow/
│   │   ├── ThreeLayerDiagram.tsx       # アーキテクチャ図
│   │   └── LayerStatusPanel.tsx
│   └── layout/
│       ├── AppShell.tsx                # メインレイアウト
│       ├── Sidebar.tsx
│       ├── TopBar.tsx
│       └── CommandPalette.tsx          # Cmd+K
├── lib/
│   ├── api.ts                          # API client
│   ├── websocket.ts                    # リアルタイム通信
│   └── theme.ts                        # デザイントークン
└── hooks/
    ├── useIntents.ts
    ├── useContradictions.ts
    ├── useMemory.ts
    └── useRealtimeUpdates.ts           # WebSocket hook
```

---

## API Integration Pattern

```typescript
// lib/api.ts
const API_BASE = 'http://localhost:8000';

// React Query example
export function useIntents() {
  return useQuery({
    queryKey: ['intents'],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/api/v1/intents`);
      return res.json();
    },
    refetchInterval: 5000, // Poll every 5s
  });
}

// WebSocket for real-time updates
export function useRealtimeIntents() {
  const [intents, setIntents] = useState([]);
  
  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws/intents');
    ws.onmessage = (event) => {
      const update = JSON.parse(event.data);
      setIntents(prev => updateIntent(prev, update));
    };
    return () => ws.close();
  }, []);
  
  return intents;
}
```

---

## Implementation Roadmap

### Phase 1: Core Dashboard (Week 1)
- [ ] Landing dashboard with hero metrics
- [ ] Intent timeline
- [ ] Navigation layout
- [ ] API integration setup

### Phase 2: Intent Details (Week 2)
- [ ] Intent detail view with tabs
- [ ] Breathing cycle visualization
- [ ] AI layer journey diagram
- [ ] Corrections timeline

### Phase 3: Intelligence Features (Week 3)
- [ ] Contradiction detection panel
- [ ] Memory explorer
- [ ] Three-layer workflow visualizer
- [ ] Real-time WebSocket updates

### Phase 4: Polish & Production (Week 4)
- [ ] Dark mode
- [ ] Animations & transitions
- [ ] Mobile responsive
- [ ] Performance optimization
- [ ] Documentation

---

## v0.dev Usage Guide

### Step 1: Dashboard Foundation
1. Copy "Landing Dashboard" prompt
2. Paste into v0.dev
3. Generate & preview
4. Refine: "Make the intent timeline more prominent"
5. Download code

### Step 2: Iterate on Details
```
# Example refinement prompts
"Add smooth animations when intent cards appear"
"Make the health gauge more visual with a circular progress"
"Use a gradient background for the hero section"
"Add hover effects to the quick action buttons"
```

### Step 3: Component Integration
```bash
# Install dependencies
cd /Users/zero/Projects/resonant-engine/dashboard/frontend
npm install @tanstack/react-query recharts framer-motion

# Add v0 generated components
# Copy to src/components/

# Connect to API
# Update API endpoints to match backend
```

---

## Competitive Positioning

### vs Kiro CLI
- **Kiro**: Terminal-based, spec-driven
- **Resonant**: Visual dashboard, intent-driven, intelligence features

### vs Cursor/Copilot
- **Cursor**: Code generation focus
- **Resonant**: Full development workflow with multi-AI orchestration

### vs Linear/Notion
- **Linear**: Project management
- **Resonant**: AI-powered development OS with philosophical layer

**Key Differentiator**: "The only development tool that remembers why you made decisions, detects contradictions, and preserves your choices"

---

## Success Metrics for New UI

1. **Time to First Intent**: < 30 seconds from login
2. **Contradiction Detection Rate**: Users act on 60%+ of alerts
3. **Memory Utilization**: Users reference past decisions 3+ times/week
4. **Session Duration**: Average 20+ minutes (vs 5 min for typical dashboards)
5. **NPS**: Target 40+ (developers are harsh critics)

---

**Next Steps**:
1. Start with "Landing Dashboard" in v0.dev
2. Get宏啓's feedback on visual direction
3. Implement in phases
4. A/B test with beta users
5. Gather metrics for product-market fit

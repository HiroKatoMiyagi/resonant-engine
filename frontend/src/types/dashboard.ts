/**
 * Dashboard Analytics API Types
 * バックエンドスキーマに完全一致
 */

export interface SystemOverview {
  total_users: number;
  active_sessions: number;
  total_intents: number;
  completed_intents: number;
  pending_contradictions: number;
  system_health: 'healthy' | 'warning' | 'error';
  uptime_seconds: number;
  memory_usage_mb: number;
  cpu_usage_percent: number;
  last_updated: string;
}

export interface TimelineEntry {
  timestamp: string;
  event_type: string;
  event_data: Record<string, unknown>;
  user_id: string | null;
  intent_id: string | null;
  session_id: string | null;
}

export interface TimelineResponse {
  entries: TimelineEntry[];
  granularity: 'minute' | 'hour' | 'day';
  start_time: string;
  end_time: string;
  total_count: number;
}

export interface Correction {
  id: string;
  correction_type: string;
  original_value: unknown;
  corrected_value: unknown;
  corrected_by: string;
  correction_reason: string;
  corrected_at: string;
  intent_id: string | null;
  user_id: string | null;
}

export interface CorrectionsResponse {
  corrections: Correction[];
  count: number;
}

// Re-evaluation Types
export interface ReEvalRequest {
  intent_id: string;
  diff: Record<string, unknown>;
  source: string;
  reason: string;
}

export interface ReEvalResult {
  intent_id: string;
  status: string;
  result: Record<string, unknown>;
}

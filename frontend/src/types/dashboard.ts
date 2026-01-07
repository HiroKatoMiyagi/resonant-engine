/**
 * Dashboard Analytics API Types
 * バックエンドAPIレスポンスに完全一致
 */

export interface StatusDistribution {
  pending?: number;
  completed?: number;
  in_progress?: number;
  failed?: number;
  [key: string]: number | undefined;
}

export interface RecentActivity {
  last_hour: number;
  last_24h: number;
  last_7d: number;
}

export interface SystemOverview {
  total_intents: number;
  status_distribution: StatusDistribution;
  recent_activity: RecentActivity;
  correction_rate: number;
  avg_processing_time_ms: number;
  active_websockets: number;
}

export interface TimelineEntry {
  time: string;
  count: number;
}

export interface TimelineResponse {
  entries?: TimelineEntry[];
  // Backend returns array directly
}

export interface Correction {
  intent_id: string;
  correction_count: number;
  last_correction: string | null;
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

/**
 * Contradiction Detection API Types
 * バックエンドスキーマに完全一致
 */

export interface ContradictionRequest {
  user_id: string;
  intent_id: string;
  intent_content: string;
}

export interface ResolveContradictionRequest {
  resolution_action: 'policy_change' | 'mistake' | 'coexist';
  resolution_rationale: string;
  resolved_by: string;
}

export interface Contradiction {
  id: string;
  user_id: string;
  new_intent_id: string;
  new_intent_content: string;
  conflicting_intent_id: string | null;
  conflicting_intent_content: string | null;
  contradiction_type: string;
  confidence_score: number;
  detected_at: string;
  details: Record<string, unknown>;
  resolution_status: string;
  resolution_action: string | null;
  resolution_rationale: string | null;
  resolved_at: string | null;
}

export interface ContradictionListResponse {
  contradictions: Contradiction[];
  count: number;
}

export interface ContradictionStats {
  total: number;
  pending: number;
  resolved: number;
  by_type: Record<string, number>;
}

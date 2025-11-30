/**
 * Memory Lifecycle API Types
 * バックエンドスキーマに完全一致
 */

export interface MemoryStatus {
  user_id: string;
  total_memories: number;
  active_memories: number;
  compressed_memories: number;
  expired_memories: number;
  memory_usage_mb: number;
  capacity_limit_mb: number;
  usage_percentage: number;
  last_cleanup_at: string | null;
  next_cleanup_at: string | null;
}

export interface CompressionResult {
  user_id: string;
  compressed_count: number;
  space_saved_mb: number;
  compression_ratio: number;
  compressed_at: string;
}

export interface CleanupResult {
  deleted_count: number;
  space_freed_mb: number;
  cleaned_at: string;
}

// Choice Preservation Types
export interface ChoiceRequest {
  choice_id: string;
  choice_text: string;
}

export interface CreateChoicePointRequest {
  user_id: string;
  question: string;
  choices: ChoiceRequest[];
  tags: string[];
  context_type: string;
}

export interface DecideChoiceRequest {
  selected_choice_id: string;
  decision_rationale: string;
  rejection_reasons: Record<string, string>;
}

export interface ChoicePoint {
  id: string;
  user_id: string;
  question: string;
  choices: ChoiceRequest[];
  tags: string[];
  context_type: string;
  status: 'pending' | 'decided' | 'expired';
  selected_choice_id: string | null;
  decision_rationale: string | null;
  rejection_reasons: Record<string, string>;
  created_at: string;
  decided_at: string | null;
}

export interface ChoicePointListResponse {
  choice_points: ChoicePoint[];
  count: number;
}

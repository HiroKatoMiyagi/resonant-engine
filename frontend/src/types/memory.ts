/**
 * Memory Lifecycle API Types
 * バックエンドスキーマに完全一致
 */

export interface MemoryStatus {
  active_count: number;
  archive_count: number;
  total_count: number;
  usage_ratio: number;
  total_size_bytes: number;
  limit: number;
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
  choice_points?: ChoicePoint[];
  results?: ChoicePoint[];
  count: number;
}

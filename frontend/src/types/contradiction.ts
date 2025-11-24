/**
 * Contradiction型定義
 * 
 * バックエンドのbridge/contradiction/api_schemas.pyと完全一致
 * 変更禁止 - バックエンドスキーマに依存
 */

/**
 * 矛盾タイプ（バックエンドのcontradiction_typeに対応）
 * 変更禁止 - バックエンドのdetector.pyで定義されている値
 */
export type ContradictionType =
  | 'tech_stack'    // 技術スタック矛盾
  | 'policy_shift'  // ポリシー転換
  | 'duplicate'     // 重複作業
  | 'dogma';        // ドグマ（未検証の断定）

/**
 * 解決ステータス
 * 変更禁止 - バックエンドのapi_schemas.pyで定義
 */
export type ResolutionStatus = 'pending' | 'resolved' | 'dismissed';

/**
 * 解決アクション
 * 変更禁止 - バックエンドのapi_schemas.pyで定義
 */
export type ResolutionAction = 'policy_change' | 'mistake' | 'coexist';

/**
 * ContradictionSchema - バックエンドapi_schemas.pyと完全一致
 *
 * IMPORTANT: この型定義はバックエンドのContradictionSchemaと
 * 1対1で対応している。変更してはならない。
 */
export interface Contradiction {
  id: string;                              // UUID形式
  user_id: string;
  new_intent_id: string;                   // UUID形式
  new_intent_content: string;
  conflicting_intent_id: string | null;    // UUID形式
  conflicting_intent_content: string | null;
  contradiction_type: ContradictionType;
  confidence_score: number;                // 0.0-1.0
  detected_at: string;                     // ISO 8601形式
  details: Record<string, unknown>;
  resolution_status: ResolutionStatus;
  resolution_action: ResolutionAction | null;
  resolution_rationale: string | null;
  resolved_at: string | null;              // ISO 8601形式
}

/**
 * 矛盾チェックリクエスト
 */
export interface CheckContradictionRequest {
  user_id: string;
  intent_id: string;       // UUID形式
  intent_content: string;
}

/**
 * 矛盾解決リクエスト
 */
export interface ResolveContradictionRequest {
  resolution_action: ResolutionAction;
  resolution_rationale: string;  // 最低10文字
  resolved_by: string;
}

/**
 * APIレスポンス（一覧取得用）
 */
export interface ContradictionListResponse {
  contradictions: Contradiction[];
  total: number;
}

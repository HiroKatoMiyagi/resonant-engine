/**
 * Contradiction Detection API
 * 
 * Bridge API (/api/v1/) を使用
 * 環境変数からBase URLを取得（ハードコード禁止）
 */

import axios from 'axios';
import type {
  ContradictionListResponse,
  CheckContradictionRequest,
  ResolveContradictionRequest
} from '../types/contradiction';

// API Base URL - 環境変数から取得（ハードコード禁止）
const BRIDGE_API_URL = import.meta.env.VITE_BRIDGE_API_URL || 'http://localhost:8000';

/**
 * 未解決の矛盾一覧を取得
 * 
 * @param userId - ユーザーID
 * @returns 矛盾一覧レスポンス
 */
export async function getPendingContradictions(
  userId: string
): Promise<ContradictionListResponse> {
  const response = await axios.get<ContradictionListResponse>(
    `${BRIDGE_API_URL}/api/v1/contradiction/pending`,
    { params: { user_id: userId } }
  );
  return response.data;
}

/**
 * Intentの矛盾をチェック
 * 
 * @param request - チェックリクエスト
 * @returns 検出された矛盾一覧
 */
export async function checkIntentContradiction(
  request: CheckContradictionRequest
): Promise<ContradictionListResponse> {
  const response = await axios.post<ContradictionListResponse>(
    `${BRIDGE_API_URL}/api/v1/contradiction/check`,
    request
  );
  return response.data;
}

/**
 * 矛盾を解決
 * 
 * @param contradictionId - 矛盾ID（UUID）
 * @param request - 解決リクエスト
 * @returns ステータスレスポンス
 */
export async function resolveContradiction(
  contradictionId: string,
  request: ResolveContradictionRequest
): Promise<{ status: string }> {
  const response = await axios.put<{ status: string }>(
    `${BRIDGE_API_URL}/api/v1/contradiction/${contradictionId}/resolve`,
    request
  );
  return response.data;
}

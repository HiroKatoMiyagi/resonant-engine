/**
 * Contradiction Detection API
 * 矛盾検出機能のAPI関数
 */

import { contradictionsApi } from './client';
import type { ContradictionListResponse, ContradictionRequest, ResolveContradictionRequest } from '../types/contradiction';

/**
 * 未解決の矛盾を取得
 */
export const getPendingContradictions = async (userId: string): Promise<ContradictionListResponse> => {
  const response = await contradictionsApi.getPending(userId);
  return response.data;
};

/**
 * 矛盾をチェック
 */
export const checkContradiction = async (data: ContradictionRequest): Promise<ContradictionListResponse> => {
  const response = await contradictionsApi.check(data);
  return response.data;
};

/**
 * 矛盾を解決
 */
export const resolveContradiction = async (
  contradictionId: string,
  data: ResolveContradictionRequest
): Promise<{ status: string; contradiction_id: string; resolution_action: string }> => {
  const response = await contradictionsApi.resolve(contradictionId, data);
  return response.data;
};

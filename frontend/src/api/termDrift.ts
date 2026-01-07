import api from './client';
import type { TermDrift, TermDriftResolution, AnalyzeRequest, AnalyzeResult } from '../types/termDrift';

export const termDriftApi = {
    getPending: (userId: string, limit: number = 50) =>
        api.get<TermDrift[]>('/v1/term-drift/pending', { params: { user_id: userId, limit } }),

    analyze: (data: AnalyzeRequest) =>
        api.post<AnalyzeResult>('/v1/term-drift/analyze', data),

    resolve: (driftId: string, data: TermDriftResolution) =>
        api.put<{ status: string; drift_id: string }>(`/v1/term-drift/${driftId}/resolve`, data),
};

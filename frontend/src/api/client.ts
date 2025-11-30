import axios from 'axios';
import type {
  MessageListResponse,
  Message,
  SpecificationListResponse,
  Specification,
  IntentListResponse,
  Intent,
  NotificationListResponse,
  Notification,
  // 🆕 Advanced Features Types
  ContradictionRequest,
  ResolveContradictionRequest,
  ContradictionListResponse,
  MemoryStatus,
  CompressionResult,
  CleanupResult,
  CreateChoicePointRequest,
  DecideChoiceRequest,
  ChoicePoint,
  ChoicePointListResponse,
  SystemOverview,
  TimelineResponse,
  CorrectionsResponse,
  ReEvalRequest,
  ReEvalResult,
} from '../types';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  timeout: 10000,
});

export const messagesApi = {
  list: (params?: Record<string, unknown>) =>
    api.get<MessageListResponse>('/messages', { params }),
  get: (id: string) => api.get<Message>(`/messages/${id}`),
  create: (data: { user_id: string; content: string; message_type?: string }) =>
    api.post<Message>('/messages', data),
  update: (id: string, data: { content?: string; metadata?: Record<string, unknown> }) =>
    api.put<Message>(`/messages/${id}`, data),
  delete: (id: string) => api.delete(`/messages/${id}`),
};

export const specificationsApi = {
  list: (params?: Record<string, unknown>) =>
    api.get<SpecificationListResponse>('/specifications', { params }),
  get: (id: string) => api.get<Specification>(`/specifications/${id}`),
  create: (data: { title: string; content: string; status?: string; tags?: string[] }) =>
    api.post<Specification>('/specifications', data),
  update: (id: string, data: Partial<Specification>) =>
    api.put<Specification>(`/specifications/${id}`, data),
  delete: (id: string) => api.delete(`/specifications/${id}`),
};

export const intentsApi = {
  list: (params?: Record<string, unknown>) =>
    api.get<IntentListResponse>('/intents', { params }),
  get: (id: string) => api.get<Intent>(`/intents/${id}`),
  create: (data: { description: string; priority?: number; intent_type?: string }) =>
    api.post<Intent>('/intents', data),
  update: (id: string, data: Partial<Intent>) =>
    api.put<Intent>(`/intents/${id}`, data),
  updateStatus: (id: string, data: { status: string; result?: Record<string, unknown> }) =>
    api.patch<Intent>(`/intents/${id}/status`, data),
  delete: (id: string) => api.delete(`/intents/${id}`),
};

export const notificationsApi = {
  list: (params?: Record<string, unknown>) =>
    api.get<NotificationListResponse>('/notifications', { params }),
  get: (id: string) => api.get<Notification>(`/notifications/${id}`),
  create: (data: { user_id: string; title: string; message?: string; notification_type?: string }) =>
    api.post<Notification>('/notifications', data),
  markRead: (notification_ids: string[]) =>
    api.post('/notifications/mark-read', { notification_ids }),
  delete: (id: string) => api.delete(`/notifications/${id}`),
};

// 🆕 Contradiction Detection API
export const contradictionsApi = {
  getPending: (userId: string) =>
    api.get<ContradictionListResponse>('/v1/contradiction/pending', { params: { user_id: userId } }),
  check: (data: ContradictionRequest) =>
    api.post<ContradictionListResponse>('/v1/contradiction/check', data),
  resolve: (contradictionId: string, data: ResolveContradictionRequest) =>
    api.put<{ status: string; contradiction_id: string; resolution_action: string }>(
      `/v1/contradiction/${contradictionId}/resolve`,
      data
    ),
};

// 🆕 Memory Lifecycle API
export const memoryApi = {
  getStatus: (userId: string) =>
    api.get<MemoryStatus>('/v1/memory/lifecycle/status', { params: { user_id: userId } }),
  compress: (userId: string) =>
    api.post<CompressionResult>('/v1/memory/lifecycle/compress', null, { params: { user_id: userId } }),
  cleanupExpired: () =>
    api.delete<CleanupResult>('/v1/memory/lifecycle/expired'),
};

// 🆕 Choice Preservation API
export const choicePointsApi = {
  getPending: (userId: string) =>
    api.get<ChoicePointListResponse>('/v1/memory/choice-points/pending', { params: { user_id: userId } }),
  create: (data: CreateChoicePointRequest) =>
    api.post<ChoicePoint>('/v1/memory/choice-points/', data),
  decide: (choicePointId: string, data: DecideChoiceRequest) =>
    api.put<ChoicePoint>(`/v1/memory/choice-points/${choicePointId}/decide`, data),
  search: (params: { user_id: string; tags?: string[]; context_type?: string }) =>
    api.get<ChoicePointListResponse>('/v1/memory/choice-points/search', { params }),
};

// 🆕 Dashboard Analytics API
export const dashboardApi = {
  getOverview: () =>
    api.get<SystemOverview>('/v1/dashboard/overview'),
  getTimeline: (granularity: 'minute' | 'hour' | 'day' = 'hour') =>
    api.get<TimelineResponse>('/v1/dashboard/timeline', { params: { granularity } }),
  getCorrections: (limit: number = 50) =>
    api.get<CorrectionsResponse>('/v1/dashboard/corrections', { params: { limit } }),
};

// 🆕 Re-evaluation API
export const reevalApi = {
  reEvaluateIntent: (data: ReEvalRequest) =>
    api.post<ReEvalResult>('/v1/intent/reeval', data),
};

export default api;

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

export default api;

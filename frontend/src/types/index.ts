export interface Message {
  id: string;
  user_id: string;
  content: string;
  message_type: 'user' | 'yuno' | 'kana' | 'system';
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface MessageListResponse {
  items: Message[];
  total: number;
  limit: number;
  offset: number;
}

export interface Specification {
  id: string;
  title: string;
  content: string;
  version: number;
  status: 'draft' | 'review' | 'approved';
  tags: string[];
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface SpecificationListResponse {
  items: Specification[];
  total: number;
  limit: number;
  offset: number;
}

export interface Intent {
  id: string;
  description: string;
  intent_type: string | null;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  priority: number;
  result: Record<string, unknown> | null;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  processed_at: string | null;
}

export interface IntentListResponse {
  items: Intent[];
  total: number;
  limit: number;
  offset: number;
}

export interface Notification {
  id: string;
  user_id: string;
  title: string;
  message: string | null;
  notification_type: 'info' | 'success' | 'warning' | 'error';
  is_read: boolean;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface NotificationListResponse {
  items: Notification[];
  total: number;
  limit: number;
  offset: number;
}

// 🆕 Advanced Features Types
export * from './contradiction';
export * from './memory';
export * from './dashboard';

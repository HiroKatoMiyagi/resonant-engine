export type ConstraintLevel = 'critical' | 'high' | 'medium' | 'low';
export type CheckResult = 'approved' | 'rejected' | 'pending' | 'blocked';
export type Operation = 'write' | 'delete' | 'rename' | 'read';

export interface FileModificationRequest {
    user_id: string;
    file_path: string;
    operation: Operation;
    content?: string;      // write時のみ
    new_path?: string;     // rename時のみ
    reason: string;
    requested_by: string;
    force?: boolean;
}

export interface FileModificationResult {
    success: boolean;
    operation: string;
    file_path: string;
    message: string;
    constraint_level: ConstraintLevel;
    check_result: CheckResult;
    backup_path: string | null;
    file_hash: string | null;
    timestamp: string;
}

export interface FileReadResult {
    success: boolean;
    file_path: string;
    content: string | null;
    file_hash: string | null;
    message: string;
}

export interface ConstraintCheckResult {
    file_path: string;
    constraint_level: string;
    check_result: string;
    can_proceed: boolean;
    warning_message: string | null;
    required_actions: string[];
    questions: string[];
    min_reason_length: number;
    current_reason_length: number;
}

// Log types
export interface OperationLog {
    id: string;
    user_id: string;
    file_path: string;
    operation: string;
    reason: string;
    requested_by: string;
    constraint_level: string;
    result: string;
    backup_path: string | null;
    created_at: string;
}

export interface OperationLogsResult {
    total: number;
    logs: OperationLog[];
}

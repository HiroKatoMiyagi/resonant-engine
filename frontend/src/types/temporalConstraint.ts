export type ConstraintLevel = 'critical' | 'high' | 'medium' | 'low';
export type CheckResult = 'approved' | 'rejected' | 'pending';

export interface FileVerification {
    id: string;
    user_id: string;
    file_path: string;
    file_hash: string | null;
    verification_type: string;
    verification_description: string | null;
    test_hours_invested: number;
    constraint_level: ConstraintLevel;
    verified_at: string;
    stable_since: string | null;
    verified_by: string | null;
}

export interface TemporalConstraintCheck {
    file_path: string;
    constraint_level: ConstraintLevel;
    check_result: CheckResult;
    verification_info: FileVerification | null;
    warning_message: string | null;
    required_actions: string[];
    questions: string[];
}

export interface ModificationRequest {
    user_id: string;
    file_path: string;
    modification_type: 'edit' | 'delete' | 'rename';
    modification_reason: string;
    requested_by: 'user' | 'ai_agent' | 'system'; // 'ai_agent' uses 'ai' in python usually, but here spec says ai_agent in UI type? No, usually matched. Let's use string or literal.
    // Python backend uses `RequestOrigin` enum: user, ai, system.
    // The spec says `requested_by: 'user' | 'ai_agent' | 'system'`. Let's stick to spec but keep in mind backend enum.
}

export interface VerificationRegisterResult {
    status: string;
    verification_id: string;
    file_path: string;
    constraint_level: string;
}

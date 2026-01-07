import api from './client';
import type {
    TemporalConstraintCheck,
    ModificationRequest,
    ConstraintLevel,
    VerificationRegisterResult
} from '../types/temporalConstraint';

export const temporalConstraintApi = {
    check: (data: ModificationRequest) =>
        api.post<TemporalConstraintCheck>('/v1/temporal-constraint/check', data),

    verify: (params: {
        user_id: string;
        file_path: string;
        verification_type: string;
        test_hours?: number;
        constraint_level?: ConstraintLevel;
        description?: string;
        verified_by?: string;
    }) =>
        api.post<VerificationRegisterResult>('/v1/temporal-constraint/verify', null, { params }),

    markStable: (params: { user_id: string; file_path: string }) =>
        api.post<{ status: string; file_path: string }>('/v1/temporal-constraint/mark-stable', null, { params }),

    upgradeCritical: (params: { user_id: string; file_path: string; reason: string }) =>
        api.post<{ status: string; file_path: string }>('/v1/temporal-constraint/upgrade-critical', null, { params }),
};

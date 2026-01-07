import api from './client';
import type {
    FileModificationRequest,
    FileModificationResult,
    FileReadResult,
    ConstraintCheckResult,
    OperationLogsResult
} from '../types/fileModification';

export const fileModificationApi = {
    write: (data: FileModificationRequest) =>
        api.post<FileModificationResult>('/v1/files/write', data),

    delete: (data: FileModificationRequest) =>
        api.post<FileModificationResult>('/v1/files/delete', data),

    rename: (data: FileModificationRequest) =>
        api.post<FileModificationResult>('/v1/files/rename', data),

    read: (params: { user_id: string; file_path: string; requested_by?: string }) =>
        api.get<FileReadResult>('/v1/files/read', { params }),

    check: (data: FileModificationRequest) =>
        api.post<ConstraintCheckResult>('/v1/files/check', data),

    getLogs: (params: {
        user_id: string;
        limit?: number;
        offset?: number;
        operation?: string;
        result?: string;
    }) =>
        api.get<OperationLogsResult>('/v1/files/logs', { params }),
};

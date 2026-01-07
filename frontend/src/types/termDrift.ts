export type TermCategory = 'domain_object' | 'technical' | 'process' | 'custom';
export type DriftType = 'expansion' | 'contraction' | 'semantic_shift' | 'context_change';
export type DriftStatus = 'pending' | 'acknowledged' | 'resolved' | 'dismissed';

export interface TermDefinition {
    id: string;
    user_id: string;
    term_name: string;
    term_category: TermCategory;
    definition_text: string;
    definition_context: string | null;
    definition_source: string | null;
    structured_definition: Record<string, unknown> | null;
    version: number;
    is_current: boolean;
    defined_at: string;
}

export interface TermDrift {
    id: string;
    user_id: string;
    term_name: string;
    original_definition_id: string | null;
    new_definition_id: string | null;
    drift_type: DriftType;
    confidence_score: number;
    change_summary: string;
    impact_analysis: {
        affected_instances: number;
        migration_needed: boolean;
        details?: string;
    } | null;
    status: DriftStatus;
    detected_at: string;
}

export interface TermDriftResolution {
    resolution_action: 'intentional_change' | 'rollback' | 'migration_needed';
    resolution_note: string;  // min 10 chars
    resolved_by: string;
}

export interface AnalyzeRequest {
    user_id: string;
    text: string;
    source: string;
}

export interface AnalyzeResult {
    analyzed_terms: number;
    drifts_detected: number;
    results: {
        term_name: string;
        definition_id: string;
        drift_detected: boolean;
    }[];
}

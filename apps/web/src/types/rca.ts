export interface RcaEvidenceReference {
  evidence_id?: number;
  evidence_key?: string;
  source?: string;
  category?: string;
  strength?: number;
  value?: unknown;
}


export interface RcaFusionOutput {
  rank?: number;
  cause?: string;
  confidence?: number;
  confidence_percent?: number;
  confidence_label?: string;
  support_score?: number;
  contradiction_score?: number;

  supporting_evidence?: RcaEvidenceReference[];
  contradicting_evidence?: RcaEvidenceReference[];

  supporting_evidence_count?: number;
  contradicting_evidence_count?: number;
}


export interface RcaPrediction {
  id: number;
  engine_type: string;
  primary_cause: string | null;
  confidence: number | null;
  rank: number;
  output_json: Record<string, unknown>;
  verifier_status: string | null;
  verifier_reason: string | null;
  created_at: string;
}


export interface NormalizedRcaCase {
  id: number;
  case_uuid: string | null;
  status: string | null;
  scope_type: string | null;
  scope_ref: string | null;
  trigger_type: string | null;
  risk_score: number | null;
  risk_level: string | null;
  baseline_primary_cause: string | null;
  created_at: string | null;
  updated_at: string | null;
  predictions: RcaPrediction[];
}


export interface RcaCaseBundle {
  case: NormalizedRcaCase;

  structured: RcaPrediction | null;
  consensus: RcaPrediction | null;
  fusion: RcaPrediction[];
  llmAudits: RcaPrediction[];

  evidencePacket: unknown | null;
}

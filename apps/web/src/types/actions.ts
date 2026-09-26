export interface ActionSimulationSummary {
  id: number;
  attempt: number;
  status: string;
  simulation_mode: string;
  verification_ready: boolean;
  rollback_ready: boolean;
  execution_allowed: boolean;
}


export interface ActionVerificationSummary {
  id: number;
  status: string;
  rollback_decision: string;
  execution_allowed: boolean;
  integrity_valid: boolean;
}


export interface ActionPlan {
  id: number;
  action_uuid: string;

  rca_case_id: number;
  alert_id: number | null;
  device_id: number | null;

  source_primary_cause: string;
  source_confidence: number | null;
  source_verifier_status: string | null;

  action_code: string;
  action_type: string;

  target_type: string;
  target_ref: string | null;

  title: string;
  description: string;
  rationale: string;

  status: string;
  execution_mode: string;
  safety_gate_status: string;

  requires_human_approval: boolean;
  auto_eligible: boolean;

  risk_level: string;
  blast_radius: string;

  verification_required: boolean;
  rollback_required: boolean;

  parameters_json: Record<string, unknown>;
  preconditions_json: string[];
  safety_checks_json: Record<string, unknown>;
  verification_plan_json: string[];
  rollback_plan_json: string[];

  reviewed_by: string | null;
  review_reason: string | null;
  reviewed_at: string | null;

  approved_for_simulation_at: string | null;

  rejected_at: string | null;
  blocked_at: string | null;
  status_updated_at: string | null;

  planner_version: string;
  schema_version: string;

  created_at: string;
  updated_at: string;

  latest_simulation: ActionSimulationSummary | null;
  latest_verification: ActionVerificationSummary | null;
}

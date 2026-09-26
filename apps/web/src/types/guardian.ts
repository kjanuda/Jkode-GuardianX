export interface DashboardOverview {
  schema_version: string;
  generated_at: string;

  network: {
    total_devices: number;
    devices_with_active_alerts: number;
    devices_without_active_alerts: number;
    active_alert_device_ratio: number;
  };

  alerts: {
    total: number;
    active: number;
    critical: number;
    high: number;
    by_status: Record<string, number>;
    by_severity: Record<string, number>;
  };

  rca: {
    total_cases: number;
    by_status: Record<string, number>;
    predictions_by_engine: Record<string, number>;
    verified_structured_predictions: number;
    rejected_structured_predictions: number;
  };

  actions: {
    total: number;
    by_status: Record<string, number>;
    execution_modes: Record<string, number>;
    auto_eligible: number;
    requires_human_approval: number;
  };

  feedback: {
    total: number;
    by_status: Record<string, number>;
    quality_gates: Record<string, number>;
    training_eligible: number;
  };

  recent_incidents: unknown[];

  safety: {
    execution_mode: string;
    real_network_execution_enabled: boolean;
    auto_execution_enabled: boolean;
    human_approval_required: boolean;
    auto_eligible_action_count: number;
    human_approval_action_count: number;
  };
}


export interface DashboardIncident {
  incident_id: string;
  incident_status: string;

  case: {
    id: number;
    uuid: string;
    status: string;
    scope_type: string;
    scope_ref: string;
    trigger_type: string;
    created_at: string;
    updated_at: string;
  };

  device: {
    internal_id: number | null;
    external_id: string | null;
  };

  risk: {
    score: number | null;
    level: string | null;
    severity: string | null;
  };

  alert: {
    id: number;
    status: string;
    title: string;
    summary: string;
    severity: string;
    risk_score: number;
    primary_cause: string;
    occurrence_count: number;
    reopened_count: number;
    first_seen_at: string;
    last_seen_at: string;
    resolved_at: string | null;
  } | null;

  diagnosis: {
    prediction_id: number | null;
    engine: string | null;
    primary_cause: string;
    confidence: number | null;
    verifier_status: string | null;
    verified: boolean;
  };

  action: {
    id: number;
    uuid: string;
    status: string;
    action_code: string;
    action_type: string;
    title: string;
    target_type: string;
    target_ref: string | null;
    risk_level: string;
    blast_radius: string;
    execution_mode: string;
    safety_gate_status: string;
    requires_human_approval: boolean;
    auto_eligible: boolean;
    reviewed_by: string | null;
    reviewed_at: string | null;
  } | null;

  simulation: {
    id: number;
    attempt: number;
    status: string;
    mode: string;
    verification_ready: boolean;
    rollback_ready: boolean;
    execution_allowed: boolean;
    finished_at: string | null;
  } | null;

  verification: {
    id: number;
    status: string;
    verification_type: string;
    rollback_decision: string;
    execution_allowed: boolean;
    verified_at: string | null;
  } | null;

  feedback: {
    id: number;
    revision: number;
    status: string;
    diagnosis_assessment: string;
    action_assessment: string;
    resolution_status: string;
    operator_confidence: number | null;
    quality_gate_status: string;
    training_eligible: boolean;
    reviewer: string | null;
  } | null;

  safety: {
    real_execution_enabled: boolean;
    execution_mode: string;
    auto_eligible: boolean;
  };
}


export interface DashboardIncidents {
  schema_version: string;
  generated_at: string;
  count: number;
  limit: number;
  items: DashboardIncident[];
}


export interface DashboardMap {
  schema_version: string;
  generated_at: string;

  summary: {
    tower_count: number;
    cell_count: number;
    device_count: number;
    geolocated_device_count: number;
    active_device_alert_count: number;
    point_count: number;
  };

  safety: {
    execution_mode: string;
    real_network_execution_enabled: boolean;
    auto_execution_enabled: boolean;
  };
}


export interface GuardianAlert {
  id: number;
  device_id: string;
  status: string;
  severity: string;
  risk_score: number;
  primary_cause: string;
  title: string;
  occurrence_count: number;
  first_seen_at: string;
  last_seen_at: string;
  resolved_at: string | null;
}


export interface GuardianAlertCollection {
  items: GuardianAlert[];
  count: number;
}

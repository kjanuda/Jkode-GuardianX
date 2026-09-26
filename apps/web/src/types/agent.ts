export interface AgentSource {
  source_type: string;
  source_id: string;
  label: string;
  verified: boolean | null;
}

export interface AgentAuthority {
  read_only_agent: boolean;
  deterministic_rca_authoritative: boolean;
  llm_can_override_rca: boolean;
  llm_can_execute_actions: boolean;
  real_network_execution_enabled: boolean;
  auto_execution_enabled: boolean;
}

export interface AgentResponse {
  schema_version: string;

  answer: string;

  provider: string;
  model: string;

  intent: string;

  entities: {
    case_id: number | null;
    action_plan_id: number | null;
    device_id: string | null;
    cell_id: string | null;
  };

  sources: AgentSource[];

  authority: AgentAuthority;

  evidence_summary: {
    rca_case_available: boolean;
    deterministic_rca_available: boolean;
    consensus_available: boolean;
    action_plan_available: boolean;
    device_context_available: boolean;
    cell_context_available: boolean;
    rca_evidence_count: number;
    active_alert_count: number;
  };
}

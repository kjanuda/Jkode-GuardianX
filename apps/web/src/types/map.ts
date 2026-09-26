export type MapPointType =
  | "TOWER"
  | "CELL"
  | "DEVICE";


export interface GuardianMapPoint {
  point_type: MapPointType;
  id: string;

  latitude: number;
  longitude: number;

  status: string;

  primary_cause?: string | null;
  action_status?: string | null;

  active_alert?: boolean;
  severity?: string | null;
}


export interface GuardianTower {
  id: number;
  tower_code: string;
  name: string | null;

  latitude: number;
  longitude: number;

  elevation_m: number | null;
  status: string;

  coordinate_source: string;
}


export interface GuardianCell {
  id: number;
  cell_id: string;

  technology: string;
  band: string | null;
  bandwidth_mhz: number | null;

  pci: number | null;
  earfcn: number | null;

  status: string;

  latitude: number | null;
  longitude: number | null;

  coordinate_source: string;

  sector: {
    id: number;
    sector_code: string;
    azimuth_deg: number | null;
    electrical_tilt_deg: number | null;
    mechanical_tilt_deg: number | null;
    status: string;
  } | null;

  tower: {
    id: number;
    tower_code: string;
    name: string | null;
    elevation_m: number | null;
    status: string;
  } | null;

  rca: {
    case_id: number;
    case_status: string;
    primary_cause: string;
    confidence: number | null;
    verifier_status: string | null;
  } | null;

  action: {
    id: number;
    status: string;
    action_code: string;
    risk_level: string;
    execution_mode: string;
    auto_eligible: boolean;
  } | null;
}


export interface GuardianDevice {
  id: number;
  device_id: string;

  status: string;

  model: string | null;
  manufacturer: string | null;
  software_version: string | null;
  antenna_type: string | null;

  latitude: number | null;
  longitude: number | null;

  coordinate_source: string;

  latest_telemetry: {
    id: number;
    timestamp: string;

    rsrp: number | null;
    rsrq: number | null;
    rssi: number | null;
    sinr: number | null;

    download_mbps: number | null;
    upload_mbps: number | null;

    latency_ms: number | null;
    packet_loss: number | null;
  } | null;

  serving_cell: {
    id: number;
    cell_id: string;
    technology: string;
    band: string | null;
  } | null;

  active_alert: {
    id: number;
    status: string;
    severity: string;
    risk_score: number;
    primary_cause: string;
    title: string;
  } | null;

  serving_cell_rca: GuardianCell["rca"];

  serving_cell_action: GuardianCell["action"];

  safety: {
    real_execution_enabled: boolean;
    auto_execution_enabled: boolean;
  };
}


export interface GuardianMapPayload {
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

  towers: GuardianTower[];
  cells: GuardianCell[];
  devices: GuardianDevice[];
  points: GuardianMapPoint[];

  safety: {
    execution_mode: string;
    real_network_execution_enabled: boolean;
    auto_execution_enabled: boolean;
  };
}

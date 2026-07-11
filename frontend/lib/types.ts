export interface DiagnoseRequest {
  message: string;
  product_id?: string | null;
  customer_id?: string | null;
  asset_id?: string | null;
  force_keep_context?: boolean;
}

export interface Diagnosis {
  product_id?: string;
  product_name?: string;
  asset_id?: string;
  model_number?: string;
  sku_id?: string;
  serial_number?: string;
  matched_symptoms?: Array<{
    symptom_id: string;
    description: string;
    severity: string;
    match_score: number;
    source_system?: string;
  }>;
  ranked_failure_modes?: Array<{
    failure_mode_id: string;
    name: string;
    description: string;
    posterior?: number;
    total_confidence?: number;
    rpn?: number;
    action_priority?: "High" | "Medium" | "Low";
    repair_minutes?: number;
    safety_notes?: string;
    indications?: Array<{ symptom_id: string; confidence: number }>;
  }>;
  /** Targeted troubleshooting steps from Neo4j HAS_DIAGNOSTIC_STEP / CONFIRMS */
  diagnostic_steps?: Array<{
    step_id: string;
    description: string;
    step_order?: number;
    expected_outcome?: string;
    source_system?: string;
    source_document_uri?: string;
  }>;
  historical_resolutions?: Array<any>;
  predicted_parts?: Array<any>;
  confidence?: number;
  graph_confidence?: number;
  language_confidence?: number;
  // Separated scoring fields (new in 2026-07)
  recommendation_strength?: "Strong" | "Moderate" | "Weak" | "Insufficient data";
  posterior_dominance_ratio?: number;
  traversed_symptom_ids?: string[];
  traversed_fm_id?: string;
  graph_subgraph?: any;
  provenance_trail?: Array<any>;
  evidence?: string[];
  warnings?: string[];
  context_blocked?: boolean;
  context_block_code?: string;
  resolution_meta?: {
    soft?: boolean;
    session?: string;
    suggested_product_id?: string;
    message_product_id?: string;
    bound_product_id?: string;
    can_force_keep?: boolean;
    [key: string]: any;
  };
}

export interface DiagnoseResponse {
  response: string;
  diagnosis?: Diagnosis | null;
  escalated: boolean;
  case_id?: string | null;
  crm_context?: any;
  warranty?: any;
  provenance_trail?: any[];
  graph_subgraph?: any;
}

export interface Claim {
  claim_id: string;
  status: string;
  asset_id: string;
  customer_id: string;
  product_id?: string;
  failure_mode_name?: string;
  submitted_at?: string;
}

export interface GraphData {
  nodes: Array<{ id: string; label?: string; [key: string]: any }>;
  edges: Array<{ id?: string; source: string; target: string; [key: string]: any }>;
  node_count: number;
  edge_count: number;
}

export interface Escalation {
  case_id: string;
  status: string;
  user_message: string;
  diagnosis?: any;
  created_at?: string;
}

export interface DiagnoseRequest {
  message: string;
  product_id?: string | null;
  customer_id?: string | null;
  asset_id?: string | null;
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

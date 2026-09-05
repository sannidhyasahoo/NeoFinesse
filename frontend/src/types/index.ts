export interface EvidenceNode {
  evidence_id: string;
  entity_type: string;
  entity_id: string;
  amount_inr: number;
  currency: string;
  source_file: string;
  sheet: string;
  row: number;
  cell: string;
  evidence_level: string;
  record_hash: string;
  relationship_path: string;
  status: "VERIFIED" | "REJECTED";
  rejection_reason?: string;
  lesson?: string;
  description?: string;
}

export interface AIHypothesis {
  proposed_explanation: string;
  candidate_entities: string[];
  requested_tools: string[];
  confidence_score: number;
  reasoning: string;
}

export interface VerifierConstraint {
  constraint_name: string;
  description: string;
  status: "PASS" | "FAIL";
  details: string;
}

export interface Scenario {
  scenario_id: string;
  case_id: string;
  category: string;
  settlement_id: string;
  expected_amount_inr: number;
  actual_bank_credit_inr: number;
  variance_inr: number;
  currency: string;
  expected_outcome: "RESOLVED" | "VALID_DELAYED_CREDIT" | "PARTIALLY_RESOLVED" | "ESCALATE";
  primary_cause: string;
  evidence_level: string;
  evidence_nodes: EvidenceNode[];
  rejected_decoys: EvidenceNode[];
  ai_hypothesis: AIHypothesis;
  verifier_constraints: VerifierConstraint[];
  escalation_details?: {
    is_escalated: boolean;
    unresolved_variance_inr: number;
    reasons: string[];
    action: string;
  };
}

export interface DemoCase {
  demo_id: string;
  title: string;
  subtitle: string;
  scenario_id: string;
  case_id: string;
  settlement_id: string;
  variance_display: string;
  core_lesson: string;
  workflow_step: string;
  badge_color: string;
}

export interface BenchmarkComparison {
  name: string;
  type: string;
  accuracy: string;
  false_closure: string;
  false_escalation: string;
  status: string;
}

export interface BenchmarkData {
  metadata: {
    product_name: string;
    tagline: string;
    core_principle: string;
    version: string;
    timestamp: string;
  };
  kpis: {
    total_settlements: number;
    total_variances: number;
    resolved_count: number;
    partially_resolved_count: number;
    escalated_count: number;
    false_closure_rate_pct: number;
    evidence_coverage_pct: number;
  };
  benchmarks: {
    total_scenarios: number;
    resolved_scenarios: number;
    partially_resolved_scenarios: number;
    escalated_scenarios: number;
    observed_resolution_rate_pct: number;
    false_closure_rate_pct: number;
    evidence_verification_rate_pct: number;
    benchmarks_comparison: BenchmarkComparison[];
  };
  demo_cases: DemoCase[];
  scenarios: Scenario[];
}

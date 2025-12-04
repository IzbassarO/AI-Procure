export interface TenderRiskBankingProduct {
  product: string;
  justification?: string;
  conditions?: string;
}

export interface TenderRiskKeyRisk {
  category: string;
  severity: string;
  description: string;
}

export interface TenderRiskAnalysis {
  overall_risk_level?: string;
  risk_score_estimate?: number;
  investment_opportunity_score?: number;
  banking_products?: TenderRiskBankingProduct[];
  key_risks?: TenderRiskKeyRisk[];
  investment_risks?: string[];
  red_flags?: string[];
  positive_factors?: string[];
  manager_checklist?: string[];
  recommendations?: string[];
  executive_summary?: string;
  detailed_analysis?: string;
  model_used?: string;
}

export interface TenderRiskResult {
  tender_id: string;
  tender_name: string;
  analysis: TenderRiskAnalysis;
}

export interface TenderRiskResponse {
  status: string;
  timestamp: string;
  total_tenders: number;
  results: TenderRiskResult[];
  pdf_report?: string;
  txt_report?: string;
  json_report?: string;
}

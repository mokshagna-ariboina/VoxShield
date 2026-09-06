// ── Aligned with backend/app/schemas/analysis.py ──

export interface SignalBreakdown {
  clone_probability: number;
  social_engineering_score: number;
  speaker_mismatch_score: number;
  trust_novelty_score: number;
  transaction_risk_score: number;
  [key: string]: number;
}

export interface MatchedPattern {
  category: string;
  phrase: string;
  weight: number;
}

export interface AnalysisResponse {
  id: string;
  composite_risk_score: number;
  risk_level: 'pass' | 'challenge' | 'escalate';
  signal_breakdown: SignalBreakdown;
  matched_patterns: MatchedPattern[];
  transcript: string;
  recommended_action: string;
  created_at: string;
}

// ── Aligned with backend/app/schemas/liveness.py ──

export interface ChallengeResponse {
  challenge_id: string;
  challenge_text: string;
  digits: string;
}

export interface VerifyResponse {
  passed: boolean;
  digits_matched: boolean;
  response_clone_probability: number;
  spoken_digits: string;
}

// ── Aligned with backend/app/schemas/calls.py ──

export interface CallRecord {
  id: string;
  created_at: string;
  caller_id?: string;
  audio_file_path: string;
  clone_probability: number;
  social_engineering_score: number;
  speaker_mismatch_score: number;
  trust_novelty_score: number;
  transaction_risk_score: number;
  composite_risk_score: number;
  risk_level: string;
  signal_breakdown: SignalBreakdown;
  transcript?: string;
  matched_patterns?: MatchedPattern[];
}

export interface CallListResponse {
  items: CallRecord[];
  total: number;
  page: number;
  page_size: number;
}

// ── Other types ──

export interface TimelineEvent {
  timestamp: string;
  event_type: string;
  description: string;
  status: 'complete' | 'pending' | 'failed';
  severity?: 'low' | 'medium' | 'high';
}

export interface SpeakerProfile {
  id: string;
  speaker_name: string;
  enrolled_at: string;
}

export interface TransactionAssessment {
  transaction_risk_score: number;
  action: string;
  reasons: string[];
}

export interface RiskBucket {
  name: string;
  count: number;
  color: string;
}

export interface DashboardStatsResponse {
  total_monitored: number;
  flagged_high_risk_percentage: number;
  average_risk_score: number;
  challenges_passed_percentage: number;
  risk_distribution: RiskBucket[];
}

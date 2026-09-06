from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

class CallRecordResponse(BaseModel):
    id: UUID
    created_at: datetime
    caller_id: Optional[str]
    audio_file_path: str
    clone_probability: float
    social_engineering_score: float
    speaker_mismatch_score: float
    trust_novelty_score: float
    transaction_risk_score: float
    composite_risk_score: float
    risk_level: str
    signal_breakdown: Dict[str, Any]
    transcript: Optional[str]
    matched_patterns: Optional[List[Dict[str, Any]]]

class CallListResponse(BaseModel):
    items: List[CallRecordResponse]
    total: int
    page: int
    page_size: int

class DashboardStatsResponse(BaseModel):
    total_monitored: int
    flagged_high_risk_percentage: float
    average_risk_score: float
    challenges_passed_percentage: float
    risk_distribution: List[Dict[str, Any]]

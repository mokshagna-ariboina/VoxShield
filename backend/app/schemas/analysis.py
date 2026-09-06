from pydantic import BaseModel
from typing import List
from datetime import datetime
from uuid import UUID

class SignalBreakdown(BaseModel):
    clone_probability: float
    social_engineering_score: float
    speaker_mismatch_score: float
    trust_novelty_score: float
    transaction_risk_score: float

class MatchedPattern(BaseModel):
    category: str
    phrase: str
    weight: float

class AnalysisResponse(BaseModel):
    id: UUID
    composite_risk_score: float
    risk_level: str
    signal_breakdown: SignalBreakdown
    transcript: str
    matched_patterns: List[MatchedPattern]
    recommended_action: str
    created_at: datetime

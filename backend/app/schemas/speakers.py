from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

class SpeakerEnrollRequest(BaseModel):
    speaker_name: str
    phone_number: Optional[str] = None

class SpeakerEnrollResponse(BaseModel):
    id: UUID
    speaker_name: str
    enrolled_at: datetime

class SpeakerVerifyResponse(BaseModel):
    match: bool
    similarity_score: float
    speaker_name: Optional[str] = None

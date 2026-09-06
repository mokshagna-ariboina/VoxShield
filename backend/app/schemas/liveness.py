from pydantic import BaseModel
from uuid import UUID

class ChallengeRequest(BaseModel):
    call_record_id: UUID

class ChallengeResponse(BaseModel):
    challenge_id: UUID
    challenge_text: str
    digits: str

class VerifyResponse(BaseModel):
    passed: bool
    digits_matched: bool
    response_clone_probability: float
    spoken_digits: str

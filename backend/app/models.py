import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Boolean, Integer, DateTime, ForeignKey, Text, LargeBinary, JSON
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class CallRecord(Base):
    __tablename__ = "call_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow)
    caller_id = Column(String, nullable=True)
    audio_file_path = Column(String, nullable=False)
    clone_probability = Column(Float, nullable=False)
    social_engineering_score = Column(Float, nullable=False)
    speaker_mismatch_score = Column(Float, default=0.0)
    trust_novelty_score = Column(Float, default=0.0)
    transaction_risk_score = Column(Float, default=0.0)
    composite_risk_score = Column(Float, nullable=False)
    risk_level = Column(String, nullable=False) # pass/challenge/escalate
    signal_breakdown = Column(JSON, nullable=False)
    transcript = Column(Text, nullable=True)
    matched_patterns = Column(JSON, nullable=True)

class LivenessChallenge(Base):
    __tablename__ = "liveness_challenges"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    call_record_id = Column(UUID(as_uuid=True), ForeignKey("call_records.id"), nullable=False)
    challenge_text = Column(String, nullable=False)
    response_transcript = Column(String, nullable=True)
    digits_matched = Column(Boolean, nullable=True)
    response_clone_probability = Column(Float, nullable=True)
    passed = Column(Boolean, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class SpeakerProfile(Base):
    __tablename__ = "speaker_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    speaker_name = Column(String, nullable=False)
    phone_number = Column(String, nullable=True)
    embedding_vector = Column(LargeBinary, nullable=False)
    enrolled_at = Column(DateTime, default=datetime.utcnow)

class TrustContact(Base):
    __tablename__ = "trust_contacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    speaker_profile_id = Column(UUID(as_uuid=True), ForeignKey("speaker_profiles.id"), nullable=False)
    contact_name = Column(String, nullable=True)
    contact_phone = Column(String, nullable=False)
    call_count = Column(Integer, default=0)
    last_seen = Column(DateTime, default=datetime.utcnow)
    trust_score = Column(Float, default=0.0)

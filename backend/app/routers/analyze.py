"""Core analysis router — upload audio, get risk score + signal breakdown."""

import uuid
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import (
    APIRouter, Depends, File, Form, HTTPException,
    Request, UploadFile, status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import CallRecord
from app.schemas.analysis import AnalysisResponse, SignalBreakdown, MatchedPattern
from app.utils.audio import load_audio, save_upload

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analyze", tags=["Analysis"])


@router.post("", response_model=AnalysisResponse, status_code=status.HTTP_201_CREATED)
async def analyze_audio(
    request: Request,
    file: UploadFile = File(..., description="Audio file to analyze (.wav, .mp3, .flac, .m4a, .ogg)"),
    caller_id: Optional[str] = Form(None, description="Optional caller identifier (phone number)"),
    transaction_amount: float = Form(0.0, description="Amount for financial transactions"),
    recipient_is_new: bool = Form(False, description="Explicitly marked as new recipient"),
    is_international: bool = Form(False, description="Is international transfer"),
    recipient_account: Optional[str] = Form(None, description="Recipient phone or account ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    Analyze an audio file for potential voice cloning and social engineering risks.
    """
    allowed_extensions = (".wav", ".mp3", ".flac", ".m4a", ".ogg", ".webm", ".opus")
    filename = file.filename or ""
    if not filename.lower().endswith(allowed_extensions):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format. Accepted: {', '.join(allowed_extensions)}",
        )

    try:
        file_path = await save_upload(file, settings.UPLOAD_DIR)

        # 1. AASIST deepfake detector
        aasist_result = request.app.state.aasist_detector.detect_file(file_path)
        clone_probability = aasist_result["clone_probability"]

        # 2. Whisper speech-to-text
        whisper_result = request.app.state.whisper_transcriber.transcribe(file_path)
        transcript = whisper_result["text"]

        # 3. Social-engineering language analysis
        lang_result = request.app.state.language_analyzer.analyze(transcript)
        social_engineering_score = lang_result["social_engineering_score"]
        matched_patterns_raw = lang_result["matched_patterns"]

        # 4. Speaker Profile Lookup for Speaker Verification & Trust Novelty
        speaker_mismatch_score = 0.0
        trust_novelty_score = 0.5  # Default elevated novelty if no context

        if caller_id:
            from sqlalchemy import select
            from app.models import SpeakerProfile, TrustContact
            stmt = select(SpeakerProfile).where(SpeakerProfile.phone_number == caller_id)
            res = await db.execute(stmt)
            speaker = res.scalars().first()
            
            if speaker:
                # Speaker Mismatch
                speaker_verifier = request.app.state.speaker_verifier
                if speaker_verifier and speaker_verifier.available:
                    verify_result = speaker_verifier.verify(file_path, speaker.embedding_vector)
                    if verify_result.get("match", False):
                        speaker_mismatch_score = 0.0
                    else:
                        speaker_mismatch_score = max(0.0, 1.0 - verify_result.get("similarity_score", 0.0))
                
                # Trust Novelty
                if recipient_is_new:
                    trust_novelty_score = 1.0 # Explicitly marked new
                elif recipient_account:
                    t_stmt = select(TrustContact).where(TrustContact.speaker_profile_id == speaker.id, TrustContact.contact_phone == recipient_account)
                    t_res = await db.execute(t_stmt)
                    contact = t_res.scalars().first()
                    if contact:
                        trust_novelty_score = 0.1 # Known contact
                    else:
                        trust_novelty_score = 0.7 # Unknown contact but we have profile
        else:
            if recipient_is_new:
                trust_novelty_score = 1.0

        # 5. Transaction Guard (baseline transaction risk)
        tx_guard = request.app.state.transaction_guard
        tx_result = tx_guard.assess_risk(
            amount=transaction_amount,
            recipient_is_new=recipient_is_new or (trust_novelty_score > 0.5),
            is_international=is_international,
            call_risk_score=0.0
        )
        transaction_risk_score = tx_result["transaction_risk_score"]

        # 6. Risk Engine Fusion
        risk_result = request.app.state.risk_engine.compute_risk(
            clone_probability=clone_probability,
            social_engineering_score=social_engineering_score,
            speaker_mismatch_score=speaker_mismatch_score,
            trust_novelty_score=trust_novelty_score,
            transaction_risk_score=transaction_risk_score,
        )
        composite_risk_score = risk_result["composite_risk_score"]
        risk_level = risk_result["risk_level"]
        signal_breakdown_raw = risk_result["signal_breakdown"]
        
        # 7. Final Transaction Action based on composite risk
        final_action = tx_guard.assess_risk(
            amount=transaction_amount,
            recipient_is_new=recipient_is_new,
            is_international=is_international,
            call_risk_score=composite_risk_score
        )["action"]
        
        recommended_action = f"{risk_result['recommended_action']} Action: {final_action.upper()}"

        # 8. Persist CallRecord
        call_id = uuid.uuid4()
        now = datetime.utcnow()
        call_record = CallRecord(
            id=call_id,
            created_at=now,
            caller_id=caller_id,
            audio_file_path=file_path,
            clone_probability=clone_probability,
            social_engineering_score=social_engineering_score,
            speaker_mismatch_score=speaker_mismatch_score,
            trust_novelty_score=trust_novelty_score,
            transaction_risk_score=transaction_risk_score,
            composite_risk_score=composite_risk_score,
            risk_level=risk_level,
            signal_breakdown=signal_breakdown_raw,
            transcript=transcript,
            matched_patterns=matched_patterns_raw,
        )
        db.add(call_record)
        await db.commit()
        await db.refresh(call_record)

        # Build response
        signal_breakdown = SignalBreakdown(
            clone_probability=clone_probability,
            social_engineering_score=social_engineering_score,
            speaker_mismatch_score=speaker_mismatch_score,
            trust_novelty_score=trust_novelty_score,
            transaction_risk_score=transaction_risk_score,
        )

        matched_patterns = [
            MatchedPattern(
                category=p["category"],
                phrase=p["phrase"],
                weight=p["weight"],
            )
            for p in matched_patterns_raw
        ]

        return AnalysisResponse(
            id=call_id,
            composite_risk_score=composite_risk_score,
            risk_level=risk_level,
            signal_breakdown=signal_breakdown,
            transcript=transcript,
            matched_patterns=matched_patterns,
            recommended_action=recommended_action,
            created_at=now,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error during audio analysis")
        raise HTTPException(
            status_code=500,
            detail=f"Internal error during analysis: {str(e)}",
        )

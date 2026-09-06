"""Liveness challenge router — generate challenges and verify responses."""

import uuid
import logging

from fastapi import (
    APIRouter, Depends, File, HTTPException,
    Request, UploadFile, status,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.database import get_db
from app.models import CallRecord, LivenessChallenge
from app.schemas.liveness import ChallengeRequest, ChallengeResponse, VerifyResponse
from app.utils.audio import load_audio, save_upload

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/liveness", tags=["Liveness"])


@router.post("/challenge", response_model=ChallengeResponse, status_code=status.HTTP_201_CREATED)
async def create_challenge(
    request: Request,
    body: ChallengeRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a liveness challenge for a given call record.

    Returns a random digit sequence the caller must repeat to prove liveness.
    """
    # Verify call record exists
    stmt = select(CallRecord).where(CallRecord.id == body.call_record_id)
    result = await db.execute(stmt)
    call_record = result.scalars().first()

    if not call_record:
        raise HTTPException(status_code=404, detail="Call record not found")

    # Generate challenge
    liveness_service = request.app.state.liveness_service
    challenge_data = liveness_service.generate_challenge()

    # Persist
    challenge_id = uuid.uuid4()
    challenge = LivenessChallenge(
        id=challenge_id,
        call_record_id=call_record.id,
        challenge_text=challenge_data["challenge_text"],
    )
    db.add(challenge)
    await db.commit()
    await db.refresh(challenge)

    return ChallengeResponse(
        challenge_id=challenge.id,
        challenge_text=challenge_data["challenge_text"],
        digits=challenge_data["digits"],
    )


@router.post("/verify/{challenge_id}", response_model=VerifyResponse)
async def verify_challenge(
    challenge_id: uuid.UUID,
    request: Request,
    file: UploadFile = File(..., description="Audio recording of the challenge response"),
    db: AsyncSession = Depends(get_db),
):
    """
    Verify a liveness challenge by processing an audio response.

    1. Transcribes the response audio with Whisper
    2. Compares spoken digits against expected digits
    3. Runs AASIST on the response for a second deepfake check
    """
    # Look up challenge
    stmt = select(LivenessChallenge).where(LivenessChallenge.id == challenge_id)
    result = await db.execute(stmt)
    challenge = result.scalars().first()

    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")

    try:
        # Save and load response audio
        file_path = await save_upload(file, settings.UPLOAD_DIR)

        # Transcribe response
        whisper_result = request.app.state.whisper_transcriber.transcribe(file_path)
        response_transcript = whisper_result["text"]

        # Extract the expected digits from challenge_text (stored as "Please repeat: X-X-X-X-X-X")
        # The digits are the raw digit string without dashes
        expected_digits = "".join(c for c in challenge.challenge_text if c.isdigit())

        # Verify digit match
        liveness_service = request.app.state.liveness_service
        verify_result = liveness_service.verify_response(expected_digits, response_transcript)

        # Run AASIST on response audio for second clone check
        audio_data, sample_rate = load_audio(file_path)
        aasist_result = request.app.state.aasist_detector.detect_file(file_path)
        response_clone_prob = aasist_result["clone_probability"]

        # Final pass decision: digits must match AND clone probability must be low
        digits_matched = verify_result["digits_matched"]
        passed = digits_matched and response_clone_prob < 0.5

        # Update challenge record
        challenge.response_transcript = response_transcript
        challenge.digits_matched = digits_matched
        challenge.response_clone_probability = response_clone_prob
        challenge.passed = passed
        await db.commit()
        await db.refresh(challenge)

        return VerifyResponse(
            passed=passed,
            digits_matched=digits_matched,
            response_clone_probability=response_clone_prob,
            spoken_digits=verify_result["spoken_digits"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error during liveness verification")
        raise HTTPException(
            status_code=500,
            detail=f"Internal error during verification: {str(e)}",
        )

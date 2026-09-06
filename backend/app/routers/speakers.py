import uuid
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, File, UploadFile, Form, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import SpeakerProfile
from app.schemas.speakers import SpeakerEnrollResponse, SpeakerVerifyResponse
from app.utils.audio import save_upload

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/speakers", tags=["Speakers"])

@router.post("/enroll", response_model=SpeakerEnrollResponse, status_code=status.HTTP_201_CREATED)
async def enroll_speaker(
    request: Request,
    speaker_name: str = Form(...),
    phone_number: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Enroll a new speaker by extracting their voice embedding.
    """
    try:
        from app.config import settings
        import pickle
        file_path = await save_upload(file, settings.UPLOAD_DIR)
        speaker_verifier = request.app.state.speaker_verifier
        
        # Extract embedding
        embedding = speaker_verifier.extract_embedding(file_path)
        if embedding is None:
            raise HTTPException(status_code=400, detail="Could not extract voice embedding")
            
        embedding_bytes = pickle.dumps(embedding)
        
        speaker_id = uuid.uuid4()
        speaker = SpeakerProfile(
            id=speaker_id,
            speaker_name=speaker_name,
            phone_number=phone_number,
            embedding_vector=embedding_bytes
        )
        db.add(speaker)
        await db.commit()
        await db.refresh(speaker)
        
        return SpeakerEnrollResponse(
            speaker_id=speaker.id,
            speaker_name=speaker.speaker_name
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during speaker enrollment: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during enrollment")

@router.post("/verify", response_model=SpeakerVerifyResponse)
async def verify_speaker(
    request: Request,
    speaker_profile_id: uuid.UUID = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Verify a caller's voice against an enrolled speaker profile.
    """
    stmt = select(SpeakerProfile).where(SpeakerProfile.id == speaker_profile_id)
    result = await db.execute(stmt)
    speaker = result.scalars().first()
    
    if not speaker:
        raise HTTPException(status_code=404, detail="Speaker profile not found")
        
    try:
        from app.config import settings
        file_path = await save_upload(file, settings.UPLOAD_DIR)
        speaker_verifier = request.app.state.speaker_verifier
        
        # Verify embedding
        verify_result = speaker_verifier.verify(file_path, speaker.embedding_vector)
        
        return SpeakerVerifyResponse(
            speaker_profile_id=speaker.id,
            is_match=verify_result.get("match", False),
            confidence=verify_result.get("similarity_score", 0.0)
        )
    except Exception as e:
        logger.error(f"Error during speaker verification: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during verification")

@router.get("", response_model=list)
async def list_speakers(db: AsyncSession = Depends(get_db)):
    """
    List all enrolled speakers.
    """
    stmt = select(SpeakerProfile)
    result = await db.execute(stmt)
    speakers = result.scalars().all()
    return speakers

import uuid
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.database import get_db
from app.models import TrustContact, SpeakerProfile

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/trust", tags=["Trust"])

class TrustContactCreate(BaseModel):
    speaker_profile_id: uuid.UUID
    contact_name: str
    contact_phone: str

class TrustContactUpdate(BaseModel):
    trust_score: float = None
    call_count: int = None

@router.get("/contacts/{speaker_id}")
async def list_contacts(speaker_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """
    List all trusted contacts for a given speaker.
    """
    stmt = select(TrustContact).where(TrustContact.speaker_profile_id == speaker_id)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/contacts", status_code=status.HTTP_201_CREATED)
async def add_contact(contact: TrustContactCreate, db: AsyncSession = Depends(get_db)):
    """
    Add a trusted contact for a speaker profile.
    """
    stmt = select(SpeakerProfile).where(SpeakerProfile.id == contact.speaker_profile_id)
    res = await db.execute(stmt)
    if not res.scalars().first():
        raise HTTPException(status_code=404, detail="Speaker profile not found")

    new_contact = TrustContact(
        id=uuid.uuid4(),
        speaker_profile_id=contact.speaker_profile_id,
        contact_name=contact.contact_name,
        contact_phone=contact.contact_phone,
        trust_score=1.0,
        call_count=0
    )
    db.add(new_contact)
    await db.commit()
    await db.refresh(new_contact)
    return new_contact

@router.put("/contacts/{contact_id}")
async def update_contact(contact_id: uuid.UUID, update_data: TrustContactUpdate, db: AsyncSession = Depends(get_db)):
    """
    Update trust score and call count for a contact.
    """
    stmt = select(TrustContact).where(TrustContact.id == contact_id)
    result = await db.execute(stmt)
    contact = result.scalars().first()
    
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
        
    if update_data.trust_score is not None:
        contact.trust_score = update_data.trust_score
    if update_data.call_count is not None:
        contact.call_count = update_data.call_count
        
    await db.commit()
    await db.refresh(contact)
    return contact

@router.delete("/contacts/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_contact(contact_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """
    Remove a trusted contact.
    """
    stmt = select(TrustContact).where(TrustContact.id == contact_id)
    result = await db.execute(stmt)
    contact = result.scalars().first()
    
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
        
    await db.delete(contact)
    await db.commit()
    return None

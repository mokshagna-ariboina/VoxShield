import uuid
import logging
from typing import Optional
from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.database import get_db
from app.models import CallRecord

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/transactions", tags=["Transactions"])

class TransactionAssessRequest(BaseModel):
    amount: float
    recipient_is_new: bool
    is_international: bool
    call_record_id: Optional[uuid.UUID] = None

class TransactionHoldRequest(BaseModel):
    transaction_id: str
    reason: str

class TransactionReleaseRequest(BaseModel):
    transaction_id: str

@router.post("/assess")
async def assess_transaction(
    request: Request,
    assess_req: TransactionAssessRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Assess a transaction for risk, optionally associated with a call record.
    """
    risk_score = 0.0
    
    if assess_req.call_record_id:
        stmt = select(CallRecord).where(CallRecord.id == assess_req.call_record_id)
        result = await db.execute(stmt)
        call_record = result.scalars().first()
        if call_record:
            risk_score = call_record.composite_score
            
    # Attempt to use transaction_guard if present
    transaction_guard = getattr(request.app.state, "transaction_guard", None)
    if transaction_guard:
        assessment = transaction_guard.assess_risk(
            amount=assess_req.amount,
            recipient_is_new=assess_req.recipient_is_new,
            is_international=assess_req.is_international,
            call_risk_score=risk_score
        )
    else:
        # Fallback simplistic assessment
        action = "allow"
        reasons = []
        if risk_score > 0.7 or (assess_req.amount > 10000 and assess_req.is_international):
            action = "block"
            reasons.append("High risk combination of transaction details and call risk.")
        elif risk_score > 0.4 or assess_req.recipient_is_new:
            action = "hold"
            reasons.append("Moderate risk detected, holding for review.")
            
        assessment = {
            "action": action,
            "reasons": reasons
        }

    return assessment

@router.post("/hold")
async def hold_transaction(req: TransactionHoldRequest):
    """
    Mock endpoint to hold a transaction.
    """
    logger.info(f"Transaction {req.transaction_id} held. Reason: {req.reason}")
    return {
        "status": "success",
        "transaction_id": req.transaction_id,
        "action": "held",
        "reason": req.reason
    }

@router.post("/release")
async def release_transaction(req: TransactionReleaseRequest):
    """
    Mock endpoint to release a held transaction.
    """
    logger.info(f"Transaction {req.transaction_id} released.")
    return {
        "status": "success",
        "transaction_id": req.transaction_id,
        "action": "released"
    }

"""Call log router — paginated call history with filtering."""

import uuid
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from app.database import get_db
from app.models import CallRecord
from app.schemas.calls import CallRecordResponse, CallListResponse, DashboardStatsResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/calls", tags=["Calls"])


@router.get("", response_model=CallListResponse)
async def get_calls(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level: pass, challenge, escalate"),
    db: AsyncSession = Depends(get_db),
):
    """Get a paginated list of call records, sorted by most recent first."""
    # Base query
    base_stmt = select(CallRecord)
    count_stmt = select(func.count(CallRecord.id))

    if risk_level:
        base_stmt = base_stmt.where(CallRecord.risk_level == risk_level)
        count_stmt = count_stmt.where(CallRecord.risk_level == risk_level)

    # Total count
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    # Paginated results
    offset = (page - 1) * page_size
    stmt = base_stmt.order_by(desc(CallRecord.created_at)).offset(offset).limit(page_size)
    result = await db.execute(stmt)
    calls = result.scalars().all()

    return CallListResponse(
        items=[
            CallRecordResponse(
                id=c.id,
                created_at=c.created_at,
                caller_id=c.caller_id,
                audio_file_path=c.audio_file_path,
                clone_probability=c.clone_probability,
                social_engineering_score=c.social_engineering_score,
                speaker_mismatch_score=c.speaker_mismatch_score,
                trust_novelty_score=c.trust_novelty_score,
                transaction_risk_score=c.transaction_risk_score,
                composite_risk_score=c.composite_risk_score,
                risk_level=c.risk_level,
                signal_breakdown={k: v.get("raw_score", 0.0) if isinstance(v, dict) else v for k, v in c.signal_breakdown.items()} if c.signal_breakdown else {},
                transcript=c.transcript,
                matched_patterns=c.matched_patterns,
            )
            for c in calls
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    """Get aggregated statistics for the Analyst Dashboard."""
    from app.models import LivenessChallenge
    from sqlalchemy import select, func, case

    # 1. Total Monitored & Averages & High Risk count
    stmt = select(
        func.count(CallRecord.id).label("total"),
        func.avg(CallRecord.composite_risk_score).label("avg_risk"),
        func.sum(
            case(
                (CallRecord.risk_level.in_(["challenge", "escalate"]), 1),
                else_=0
            )
        ).label("high_risk_count")
    )
    res = await db.execute(stmt)
    row = res.one()
    
    total = row.total or 0
    avg_risk = float(row.avg_risk or 0.0)
    high_risk_count = row.high_risk_count or 0
    
    flagged_pct = (high_risk_count / total * 100) if total > 0 else 0.0
    
    # 2. Challenges Passed Percentage
    l_stmt = select(
        func.count(LivenessChallenge.id).label("total_challenges"),
        func.sum(
            case(
                (LivenessChallenge.passed == True, 1),
                else_=0
            )
        ).label("passed_count")
    )
    l_res = await db.execute(l_stmt)
    l_row = l_res.one()
    
    total_challenges = l_row.total_challenges or 0
    passed_challenges = l_row.passed_count or 0
    challenges_pct = (passed_challenges / total_challenges * 100) if total_challenges > 0 else 0.0
    
    # 3. Risk Distribution (Bucket values 0.0-1.0 to 0-100 scales)
    # 0.00-0.20 -> 0-20, >0.20-0.40 -> 21-40, >0.40-0.60 -> 41-60, >0.60-0.80 -> 61-80, >0.80-1.00 -> 81-100
    dist_stmt = select(
        func.sum(case((CallRecord.composite_risk_score <= 0.20, 1), else_=0)).label("bucket_20"),
        func.sum(case(((CallRecord.composite_risk_score > 0.20) & (CallRecord.composite_risk_score <= 0.40), 1), else_=0)).label("bucket_40"),
        func.sum(case(((CallRecord.composite_risk_score > 0.40) & (CallRecord.composite_risk_score <= 0.60), 1), else_=0)).label("bucket_60"),
        func.sum(case(((CallRecord.composite_risk_score > 0.60) & (CallRecord.composite_risk_score <= 0.80), 1), else_=0)).label("bucket_80"),
        func.sum(case((CallRecord.composite_risk_score > 0.80, 1), else_=0)).label("bucket_100")
    )
    d_res = await db.execute(dist_stmt)
    d_row = d_res.one()
    
    risk_dist = [
        {"name": "0-20", "count": d_row.bucket_20 or 0, "color": "#22c55e"},
        {"name": "21-40", "count": d_row.bucket_40 or 0, "color": "#22c55e"},
        {"name": "41-60", "count": d_row.bucket_60 or 0, "color": "#f59e0b"},
        {"name": "61-80", "count": d_row.bucket_80 or 0, "color": "#ef4444"},
        {"name": "81-100", "count": d_row.bucket_100 or 0, "color": "#ef4444"},
    ]
    
    return DashboardStatsResponse(
        total_monitored=total,
        flagged_high_risk_percentage=flagged_pct,
        average_risk_score=avg_risk * 100, # Converting 0-1 scale to 0-100 scale for UI
        challenges_passed_percentage=challenges_pct,
        risk_distribution=risk_dist
    )

@router.get("/{call_id}", response_model=CallRecordResponse)
async def get_call(
    call_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get details of a single call record by ID, including its full risk breakdown."""
    stmt = select(CallRecord).where(CallRecord.id == call_id)
    result = await db.execute(stmt)
    call = result.scalars().first()

    if not call:
        raise HTTPException(status_code=404, detail="Call record not found")

    return CallRecordResponse(
        id=call.id,
        created_at=call.created_at,
        caller_id=call.caller_id,
        audio_file_path=call.audio_file_path,
        clone_probability=call.clone_probability,
        social_engineering_score=call.social_engineering_score,
        speaker_mismatch_score=call.speaker_mismatch_score,
        trust_novelty_score=call.trust_novelty_score,
        transaction_risk_score=call.transaction_risk_score,
        composite_risk_score=call.composite_risk_score,
        risk_level=call.risk_level,
        signal_breakdown={k: v.get("raw_score", 0.0) if isinstance(v, dict) else v for k, v in call.signal_breakdown.items()} if call.signal_breakdown else {},
        transcript=call.transcript,
        matched_patterns=call.matched_patterns,
    )

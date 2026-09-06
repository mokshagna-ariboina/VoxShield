import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func, case
from app.config import settings
from app.models import CallRecord, LivenessChallenge

async def init_db():
    engine = create_async_engine(settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"), echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    return async_session()

async def test():
    db = await init_db()
    try:
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
        print(l_row)
        
        dist_stmt = select(
            func.sum(case((CallRecord.composite_risk_score <= 0.20, 1), else_=0)).label("bucket_20"),
            func.sum(case((CallRecord.composite_risk_score > 0.20) & (CallRecord.composite_risk_score <= 0.40, 1), else_=0)).label("bucket_40"),
            func.sum(case((CallRecord.composite_risk_score > 0.40) & (CallRecord.composite_risk_score <= 0.60, 1), else_=0)).label("bucket_60"),
            func.sum(case((CallRecord.composite_risk_score > 0.60) & (CallRecord.composite_risk_score <= 0.80, 1), else_=0)).label("bucket_80"),
            func.sum(case((CallRecord.composite_risk_score > 0.80, 1), else_=0)).label("bucket_100")
        )
        d_res = await db.execute(dist_stmt)
        d_row = d_res.one()
        print(d_row)

    except Exception as e:
        print("Error:", e)
    finally:
        await db.close()

asyncio.run(test())

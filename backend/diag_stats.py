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
        print(row)
    except Exception as e:
        print("Error:", e)
    finally:
        await db.close()

asyncio.run(test())

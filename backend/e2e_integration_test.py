import asyncio
import os
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import SpeakerProfile, TrustContact
from app.config import settings
from app.services.aasist_detector import AASISTDetector
from app.services.language_analyzer import LanguageAnalyzer
from app.services.risk_engine import RiskEngine
from app.services.speaker_verifier import SpeakerVerifier
from app.services.transaction_guard import TransactionGuard

import pickle

async def init_db():
    engine = create_async_engine(settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"), echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    return async_session()

async def run_integration_tests():
    db = await init_db()
    
    print("="*60)
    print("INITIALIZING SERVICES...")
    aasist = AASISTDetector('aasist/config/AASIST.conf', 'weights/AASIST.pth', 'cpu')
    lang_analyzer = LanguageAnalyzer()
    verifier = SpeakerVerifier()
    tx_guard = TransactionGuard()
    risk_engine = RiskEngine(
        weights={
            "clone_probability": 0.4,
            "social_engineering_score": 0.3,
            "speaker_mismatch_score": 0.15,
            "trust_novelty_score": 0.05,
            "transaction_risk_score": 0.1
        },
        pass_threshold=0.3,
        challenge_threshold=0.6
    )

    print("="*60)
    print("STEP 1: ENROLLMENT")
    caller_phone = "+15551234567"
    trusted_recipient = "+19998887777"
    
    # 1. Enroll human voice
    human_audio = "uploads/human.m4a.m4a"
    emb = verifier.extract_embedding(human_audio)
    emb_bytes = pickle.dumps(emb)
    
    speaker_id = uuid.uuid4()
    speaker = SpeakerProfile(
        id=speaker_id,
        speaker_name="Alice",
        phone_number=caller_phone,
        embedding_vector=emb_bytes
    )
    db.add(speaker)
    
    # 2. Add Trusted Contact
    contact = TrustContact(
        id=uuid.uuid4(),
        speaker_profile_id=speaker_id,
        contact_name="Bob",
        contact_phone=trusted_recipient,
        trust_score=1.0,
        call_count=5
    )
    db.add(contact)
    await db.commit()
    
    print(f"Enrolled Alice ({caller_phone}) with known contact Bob ({trusted_recipient})")

    # Helper for running the pipeline (mimics analyze.py)
    async def run_pipeline(name, audio_path, transcript, amount, recipient, is_new):
        print(f"\n{'-'*60}")
        print(f"TEST: {name}")
        
        # AASIST
        aasist_res = aasist.detect_file(audio_path)
        clone_prob = aasist_res["clone_probability"]
        
        # NLP
        lang_res = lang_analyzer.analyze(transcript)
        soc_eng = lang_res["social_engineering_score"]
        
        # Speaker & Trust
        speaker_mismatch = 0.0
        trust_novelty = 0.5
        
        from sqlalchemy import select
        stmt = select(SpeakerProfile).where(SpeakerProfile.phone_number == caller_phone)
        res = await db.execute(stmt)
        spk = res.scalars().first()
        
        verify_result = verifier.verify(audio_path, spk.embedding_vector)
        if verify_result.get("match", False):
            speaker_mismatch = 0.0
        else:
            speaker_mismatch = max(0.0, 1.0 - verify_result.get("similarity_score", 0.0))
            
        if is_new:
            trust_novelty = 1.0
        else:
            t_stmt = select(TrustContact).where(TrustContact.speaker_profile_id == spk.id, TrustContact.contact_phone == recipient)
            t_res = await db.execute(t_stmt)
            t_contact = t_res.scalars().first()
            if t_contact:
                trust_novelty = 0.1
            else:
                trust_novelty = 0.7
                
        # Transaction Guard Baseline
        tx_res = tx_guard.assess_risk(amount, is_new or (trust_novelty > 0.5), False, 0.0)
        tx_risk = tx_res["transaction_risk_score"]
        
        # Risk Engine
        risk_res = risk_engine.compute_risk(clone_prob, soc_eng, speaker_mismatch, trust_novelty, tx_risk)
        comp_risk = risk_res["composite_risk_score"]
        level = risk_res["risk_level"]
        
        # Transaction Action
        final_action = tx_guard.assess_risk(amount, is_new, False, comp_risk)["action"]
        
        print(f"Clone Prob: {clone_prob:.6f}")
        print(f"Social Eng: {soc_eng:.2f}")
        print(f"Speaker Mismatch: {speaker_mismatch:.2f}")
        print(f"Trust Novelty: {trust_novelty:.2f}")
        print(f"Transaction Risk: {tx_risk:.2f}")
        print(f"Composite Risk: {comp_risk:.4f} -> {level.upper()}")
        print(f"Final Action: {final_action.upper()}")

    # SCENARIO 1: BENIGN
    await run_pipeline(
        name="1. BENIGN (Human + Routine + Normal Amt + Known)",
        audio_path="uploads/human.m4a.m4a",
        transcript="Please confirm the routine payment of twenty thousand rupees scheduled for today.",
        amount=500.0,
        recipient=trusted_recipient,
        is_new=False
    )
    
    # SCENARIO 2: SUSPICIOUS
    await run_pipeline(
        name="2. SUSPICIOUS (Human + Urgent + Large Amt + New)",
        audio_path="uploads/human.m4a.m4a",
        transcript="Transfer eight lakh rupees immediately to the new beneficiary. This is urgent and confidential.",
        amount=25000.0,
        recipient="+10000000000",
        is_new=True
    )
    
    # SCENARIO 3: CLONED
    await run_pipeline(
        name="3. CLONED (Synthetic + Urgent + Large Amt + New)",
        audio_path="uploads/neural.mp3",
        transcript="Transfer eight lakh rupees immediately to the new beneficiary. This is urgent and confidential.",
        amount=25000.0,
        recipient="+10000000000",
        is_new=True
    )

if __name__ == '__main__':
    asyncio.run(run_integration_tests())


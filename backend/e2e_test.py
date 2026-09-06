import sys
import json

from app.services.aasist_detector import AASISTDetector
from app.services.language_analyzer import LanguageAnalyzer
from app.services.risk_engine import RiskEngine

def run_test(name, audio_path, injected_transcript):
    print(f"\n{'='*60}")
    print(f"TEST: {name}")
    print(f"AUDIO FILE: {audio_path}")
    print(f"TRANSCRIPT: '{injected_transcript}'")
    print(f"{'-'*60}")
    
    # 1. AASIST
    detector = AASISTDetector('aasist/config/AASIST.conf', 'weights/AASIST.pth', 'cpu')
    aasist_res = detector.detect_file(audio_path)
    clone_prob = aasist_res['clone_probability']
    print(f"1. AASIST clone_probability: {clone_prob:.6f} -> Class: {'SPOOF' if aasist_res['is_clone'] else 'BONAFIDE'}")
    
    # 2. Whisper (Simulated via injected_transcript)
    transcript = injected_transcript
    print(f"2. Whisper STT: '{transcript}'")
    
    # 3. Social Engineering
    lang_analyzer = LanguageAnalyzer()
    lang_res = lang_analyzer.analyze(transcript)
    soc_eng_score = lang_res['social_engineering_score']
    print(f"3. Social Eng Score: {soc_eng_score:.2f} | Matched: {[p['phrase'] for p in lang_res['matched_patterns']]}")
    
    # 4. Context/Trust Signals & Transaction Risk
    # In analyze.py these are hardcoded to 0.0
    speaker_mismatch = 0.0
    trust_novelty = 0.0
    transaction_risk = 0.0
    print(f"4. Trust/Context/Transaction: speaker_mismatch={speaker_mismatch}, trust_novelty={trust_novelty}, transaction_risk={transaction_risk}")
    print(f"   (STATUS: UNWIRED. Hardcoded to 0.0 in /api/analyze)")
    
    # 5. Composite Risk Engine
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
    risk_res = risk_engine.compute_risk(
        clone_probability=clone_prob,
        social_engineering_score=soc_eng_score,
        speaker_mismatch_score=speaker_mismatch,
        trust_novelty_score=trust_novelty,
        transaction_risk_score=transaction_risk
    )
    comp_risk = risk_res['composite_risk_score']
    risk_level = risk_res['risk_level']
    print(f"5. Composite Risk Score: {comp_risk:.4f} | Level: {risk_level.upper()}")
    print(f"   Recommended Action: {risk_res['recommended_action']}")
    
    # 6. API Response Fields mapping (mocking analyze.py)
    print(f"6. API Response fields mapping:")
    print(f"   composite_risk_score: {comp_risk:.4f}")
    print(f"   risk_level: {risk_level}")
    print(f"   signal_breakdown: {{ clone_probability: {clone_prob:.6f}, social_engineering_score: {soc_eng_score:.2f}, speaker_mismatch_score: 0.0, trust_novelty_score: 0.0, transaction_risk_score: 0.0 }}")

# TEST 1: Benign
run_test("TEST 1 - BENIGN", "uploads/human.m4a.m4a", "Please confirm the routine payment of twenty thousand rupees scheduled for today.")

# TEST 2: High Risk
run_test("TEST 2 - HIGH RISK", "uploads/human.m4a.m4a", "Transfer eight lakh rupees immediately to the new beneficiary. This is urgent and confidential.")

# TEST 3: Synthetic Voice
run_test("TEST 3 - SYNTHETIC", "uploads/neural.mp3", "Transfer eight lakh rupees immediately to the new beneficiary. This is urgent and confidential.")



from app.services.language_analyzer import LanguageAnalyzer
from app.services.risk_engine import RiskEngine
from app.config import settings

analyzer = LanguageAnalyzer()
risk_engine = RiskEngine(
    weights={
        'clone_probability': settings.WEIGHT_CLONE,
        'social_engineering_score': settings.WEIGHT_SOCIAL_ENG,
        'speaker_mismatch_score': settings.WEIGHT_SPEAKER,
        'trust_novelty_score': settings.WEIGHT_TRUST,
        'transaction_risk_score': settings.WEIGHT_TRANSACTION
    },
    pass_threshold=settings.RISK_THRESHOLD_PASS,
    challenge_threshold=settings.RISK_THRESHOLD_CHALLENGE
)

transcript = 'Sure, I can complete the transfer today, no problem, let me know if you need anything else.'
lang_result = analyzer.analyze(transcript)
risk = risk_engine.compute_risk(
    clone_probability=0.0,
    social_engineering_score=lang_result['social_engineering_score']
)

print('Transcript:', transcript)
print('Social Engineering Score:', lang_result['social_engineering_score'])
print('Matched Patterns:', lang_result['matched_patterns'])
print('Composite Risk Score:', risk['composite_risk_score'])
print('Risk Level:', risk['risk_level'])


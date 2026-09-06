import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class RiskEngine:
    """Engine for fusing risk signals into a composite score."""
    
    def __init__(self, weights: Dict[str, float], pass_threshold: float, challenge_threshold: float):
        self.weights = weights
        self.pass_threshold = pass_threshold
        self.challenge_threshold = challenge_threshold

    def compute_risk(self, 
                     clone_probability: float, 
                     social_engineering_score: float, 
                     speaker_mismatch_score: float = 0.0, 
                     trust_novelty_score: float = 0.0, 
                     transaction_risk_score: float = 0.0) -> Dict[str, Any]:
        """
        Compute composite risk based on multiple signals.
        
        Uses a hybrid approach: the composite score is the HIGHER of:
          1. The traditional weighted sum of all signals
          2. The single highest raw signal value (risk floor)
        
        This ensures that one dangerously high signal (e.g., 0.65 social
        engineering) can never be diluted below its own value by four
        other signals sitting at zero.
        """
        signals = {
            "clone_probability": clone_probability,
            "social_engineering_score": social_engineering_score,
            "speaker_mismatch_score": speaker_mismatch_score,
            "trust_novelty_score": trust_novelty_score,
            "transaction_risk_score": transaction_risk_score
        }
        
        weighted_sum = 0.0
        signal_breakdown = {}
        
        for name, value in signals.items():
            weight = self.weights.get(name, 0.0)
            weighted_score = value * weight
            weighted_sum += weighted_score
            signal_breakdown[name] = {
                "raw_score": value,
                "weight": weight,
                "weighted_score": weighted_score
            }
        
        # Risk floor: the highest individual signal sets a minimum
        max_signal = max(signals.values()) if signals else 0.0
        
        # Composite = whichever is higher
        composite_score = max(weighted_sum, max_signal)
        composite_score = max(0.0, min(1.0, composite_score))
        
        if composite_score < self.pass_threshold:
            risk_level = "pass"
            recommended_action = "Transaction seems normal. Allow to proceed."
        elif composite_score < self.challenge_threshold:
            risk_level = "challenge"
            recommended_action = "Moderate risk detected. Issue liveness challenge."
        else:
            risk_level = "escalate"
            recommended_action = "High risk detected. Escalate for manual review or block."
            
        return {
            "composite_risk_score": float(composite_score),
            "risk_level": risk_level,
            "recommended_action": recommended_action,
            "signal_breakdown": signal_breakdown
        }

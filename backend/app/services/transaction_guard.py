import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class TransactionGuard:
    """Evaluates transactional risk."""
    
    def assess_risk(self, amount: float, recipient_is_new: bool, is_international: bool = False, call_risk_score: float = 0.0) -> Dict[str, Any]:
        """
        Assess risk of a financial transaction.
        
        Args:
            amount: Transaction amount
            recipient_is_new: True if recipient is not in known contacts
            is_international: True if it's an international transfer
            call_risk_score: Risk score from the active call (0-1)
            
        Returns:
            Dictionary with transaction risk assessment
        """
        score = 0.0
        reasons = []
        
        if amount > 10000:
            score += 0.5
            reasons.append(f"High transaction amount ({amount})")
        elif amount > 5000:
            score += 0.3
            reasons.append(f"Moderate transaction amount ({amount})")
            
        if recipient_is_new:
            score += 0.2
            reasons.append("New/unknown recipient")
            
        if is_international:
            score += 0.15
            reasons.append("International transfer")
            
        if call_risk_score > 0.5:
            score += 0.3
            reasons.append("High contextual risk from active call")
            
        score = max(0.0, min(1.0, score))
        
        # Action is based on the combination of transaction risk and context risk (call_risk_score)
        # We define a combined transaction + contextual risk here, or rely on the final composite.
        # But this method is just assessing transaction risk. Let's return the score and let the router
        # ask for the action later, or return an action based on call_risk_score.
        # Wait, the user asked to use the existing transaction policy:
        # low risk -> allow
        # medium risk -> require verification
        # high/critical risk -> block
        
        combined_risk = max(score, call_risk_score)
        
        if combined_risk < 0.3:
            action = "allow"
        elif combined_risk < 0.6:
            action = "require verification/liveness"
        elif combined_risk < 0.8:
            action = "hold"
        else:
            action = "block"
            
        return {
            "transaction_risk_score": float(score),
            "action": action,
            "reasons": reasons
        }

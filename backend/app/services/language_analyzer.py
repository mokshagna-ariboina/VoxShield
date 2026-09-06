import logging
import re
from typing import Dict, Any

logger = logging.getLogger(__name__)

class LanguageAnalyzer:
    """Analyzes text transcripts for social engineering patterns."""
    
    def __init__(self):
        self.categories = {
            "URGENCY": [
                r"\bright now\b", r"\bimmediately\b", r"\btime-sensitive\b", 
                r"\bexpires today\b", r"\blast chance\b", r"\burgent\b", 
                r"\bhurry\b", r"\bdeadline\b", r"\bact fast\b", r"\blimited time\b",
                r"\bcompleted today\b", r"\baction completed today\b",
                r"\bas soon as possible\b", r"\bASAP\b", r"\bwithout delay\b",
                r"\btime is running out\b", r"\bdon't wait\b", r"\bdo not wait\b",
            ],
            "SECRECY": [
                r"\bdon't tell anyone\b", r"\bdo not tell anyone\b",
                r"\bkeep this between us\b", r"\bconfidential\b", 
                r"\boff the record\b", r"\bsecret\b", r"\bprivate matter\b", 
                r"\bdon't share\b", r"\bdo not share\b",
                r"\bbetween you and me\b",
                r"\bdon't discuss\b", r"\bdo not discuss\b",
                r"\bdon't mention\b", r"\bdo not mention\b",
                r"\btell no one\b", r"\bnobody needs to know\b",
            ],
            "AUTHORITY": [
                r"\bcalling from the bank\b", r"\bI'm your manager\b", r"\bcompliance requires\b", 
                r"\bthis is the IRS\b", r"\bgovernment agency\b", r"\bpolice department\b", 
                r"\blegal department\b", r"\bfraud department\b", r"\bsecurity team\b", 
                r"\bauthorized representative\b",
                r"\bhead office\b", r"\bsenior management\b", r"\bCEO\b",
                r"\bcompliance team\b", r"\brisk department\b",
            ],
            "FEAR": [
                r"\baccount will be frozen\b", r"\blegal action\b", r"\barrest warrant\b", 
                r"\bsuspended\b", r"\bterminated\b", r"\bpenalty\b", r"\bfine\b", 
                r"\blawsuit\b", r"\bcriminal charges\b", r"\baccount compromised\b",
                r"\byou will be held responsible\b", r"\bconsequences\b",
                r"\bblock your account\b", r"\bfreeze your account\b",
            ],
            "FINANCIAL_PRESSURE": [
                r"\btransfer now\b", r"\bwire the funds\b", r"\bgift cards\b", 
                r"\bcryptocurrency\b", r"\bWestern Union\b", r"\bmoney order\b", 
                r"\bcash deposit\b", r"\brouting number\b", r"\baccount number\b", 
                r"\bsend money\b",
                r"\bcomplete the transfer\b", r"\bprocess the payment\b",
                r"\bchanged account\b", r"\baccount details have changed\b",
                r"\bnew account\b", r"\bupdated bank details\b",
                r"\bmake the payment\b", r"\bpay immediately\b",
            ]
        }
        
        self.weights = {
            "URGENCY": 0.15,
            "SECRECY": 0.20,
            "AUTHORITY": 0.25,
            "FEAR": 0.25,
            "FINANCIAL_PRESSURE": 0.30
        }

    def analyze(self, transcript: str) -> Dict[str, Any]:
        """
        Analyze transcript for risk patterns.
        
        Args:
            transcript: Text to analyze
            
        Returns:
            Dictionary containing risk scores and matched patterns
        """
        matched_patterns = []
        category_scores = {cat: 0.0 for cat in self.categories}
        
        for category, patterns in self.categories.items():
            for pattern in patterns:
                matches = re.finditer(pattern, transcript, re.IGNORECASE)
                for match in matches:
                    matched_patterns.append({
                        "category": category,
                        "phrase": match.group(0),
                        "weight": self.weights[category]
                    })
                    category_scores[category] += self.weights[category]
                    
        active_categories = sum(1 for score in category_scores.values() if score > 0)
        base_score = sum(category_scores.values())
        
        # Super-linear scaling based on multiple category activation
        multiplier = 1.0 + (0.15 * active_categories) if active_categories > 1 else 1.0
        final_score = min(1.0, base_score * multiplier)
        
        return {
            "social_engineering_score": float(final_score),
            "categories": category_scores,
            "matched_patterns": matched_patterns
        }

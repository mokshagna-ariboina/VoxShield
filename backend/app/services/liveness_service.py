import logging
import random
import re
from typing import Dict, Any

logger = logging.getLogger(__name__)

def levenshtein_distance(s1: str, s2: str) -> int:
    """Compute standard Levenshtein distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]

class LivenessService:
    """Generates and verifies liveness challenges."""
    
    def __init__(self):
        self.rng = random.SystemRandom()

    def generate_challenge(self, length: int = 6) -> Dict[str, Any]:
        """
        Generate a random digit sequence challenge.
        
        Args:
            length: number of digits to generate
            
        Returns:
            Dictionary with challenge string and display text
        """
        digits = "".join([str(self.rng.randint(0, 9)) for _ in range(length)])
        formatted_digits = "-".join(digits)
        
        return {
            "digits": digits,
            "challenge_text": f"Please repeat: {formatted_digits}"
        }

    def verify_response(self, expected_digits: str, spoken_text: str) -> Dict[str, Any]:
        """
        Verify if the spoken text matches the expected digits.
        
        Args:
            expected_digits: The correct digit string
            spoken_text: Transcript of the user's response
            
        Returns:
            Dictionary with verification results
        """
        # Extract only digits from spoken text
        # (Handling word-numbers like "one" would require a more complex parser, assuming raw digit matches for simplicity)
        spoken_digits = re.sub(r"[^\d]", "", spoken_text)
        
        dist = levenshtein_distance(expected_digits, spoken_digits)
        passed = dist <= 1
        
        return {
            "digits_matched": passed,
            "spoken_digits": spoken_digits,
            "edit_distance": dist,
            "passed": passed
        }

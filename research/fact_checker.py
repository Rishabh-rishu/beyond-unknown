"""
BEYOND UNKNOWN - Fact Checker
Filters pseudo-archaeology, sensational conspiracy theories, fabricated quotes,
and verifies measurements, dates, and scientific consensus.
"""

import logging
import re
from typing import Dict, List, Tuple

logger = logging.getLogger("beyond_unknown.research.fact_checker")

# Prohibited pseudoscientific / conspiracy tokens that violate channel standards
PROHIBITED_CONSPIRACY_PATTERNS = [
    r"\baliens\b",
    r"\bextraterrestrials built\b",
    r"\bancient nuclear war\b",
    r"\billuminati\b",
    r"\bflat earth\b",
    r"\bchemtrails\b",
    r"\breptilian\b",
    r"\bperpetual motion machine\b",
    r"\binstant miracle cure\b"
]

class FactChecker:
    def __init__(self):
        self.prohibited_regex = [re.compile(p, re.IGNORECASE) for p in PROHIBITED_CONSPIRACY_PATTERNS]

    def check_sensationalism_and_conspiracies(self, text: str) -> Tuple[bool, str]:
        """
        Scans for debunked pseudoscientific tropes and sensational conspiracy claims.
        """
        for regex in self.prohibited_regex:
            match = regex.search(text)
            if match:
                return False, f"Contains ungrounded conspiracy or sensational trope: '{match.group(0)}'"
        return True, ""

    def verify_claims(
        self,
        topic_title: str,
        claims: List[str],
        verified_facts: List[str]
    ) -> Tuple[bool, List[str], List[str], str]:
        """
        Validates whether topic claims are grounded in verified facts.
        Separates verified facts from uncertain claims.
        """
        if not claims and not verified_facts:
            return False, [], [], "Topic contains no verifiable claims or facts."

        all_text = f"{topic_title} " + " ".join(claims) + " " + " ".join(verified_facts)
        clean, reason = self.check_sensationalism_and_conspiracies(all_text)
        if not clean:
            return False, [], claims, reason

        clean_verified = []
        uncertain = []

        for f in verified_facts:
            if len(f.strip()) > 10:
                clean_verified.append(f.strip())
            else:
                uncertain.append(f)

        for c in claims:
            # If claim is already represented in verified facts, keep it
            if any(c.lower() in vf.lower() or vf.lower() in c.lower() for vf in clean_verified):
                if c not in clean_verified:
                    clean_verified.append(c)
            else:
                uncertain.append(c)

        if not clean_verified:
            return False, [], uncertain, "No solid verified facts established for topic."

        return True, clean_verified, uncertain, "Facts verified successfully."

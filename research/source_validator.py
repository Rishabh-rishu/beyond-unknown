"""
BEYOND UNKNOWN - Source Validator
Validates institutional authority, HTTPS protocol, and domain authenticity
for research sources.
"""

import logging
from typing import Dict, List, Tuple
from urllib.parse import urlparse

logger = logging.getLogger("beyond_unknown.research.validator")

# High-trust authoritative domains
AUTHORITATIVE_DOMAINS = {
    # Government & International bodies
    "asi.nic.in",
    "whc.unesco.org",
    "unesco.org",
    "science.nasa.gov",
    "nasa.gov",
    "earthobservatory.nasa.gov",
    "noaa.gov",
    "oceanservice.noaa.gov",
    "usgs.gov",
    "isro.gov.in",
    "gsi.gov.in",
    # Academic & Peer-reviewed journals
    "nature.com",
    "science.org",
    "cell.com",
    "pnas.org",
    "nobelprize.org",
    # Reputable encyclopedias & institutions
    "britannica.com",
    "britishmuseum.org",
    "si.edu",  # Smithsonian
    "eventhorizontelescope.org"
}

SECONDARY_DOMAINS = {
    "wikipedia.org",
    "wikidata.org",
    "nationalgeographic.com",
    "archaeology.org",
    "phys.org"
}

class SourceValidator:
    def __init__(self):
        self.auth_domains = AUTHORITATIVE_DOMAINS
        self.secondary_domains = SECONDARY_DOMAINS

    def extract_domain(self, url: str) -> str:
        try:
            parsed = urlparse(url)
            netloc = parsed.netloc.lower()
            if netloc.startswith("www."):
                netloc = netloc[4:]
            return netloc
        except Exception:
            return ""

    def validate_url(self, url: str) -> Tuple[bool, str, str]:
        """
        Validates URL protocol and domain tier.
        Returns (is_valid, domain, tier: 'authoritative' | 'secondary' | 'unknown')
        """
        if not url.startswith("https://") and not url.startswith("http://"):
            return False, "", "invalid"

        domain = self.extract_domain(url)
        if not domain:
            return False, "", "invalid"

        # Check domain or parent domain
        for auth in self.auth_domains:
            if domain == auth or domain.endswith("." + auth):
                return True, domain, "authoritative"

        for sec in self.secondary_domains:
            if domain == sec or domain.endswith("." + sec):
                return True, domain, "secondary"

        # Accept other .gov, .edu, .org with caution
        if domain.endswith(".gov") or domain.endswith(".edu") or domain.endswith(".gov.in") or domain.endswith(".nic.in"):
            return True, domain, "authoritative"

        return True, domain, "standard"

    def validate_source_list(self, urls: List[str]) -> Tuple[bool, List[str], str]:
        """
        Enforces at least two independent reliable sources.
        Wikipedia/Wikidata cannot be the sole source.
        """
        if not urls:
            return False, [], "No source URLs provided."

        valid_domains = set()
        has_authoritative = False

        for url in urls:
            is_valid, domain, tier = self.validate_url(url)
            if is_valid:
                valid_domains.add(domain)
                if tier == "authoritative":
                    has_authoritative = True

        if len(valid_domains) < 2:
            return False, list(valid_domains), f"Requires at least 2 independent domains (found: {len(valid_domains)})."

        # Check if solely secondary (e.g. Wikipedia only)
        non_wiki_domains = [d for d in valid_domains if "wikipedia" not in d and "wikidata" not in d]
        if not non_wiki_domains:
            return False, list(valid_domains), "Wikipedia/Wikidata cannot be the sole evidence source."

        return True, list(valid_domains), "Valid source diversity."

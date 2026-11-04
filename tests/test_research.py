"""
Unit tests for Research Validation, Domain Authority, and Fact Checking.
"""

import pytest
from research.source_validator import SourceValidator
from research.fact_checker import FactChecker
from research.researcher import Researcher

def test_source_validator_domains():
    sv = SourceValidator()

    # Authoritative domains
    ok, domain, tier = sv.validate_url("https://asi.nic.in/monuments.html")
    assert ok is True
    assert tier == "authoritative"

    ok, domain, tier = sv.validate_url("https://science.nasa.gov/mission/webb/")
    assert ok is True
    assert tier == "authoritative"

    ok, domain, tier = sv.validate_url("https://whc.unesco.org/en/list/242/")
    assert ok is True
    assert tier == "authoritative"

    ok, domain, tier = sv.validate_url("https://www.nature.com/articles/nature123")
    assert ok is True
    assert tier == "authoritative"

    # Secondary domain
    ok, domain, tier = sv.validate_url("https://en.wikipedia.org/wiki/Kailasa_Temple")
    assert ok is True
    assert tier == "secondary"

def test_source_diversity_rules():
    sv = SourceValidator()

    # Fails if fewer than 2 sources
    ok, domains, msg = sv.validate_source_list(["https://asi.nic.in/"])
    assert ok is False
    assert "at least 2 independent domains" in msg

    # Fails if Wikipedia is the sole source
    ok, domains, msg = sv.validate_source_list([
        "https://en.wikipedia.org/wiki/Kailasa",
        "https://wikidata.org/wiki/Q123"
    ])
    assert ok is False
    assert "Wikipedia/Wikidata cannot be the sole" in msg

    # Passes with 2 independent reliable domains
    ok, domains, msg = sv.validate_source_list([
        "https://asi.nic.in/monuments.html",
        "https://whc.unesco.org/en/list/242/"
    ])
    assert ok is True

def test_fact_checker_filters_conspiracy_theories():
    fc = FactChecker()

    # Prohibited claims
    clean, reason = fc.check_sensationalism_and_conspiracies("Ancient aliens built the Kailasa Temple.")
    assert clean is False
    assert "conspiracy" in reason.lower()

    clean, reason = fc.check_sensationalism_and_conspiracies("Evidence of ancient nuclear war found in Mohenjo-Daro.")
    assert clean is False

    # Valid factual claim
    clean, reason = fc.check_sensationalism_and_conspiracies(
        "Excavated top-down from basalt rock with over 200,000 tonnes removed."
    )
    assert clean is True

def test_researcher_rejection_flow(tmp_path):
    researcher = Researcher(data_dir=tmp_path)
    
    # Topic with invalid/insufficient sources
    bad_topic = {
        "id": "BAD-001",
        "title": "Fabricated Atlantis Discovery",
        "primary_sources": ["https://randomblog.com/post1"],
        "core_facts": ["Ancient aliens built a secret underwater base."]
    }

    dossier = researcher.research_topic(bad_topic)
    assert dossier.research_status == "rejected"
    assert len(dossier.verified_facts) == 0

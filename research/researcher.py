"""
BEYOND UNKNOWN - Research Orchestrator
Coordinates multi-source evidence retrieval, source validation, and fact checking.
Saves research dossiers to data/research_cache.json.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel
from config import settings
from research.source_validator import SourceValidator
from research.fact_checker import FactChecker

logger = logging.getLogger("beyond_unknown.researcher")

class ResearchDossier(BaseModel):
    topic_id: str
    topic: str
    country: str
    category: str
    main_claims: List[str]
    verified_facts: List[str]
    uncertain_claims: List[str]
    source_urls: List[str]
    source_titles: List[str]
    research_status: str  # "verified" | "rejected"

class Researcher:
    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or settings.DATA_DIR
        self.cache_file = self.data_dir / "research_cache.json"
        self.validator = SourceValidator()
        self.fact_checker = FactChecker()

    def _load_cache(self) -> Dict[str, Dict]:
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return {item.get("topic_id"): item for item in data if "topic_id" in item}
                    elif isinstance(data, dict):
                        return data
            except Exception as e:
                logger.error(f"Error loading research cache: {e}")
        return {}

    def _save_cache(self, cache: Dict[str, Dict]):
        items = list(cache.values())
        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2, ensure_ascii=False)

    def research_topic(self, topic: Dict) -> ResearchDossier:
        """
        Conducts research verification on a topic.
        Checks cached dossiers first, otherwise performs fresh validation.
        """
        topic_id = topic.get("id", "")
        title = topic.get("title", "")
        country = topic.get("country", "Global")
        category = topic.get("category", "General")
        sources = topic.get("primary_sources", [])
        core_facts = topic.get("core_facts", [])

        # Check existing cache
        cache = self._load_cache()
        if topic_id in cache:
            cached_item = cache[topic_id]
            logger.info(f"Using cached research dossier for {topic_id} ({cached_item.get('research_status')})")
            return ResearchDossier.model_validate(cached_item)

        logger.info(f"Conducting research validation for topic [{topic_id}] '{title}'...")

        # 1. Validate sources
        sources_ok, valid_domains, source_msg = self.validator.validate_source_list(sources)
        if not sources_ok:
            logger.warning(f"Topic {topic_id} failed source validation: {source_msg}")
            dossier = ResearchDossier(
                topic_id=topic_id,
                topic=title,
                country=country,
                category=category,
                main_claims=core_facts,
                verified_facts=[],
                uncertain_claims=core_facts,
                source_urls=sources,
                source_titles=[self.validator.extract_domain(s) for s in sources],
                research_status="rejected"
            )
            cache[topic_id] = dossier.model_dump()
            self._save_cache(cache)
            return dossier

        # 2. Verify facts and filter conspiracy/sensational claims
        facts_ok, verified_facts, uncertain_claims, fact_msg = self.fact_checker.verify_claims(
            topic_title=title,
            claims=core_facts,
            verified_facts=core_facts
        )

        if not facts_ok:
            logger.warning(f"Topic {topic_id} failed fact checking: {fact_msg}")
            dossier = ResearchDossier(
                topic_id=topic_id,
                topic=title,
                country=country,
                category=category,
                main_claims=core_facts,
                verified_facts=[],
                uncertain_claims=core_facts,
                source_urls=sources,
                source_titles=[self.validator.extract_domain(s) for s in sources],
                research_status="rejected"
            )
            cache[topic_id] = dossier.model_dump()
            self._save_cache(cache)
            return dossier

        # Topic verified successfully
        dossier = ResearchDossier(
            topic_id=topic_id,
            topic=title,
            country=country,
            category=category,
            main_claims=core_facts,
            verified_facts=verified_facts,
            uncertain_claims=uncertain_claims,
            source_urls=sources,
            source_titles=[self.validator.extract_domain(s) for s in sources],
            research_status="verified"
        )

        cache[topic_id] = dossier.model_dump()
        self._save_cache(cache)
        logger.info(f"Research status for {topic_id}: VERIFIED ({len(verified_facts)} verified facts, {len(valid_domains)} sources)")
        return dossier

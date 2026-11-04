"""
BEYOND UNKNOWN - Topic Management and Deduplication Engine
Handles:
- Loading and queuing topics
- Multi-tier duplicate detection (exact, normalized, token similarity, fact angle)
- Slot matching (morning vs evening)
- Tracking published and rejected topics
- Topic queue auto-replenishment via Gemini
"""

import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from pydantic import BaseModel
from config import settings
from ai.gemini_client import GeminiClient

logger = logging.getLogger("beyond_unknown.topics")

class TopicItem(BaseModel):
    id: str
    title: str
    normalized_title: str
    category: str
    country: str
    slot: str  # "morning" or "evening"
    core_facts: List[str]
    fact_angle: str
    primary_sources: List[str]

class GeneratedTopic(BaseModel):
    title: str
    category: str
    country: str
    slot: str
    core_facts: List[str]
    fact_angle: str
    primary_sources: List[str]

class NewTopicListSchema(BaseModel):
    topics: List[GeneratedTopic]

class TopicManager:
    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or settings.DATA_DIR
        self.topics_file = self.data_dir / "topics.json"
        self.published_file = self.data_dir / "published_tracker.json"
        self.rejected_file = self.data_dir / "rejected_topics.json"
        self.research_cache_file = self.data_dir / "research_cache.json"
        self.gemini_client = GeminiClient()

    def _load_json(self, path: Path) -> List[Dict]:
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data if isinstance(data, list) else []
            except Exception as e:
                logger.error(f"Error loading {path}: {e}")
                return []
        return []

    def _save_json(self, path: Path, data: List[Dict]):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @staticmethod
    def normalize_text(text: str) -> str:
        """Strip punctuation, lowercase, collapse whitespace."""
        cleaned = re.sub(r"[^a-zA-Z0-9\s]", "", text.lower())
        return re.sub(r"\s+", " ", cleaned).strip()

    @staticmethod
    def get_tokens(text: str) -> Set[str]:
        stop_words = {"the", "a", "an", "of", "and", "in", "to", "at", "for", "on", "with", "by", "is", "ancient", "mystery"}
        words = re.findall(r"\w+", text.lower())
        return {w for w in words if w not in stop_words and len(w) > 2}

    def calculate_similarity(self, title1: str, title2: str) -> float:
        """Token similarity combining Jaccard and overlap coefficient."""
        t1 = self.get_tokens(title1)
        t2 = self.get_tokens(title2)
        if not t1 or not t2:
            return 0.0
        intersection = t1.intersection(t2)
        union = t1.union(t2)
        jaccard = len(intersection) / len(union)
        overlap = len(intersection) / min(len(t1), len(t2))
        return max(jaccard, overlap)

    def is_duplicate(self, candidate_title: str, existing_topics: List[Dict]) -> Tuple[bool, str]:
        """
        Multi-tier duplicate detection:
        1. Exact match
        2. Normalized title match
        3. Token similarity > 0.65
        """
        cand_norm = self.normalize_text(candidate_title)
        
        for item in existing_topics:
            existing_title = item.get("title", "")
            # 1. Exact check
            if candidate_title.strip().lower() == existing_title.strip().lower():
                return True, f"Exact match with '{existing_title}' (ID: {item.get('id')})"
            
            # 2. Normalized check
            if cand_norm == self.normalize_text(existing_title):
                return True, f"Normalized match with '{existing_title}' (ID: {item.get('id')})"
            
            # 3. Token similarity
            sim = self.calculate_similarity(candidate_title, existing_title)
            if sim >= 0.65:
                return True, f"High token similarity ({sim:.2f}) with '{existing_title}' (ID: {item.get('id')})"

        return False, ""

    def get_published_ids(self) -> Set[str]:
        published = self._load_json(self.published_file)
        return {p.get("topic_id") for p in published if "topic_id" in p}

    def get_rejected_ids(self) -> Set[str]:
        rejected = self._load_json(self.rejected_file)
        return {r.get("topic_id") for r in rejected if "topic_id" in r}

    def list_remaining_topics(self, slot: Optional[str] = None) -> List[Dict]:
        all_topics = self._load_json(self.topics_file)
        published_ids = self.get_published_ids()
        rejected_ids = self.get_rejected_ids()

        remaining = []
        for t in all_topics:
            t_id = t.get("id")
            if t_id in published_ids or t_id in rejected_ids:
                continue
            if slot and t.get("slot", "").lower() != slot.lower():
                continue
            remaining.append(t)
        return remaining

    def get_next_topic(self, slot: str) -> Optional[Dict]:
        """
        Selects the next eligible un-published topic for the given slot ('morning' or 'evening').
        Auto-replenishes if topic queue is low.
        """
        slot = slot.lower()
        remaining = self.list_remaining_topics(slot=slot)

        # If queue for this slot is running low (<= 5), replenish
        if len(remaining) <= 5:
            logger.info(f"Low topic inventory for slot '{slot}' ({len(remaining)} remaining). Triggering replenishment...")
            self.replenish_topics(slot=slot, count=10)
            remaining = self.list_remaining_topics(slot=slot)

        if not remaining:
            logger.warning(f"No available topics found for slot '{slot}'.")
            return None

        # Return the first un-published topic
        selected = remaining[0]
        logger.info(f"Selected next topic: [{selected.get('id')}] {selected.get('title')} ({selected.get('category')})")
        return selected

    def mark_published(self, topic_id: str, youtube_video_id: str, publish_at_utc: str, title: str):
        published = self._load_json(self.published_file)
        # Avoid duplicate entries
        if any(p.get("topic_id") == topic_id for p in published):
            return

        published.append({
            "topic_id": topic_id,
            "youtube_video_id": youtube_video_id,
            "title": title,
            "published_at_utc": publish_at_utc,
            "status": "scheduled_or_published"
        })
        self._save_json(self.published_file, published)
        logger.info(f"Marked topic {topic_id} as published with video ID {youtube_video_id}")

    def mark_rejected(self, topic_id: str, reason: str):
        rejected = self._load_json(self.rejected_file)
        if any(r.get("topic_id") == topic_id for r in rejected):
            return

        rejected.append({
            "topic_id": topic_id,
            "reason": reason
        })
        self._save_json(self.rejected_file, rejected)
        logger.info(f"Marked topic {topic_id} as rejected: {reason}")

    def replenish_topics(self, slot: str, count: int = 10):
        """
        Ask Gemini to discover new factually grounded topics with reliable sources.
        """
        all_topics = self._load_json(self.topics_file)
        slot_categories = {
            "morning": ["Hidden India", "Ancient history and technology"],
            "evening": ["Global mysteries", "Science and space", "Strange nature and geography"]
        }.get(slot, ["Hidden India", "Global mysteries"])

        prompt = f"""
        Discover {count} unique, factual, highly engaging documentary topics for the channel BEYOND UNKNOWN.
        Slot: {slot.upper()}
        Eligible Categories: {', '.join(slot_categories)}
        
        Requirements:
        1. Grounded in authentic archaeological, NASA, UNESCO, USGS, or peer-reviewed science.
        2. Must have at least 2 independent verifiable facts.
        3. No conspiracy theories or fabricated sensationalism.
        4. Include primary source URL references (e.g., UNESCO, ASI, NASA, Nature, Britannica).
        """

        try:
            result: NewTopicListSchema = self.gemini_client.generate_structured_content(
                prompt=prompt,
                response_schema=NewTopicListSchema
            )
            
            added_count = 0
            curr_max_num = len(all_topics)
            
            for item in result.topics:
                # Check duplicates against all known topics
                is_dup, reason = self.is_duplicate(item.title, all_topics)
                if is_dup:
                    logger.info(f"Skipping duplicate generated topic '{item.title}': {reason}")
                    continue
                
                curr_max_num += 1
                prefix = "BU-GEN"
                if "india" in item.category.lower():
                    prefix = "BU-IND"
                elif "space" in item.category.lower() or "science" in item.category.lower():
                    prefix = "BU-SCI"
                elif "nature" in item.category.lower():
                    prefix = "BU-NAT"
                elif "ancient" in item.category.lower():
                    prefix = "BU-ANC"
                else:
                    prefix = "BU-GLO"

                new_id = f"{prefix}-{curr_max_num:03d}"
                new_topic = {
                    "id": new_id,
                    "title": item.title,
                    "normalized_title": self.normalize_text(item.title).replace(" ", "_"),
                    "category": item.category,
                    "country": item.country,
                    "slot": slot,
                    "core_facts": item.core_facts,
                    "fact_angle": item.fact_angle,
                    "primary_sources": item.primary_sources
                }
                all_topics.append(new_topic)
                added_count += 1

            if added_count > 0:
                self._save_json(self.topics_file, all_topics)
                logger.info(f"Successfully replenished {added_count} new unique topics to {self.topics_file}")

        except Exception as e:
            logger.error(f"Failed to replenish topics via Gemini: {e}")

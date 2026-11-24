"""Research Agent — Real-time feed ingestion, entity extraction, claim proposal."""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from agents.base import BaseAgent, AgentResult


class ResearchAgent(BaseAgent):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("research-agent", config)
        self.feeds: List[str] = config.get("feeds", []) if config else []
        self.keywords: List[str] = config.get("keywords", []) if config else []
        self.max_items: int = config.get("max_items", 50) if config else 50
        self.claims_proposed: List[Dict[str, Any]] = []

    def execute(self, task: Dict[str, Any]) -> AgentResult:
        channel_id = task.get("channel_id", "unknown")
        topic = task.get("topic", "")
        search_date = task.get("search_date", datetime.utcnow().date().isoformat())

        ctx = self.get_channel_context()
        feeds = ctx.get("search_context", {}).get("feeds_configured", self.feeds)
        keywords = ctx.get("search_context", {}).get("keywords", self.keywords)

        # Simulated feed ingestion (replace with real API calls in production)
        proposed_claims = self._simulate_feed_ingestion(feeds, keywords, topic, search_date)

        self.claims_proposed = proposed_claims

        self._record_trajectory("execute", {
            "channel_id": channel_id,
            "topic": topic,
            "feeds": feeds,
            "claims_proposed": len(proposed_claims),
            "confidence": 75.0,
            "errors": [],
        })

        return AgentResult(
            agent_id=self.agent_id,
            status="success",
            output={
                "claims_proposed": len(proposed_claims),
                "claims": proposed_claims,
                "feeds_polled": feeds,
                "search_date": search_date,
                "checklist_incomplete": False,
            },
            confidence=75.0,
        )

    def _simulate_feed_ingestion(self, feeds, keywords, topic, search_date) -> List[Dict[str, Any]]:
        """Simulate feed ingestion. Replace with real API calls."""
        claims = []
        for i, feed in enumerate(feeds[:3]):
            claims.append({
                "claim_text": f"Claim {i+1} regarding {topic} from {feed}",
                "source_url": f"https://example.com/{feed.lower().replace(' ', '-')}/{search_date}",
                "published_at": search_date,
                "source_type": "independent_reporting",
                "confidence": 70 + (i * 5),
                "entities": [{"type": "topic", "value": topic}],
                "feed_source": feed,
            })
        return claims

    def extract_insights(self, episode: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [{
            "content": f"Research for {episode.get('channel_id')}: {len(self.claims_proposed)} claims from {len(self.feeds)} feeds",
            "collection": "best_practices",
            "effectiveness": 0.8,
        }]

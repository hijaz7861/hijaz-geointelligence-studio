"""Producer Agent — Editorial strategy, story selection, risk assessment."""

from typing import Any, Dict, List, Optional
from agents.base import BaseAgent, AgentResult


class ProducerAgent(BaseAgent):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("producer-agent", config)
        self.max_stories_per_day = config.get("max_stories_per_day", 3) if config else 3
        self.risk_threshold = config.get("risk_threshold", 0.7) if config else 0.7

    def execute(self, task: Dict[str, Any]) -> AgentResult:
        channel_id = task.get("channel_id", "unknown")
        topic = task.get("topic", "")
        research_output = task.get("previous_output", {})
        claims = research_output.get("claims", []) if isinstance(research_output, dict) else []

        ctx = self.get_channel_context()
        purpose = ctx.get("purpose", "")
        target_country = ctx.get("target_country", "")

        # Score and select stories
        selected = self._select_stories(claims, purpose, target_country)

        # Risk assessment
        risk_score = self._assess_risk(selected, target_country)

        # Editorial angle
        angle = self._determine_angle(selected, purpose)

        self._record_trajectory("execute", {
            "channel_id": channel_id,
            "topic": topic,
            "claims_available": len(claims),
            "claims_selected": len(selected),
            "risk_score": risk_score,
            "angle": angle,
            "confidence": 85.0,
            "errors": [],
        })

        return AgentResult(
            agent_id=self.agent_id,
            status="success",
            output={
                "selected_claims": selected,
                "risk_score": risk_score,
                "editorial_angle": angle,
                "publish_recommendation": "proceed" if risk_score < self.risk_threshold else "review",
                "checklist_incomplete": False,
            },
            confidence=85.0,
        )

    def _select_stories(self, claims, purpose, target_country):
        return claims[:self.max_stories_per_day]

    def _assess_risk(self, claims, target_country):
        # Simplified risk scoring
        if not claims:
            return 0.0
        # Higher risk for military/defamation topics
        risk = 0.3
        for c in claims:
            text = c.get("claim_text", "").lower()
            if any(kw in text for kw in ["military", "attack", "killed", "defamation"]):
                risk += 0.2
        return min(risk, 1.0)

    def _determine_angle(self, claims, purpose):
        if not claims:
            return "No stories available"
        return f"Focus on {claims[0].get('claim_text', 'latest update')[:60]}..."

    def extract_insights(self, episode):
        return [{"content": f"Producer selected {len(self._select_stories([], '', ''))} stories", "collection": "best_practices", "effectiveness": 0.8}]

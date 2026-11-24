"""Script Agent — Claim-to-narrative, cited draft generation."""

from typing import Any, Dict, List, Optional
from agents.base import BaseAgent, AgentResult


class ScriptAgent(BaseAgent):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("script-agent", config)
        self.language = config.get("language", "en") if config else "en"
        self.include_editorial = config.get("include_editorial", True) if config else True

    def execute(self, task: Dict[str, Any]) -> AgentResult:
        channel_id = task.get("channel_id", "unknown")
        topic = task.get("topic", "")
        producer_output = task.get("previous_output", {})
        claims = producer_output.get("selected_claims", []) if isinstance(producer_output, dict) else []

        ctx = self.get_channel_context()
        lang = ctx.get("language", self.language)

        # Generate cited script
        script_lines = []
        script_lines.append(f"# {topic}")
        script_lines.append(f"\nDraft language: {lang}")
        script_lines.append(f"Channel: {ctx.get('channel_name', channel_id)}")
        script_lines.append("")

        for claim in claims:
            claim_text = claim.get("claim_text", "Unknown claim")
            script_lines.append(f"[[claim:{claim_text}]]")
            script_lines.append(f"This segment covers: {claim_text}")
            script_lines.append("")

        if self.include_editorial:
            script_lines.append("[EDITORIAL] The analysis above is based on available public sources.")
            script_lines.append("")

        script_lines.append("HUMAN REVIEW REQUIRED")

        draft = "\n".join(script_lines)
        claim_count = len(claims)

        self._record_trajectory("execute", {
            "channel_id": channel_id,
            "topic": topic,
            "claim_count": claim_count,
            "language": lang,
            "confidence": 80.0,
            "errors": [],
        })

        return AgentResult(
            agent_id=self.agent_id,
            status="success",
            output={
                "draft": draft,
                "claim_marker_count": claim_count,
                "language": lang,
                "checklist_incomplete": False,
            },
            confidence=80.0,
        )

    def extract_insights(self, episode):
        return [{"content": f"Script generated with {self.execute.__code__.co_varnames.count('claim')} claims", "collection": "best_practices", "effectiveness": 0.75}]

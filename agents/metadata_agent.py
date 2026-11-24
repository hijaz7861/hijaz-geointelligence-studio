"""Metadata Agent — YouTube title/description/source metadata draft."""

from typing import Any, Dict, List, Optional
from agents.base import BaseAgent, AgentResult


class MetadataAgent(BaseAgent):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("metadata-agent", config)

    def execute(self, task: Dict[str, Any]) -> AgentResult:
        channel_id = task.get("channel_id", "unknown")
        topic = task.get("topic", "")
        ctx = self.get_channel_context()
        script_output = task.get("previous_output", {})
        draft = script_output.get("draft", "") if isinstance(script_output, dict) else ""

        channel_name = ctx.get("channel_name", channel_id)
        language = ctx.get("language", "en")

        metadata = {
            "title": f"{topic} | {channel_name}",
            "description": f"Analysis of {topic}. Sources verified. Human review required.\n\n{draft[:200]}...",
            "tags": [topic, channel_name, language, "geopolitics", "analysis"],
            "language": language,
            "release_status": "draft_blocked",
            "publish_ready": False,
            "channel_id": channel_id,
        }

        self._record_trajectory("execute", {
            "channel_id": channel_id,
            "topic": topic,
            "release_status": "draft_blocked",
            "confidence": 85.0,
            "errors": [],
        })

        return AgentResult(
            agent_id=self.agent_id,
            status="success",
            output=metadata,
            confidence=85.0,
        )

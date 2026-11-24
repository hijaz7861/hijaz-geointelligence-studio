"""Veri Strict Agent — Process guardian, error hunter, quality enforcer."""

from typing import Any, Dict, List, Optional
from agents.base import BaseAgent, AgentResult


class VeriStrictAgent(BaseAgent):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("veri-strict-agent", config)
        self.quality_threshold = config.get("quality_threshold", 70) if config else 70
        self.auto_fix_enabled = config.get("auto_fix", True) if config else True

    def execute(self, task: Dict[str, Any]) -> AgentResult:
        channel_id = task.get("channel_id", "unknown")
        pipeline_output = task.get("pipeline_output", {})

        steps = pipeline_output.get("steps", [])
        errors_found = 0
        auto_fixes = 0
        quality_scores = {}

        for step in steps:
            status = step.get("status", "unknown")
            if status == "failed":
                errors_found += 1
            elif status == "completed":
                quality_scores[step["name"]] = 90.0
            elif status == "blocked":
                quality_scores[step["name"]] = 60.0
                errors_found += 1

        overall_quality = sum(quality_scores.values()) / len(quality_scores) if quality_scores else 0.0

        if overall_quality < self.quality_threshold:
            escalation = "human_review_required"
        else:
            escalation = "none"

        self._record_trajectory("execute", {
            "channel_id": channel_id,
            "steps_checked": len(steps),
            "errors_found": errors_found,
            "overall_quality": overall_quality,
            "escalation": escalation,
            "confidence": 95.0,
            "errors": [],
        })

        return AgentResult(
            agent_id=self.agent_id,
            status="success" if overall_quality >= self.quality_threshold else "warning",
            output={
                "steps_checked": len(steps),
                "errors_found": errors_found,
                "auto_fixes_applied": auto_fixes,
                "quality_scores": quality_scores,
                "overall_quality": overall_quality,
                "escalation": escalation,
                "publish_approved": overall_quality >= self.quality_threshold and errors_found == 0,
            },
            confidence=95.0,
        )

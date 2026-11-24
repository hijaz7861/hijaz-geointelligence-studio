"""Compliance Agent — Rights, PII, OPSEC, policy enforcement."""

from typing import Any, Dict, List, Optional
from agents.base import BaseAgent, AgentResult


class ComplianceAgent(BaseAgent):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("compliance-agent", config)
        self.opsec_delay_hours = config.get("opsec_delay_hours", 24) if config else 24
        self.pii_patterns = ["name", "face", "location", "coordinate"]

    def execute(self, task: Dict[str, Any]) -> AgentResult:
        channel_id = task.get("channel_id", "unknown")
        ctx = self.get_channel_context()
        script_output = task.get("script_output", task.get("previous_output", {}))
        if isinstance(script_output, dict) and "output" in script_output:
            script_output = script_output["output"]
        draft = script_output.get("draft", "") if isinstance(script_output, dict) else ""

        # Check for PII in draft
        pii_flags = self._check_pii(draft)
        # Check rights status
        rights_status = self._check_rights(ctx)
        # OPSEC delay
        opsec_status = self._check_opsec(ctx)

        blockers = []
        if pii_flags:
            blockers.append("PII detected - redaction required")
        if rights_status != "cleared":
            blockers.append("Media rights not cleared")
        if opsec_status != "clear":
            blockers.append(f"OPSEC delay: {self.opsec_delay_hours}h required")

        status = "blocked" if blockers else "success"

        self._record_trajectory("execute", {
            "channel_id": channel_id,
            "pii_flags": pii_flags,
            "rights_status": rights_status,
            "opsec_status": opsec_status,
            "blockers": blockers,
            "confidence": 90.0,
            "errors": [],
        })

        return AgentResult(
            agent_id=self.agent_id,
            status=status,
            output={
                "pii_flags": pii_flags,
                "rights_status": rights_status,
                "opsec_status": opsec_status,
                "blockers": blockers,
                "checklist_incomplete": len(blockers) > 0,
            },
            confidence=90.0,
            warnings=blockers,
        )

    def _check_pii(self, text: str) -> List[str]:
        flags = []
        for pattern in self.pii_patterns:
            if pattern in text.lower():
                flags.append(pattern)
        return flags

    def _check_rights(self, ctx: Dict[str, Any]) -> str:
        # Simplified: assume cleared for now
        return "cleared"

    def _check_opsec(self, ctx: Dict[str, Any]) -> str:
        # Simplified: assume clear for now
        return "clear"

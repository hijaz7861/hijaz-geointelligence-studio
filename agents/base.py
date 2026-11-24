"""Base classes for all agents in the Hijaz GeoIntelligence Studio."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class AgentResult:
    agent_id: str
    status: str  # "success", "warning", "error", "blocked"
    output: Any
    confidence: float = 0.0  # 0-100
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "status": self.status,
            "output": self.output,
            "confidence": self.confidence,
            "errors": self.errors,
            "warnings": self.warnings,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }


class BaseAgent(ABC):
    """Abstract base class for all production agents."""

    def __init__(self, agent_id: str, config: Optional[Dict[str, Any]] = None):
        self.agent_id = agent_id
        self.config = config or {}
        self.channel_context: Optional[Dict[str, Any]] = None
        self.trajectory: List[Dict[str, Any]] = []
        self._setup_logger()

    def _setup_logger(self):
        self.logger = logging.getLogger(f"agent.{self.agent_id}")

    def set_channel_context(self, context: Dict[str, Any]):
        """Inject channel-specific context into the agent."""
        self.channel_context = context
        self.logger.info(f"Channel context set: {context.get('channel_id')}")

    def get_channel_context(self) -> Dict[str, Any]:
        return self.channel_context or {}

    def _record_trajectory(self, step: str, data: Dict[str, Any]):
        self.trajectory.append({
            "step": step,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data,
        })

    def get_recent_trajectory(self, window: int = 10) -> List[Dict[str, Any]]:
        return self.trajectory[-window:]

    def has_completed_episode(self) -> bool:
        return len(self.trajectory) > 0 and self.trajectory[-1].get("step") == "completed"

    def get_episode(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "trajectory": self.trajectory,
            "timestamp": datetime.utcnow().isoformat(),
        }

    @abstractmethod
    def execute(self, task: Dict[str, Any]) -> AgentResult:
        """Execute the agent's primary task."""
        pass

    def validate_output(self, result: AgentResult) -> bool:
        """Override for agent-specific validation."""
        return result.status in ("success", "warning")

    def extract_insights(self, episode: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract learnings from an episode for MLO."""
        return []

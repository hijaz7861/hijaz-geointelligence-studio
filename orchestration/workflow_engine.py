"""Workflow Engine — durable task orchestration for multi-channel production."""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum


class WorkflowStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    MANUAL_REVIEW = "manual_review"


@dataclass
class WorkflowStep:
    name: str
    agent_id: str
    status: WorkflowStatus = WorkflowStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retries: int = 0
    max_retries: int = 3
    output: Any = None
    error: Optional[str] = None
    depends_on: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "agent_id": self.agent_id,
            "status": self.status.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "retries": self.retries,
            "error": self.error,
            "depends_on": self.depends_on,
        }


@dataclass
class WorkflowRun:
    run_id: str
    channel_id: str
    topic: str
    status: WorkflowStatus = WorkflowStatus.PENDING
    steps: List[WorkflowStep] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    quality_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "channel_id": self.channel_id,
            "topic": self.topic,
            "status": self.status.value,
            "steps": [s.to_dict() for s in self.steps],
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "quality_score": self.quality_score,
        }


# Default pipeline steps
DEFAULT_PIPELINE = [
    {"name": "research", "agent_id": "research-agent", "depends_on": []},
    {"name": "producer_decision", "agent_id": "producer-agent", "depends_on": ["research"]},
    {"name": "script_generation", "agent_id": "script-agent", "depends_on": ["producer_decision"]},
    {"name": "translation", "agent_id": "translation-agent", "depends_on": ["script_generation"]},
    {"name": "fact_check", "agent_id": "fact-check-agent", "depends_on": ["script_generation"]},
    {"name": "compliance", "agent_id": "compliance-agent", "depends_on": ["script_generation", "fact_check"]},
    {"name": "review_gate", "agent_id": "review-gate-agent", "depends_on": ["compliance"]},
    {"name": "render", "agent_id": "render-agent", "depends_on": ["review_gate"]},
    {"name": "metadata", "agent_id": "metadata-agent", "depends_on": ["render"]},
    {"name": "release_bundle", "agent_id": "release-bundle-agent", "depends_on": ["metadata"]},
]


class WorkflowEngine:
    """Orchestrates multi-step production workflows per channel."""

    def __init__(self):
        self.runs: Dict[str, WorkflowRun] = {}
        self.agents: Dict[str, Any] = {}

    def register_agent(self, agent_id: str, agent: Any):
        self.agents[agent_id] = agent

    def create_run(self, channel_id: str, topic: str, pipeline: List[Dict] = None) -> str:
        import uuid
        run_id = f"run_{uuid.uuid4().hex[:12]}"
        pipeline = pipeline or DEFAULT_PIPELINE
        run = WorkflowRun(run_id=run_id, channel_id=channel_id, topic=topic)
        for step_def in pipeline:
            run.steps.append(WorkflowStep(
                name=step_def["name"],
                agent_id=step_def["agent_id"],
                depends_on=step_def.get("depends_on", []),
            ))
        self.runs[run_id] = run
        return run_id

    def execute_run(self, run_id: str, channel_context: Dict[str, Any]) -> Dict[str, Any]:
        run = self.runs.get(run_id)
        if not run:
            return {"error": f"Run {run_id} not found"}

        run.status = WorkflowStatus.RUNNING
        context = dict(channel_context)

        for step in run.steps:
            # Check dependencies
            deps_met = all(
                self._step_status(run, dep) == WorkflowStatus.COMPLETED
                for dep in step.depends_on
            )
            if not deps_met:
                step.status = WorkflowStatus.BLOCKED
                continue

            # Execute step
            step.status = WorkflowStatus.RUNNING
            step.started_at = datetime.utcnow()

            agent = self.agents.get(step.agent_id)
            if not agent:
                step.status = WorkflowStatus.FAILED
                step.error = f"Agent {step.agent_id} not registered"
                run.status = WorkflowStatus.FAILED
                break

            agent.set_channel_context(context)

            try:
                task = {"step": step.name, "channel_id": run.channel_id, "topic": run.topic}
                task["previous_output"] = context.get(f"{step.depends_on[0]}_output" if step.depends_on else "", {})
                # Also pass script output if available
                if "script_generation_output" in context:
                    task["script_output"] = context["script_generation_output"]

                result = agent.execute(task)
                step.output = result.to_dict() if hasattr(result, "to_dict") else result
                step.status = WorkflowStatus.COMPLETED
                step.completed_at = datetime.utcnow()

                # Update context with step output
                context[f"{step.name}_output"] = step.output

                # Check if blocked
                if isinstance(result, object) and hasattr(result, "status"):
                    if result.status == "blocked":
                        step.status = WorkflowStatus.BLOCKED
                        run.status = WorkflowStatus.BLOCKED
                        break

            except Exception as e:
                step.error = str(e)
                step.retries += 1
                if step.retries >= step.max_retries:
                    step.status = WorkflowStatus.FAILED
                    run.status = WorkflowStatus.FAILED
                    break
                else:
                    step.status = WorkflowStatus.PENDING  # retry

        if run.status == WorkflowStatus.RUNNING:
            run.status = WorkflowStatus.COMPLETED
            run.completed_at = datetime.utcnow()

        return run.to_dict()

    def _step_status(self, run: WorkflowRun, step_name: str) -> WorkflowStatus:
        for step in run.steps:
            if step.name == step_name:
                return step.status
        return WorkflowStatus.PENDING

    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        run = self.runs.get(run_id)
        return run.to_dict() if run else None

    def list_runs(self, channel_id: Optional[str] = None) -> List[Dict[str, Any]]:
        runs = list(self.runs.values())
        if channel_id:
            runs = [r for r in runs if r.channel_id == channel_id]
        return [r.to_dict() for r in runs]

"""Meta-Learning Orchestrator — detects misbehavior, teaches agents, shares knowledge."""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from agents.base import BaseAgent, AgentResult


@dataclass
class Anomaly:
    agent_id: str
    pattern: str
    severity: str  # "low", "medium", "high", "critical"
    suggested_intervention: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class TeachingSession:
    agent_id: str
    anomaly: Anomaly
    explanation: str
    demonstration: str
    practice_task: str
    updated_prompt: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


class BehaviorMonitor:
    """Detects when an agent deviates from expected patterns."""

    ANOMALY_PATTERNS = {
        "repeated_errors": {"threshold": 3, "action": "intervene_and_teach"},
        "confidence_collapse": {"threshold": 0.4, "action": "request_human_demo"},
        "checklist_evasion": {"pattern": "marked_done_but_incomplete", "action": "enforce_checklist"},
        "resource_abuse": {"pattern": "usage_over_2x_allocated", "action": "throttle_and_optimize"},
    }

    def detect(self, agent_id: str, trajectory: List[Dict[str, Any]]) -> List[Anomaly]:
        anomalies = []
        if not trajectory:
            return anomalies

        # Check for repeated errors
        errors = [t for t in trajectory if t.get("data", {}).get("errors")]
        if len(errors) >= self.ANOMALY_PATTERNS["repeated_errors"]["threshold"]:
            anomalies.append(Anomaly(
                agent_id=agent_id,
                pattern="repeated_errors",
                severity="high",
                suggested_intervention="intervene_and_teach",
            ))

        # Check for low confidence
        confidences = [t.get("data", {}).get("confidence", 100) for t in trajectory]
        if confidences and min(confidences) < 40:
            anomalies.append(Anomaly(
                agent_id=agent_id,
                pattern="confidence_collapse",
                severity="high",
                suggested_intervention="request_human_demo",
            ))

        # Check for checklist evasion
        for t in trajectory:
            status = t.get("data", {}).get("status")
            if status == "done" and t.get("data", {}).get("checklist_incomplete"):
                anomalies.append(Anomaly(
                    agent_id=agent_id,
                    pattern="checklist_evasion",
                    severity="medium",
                    suggested_intervention="enforce_checklist_completion",
                ))
                break

        return anomalies


class CorrectionEngine:
    """Generates fixes and teaches agents why."""

    def teach(self, agent_id: str, anomaly: Anomaly, context: Dict[str, Any]) -> TeachingSession:
        explanations = {
            "repeated_errors": f"Agent {agent_id} has repeated errors. Reviewing common failure patterns and correcting approach.",
            "confidence_collapse": f"Agent {agent_id} confidence dropped below 40%. Needs additional training or human demonstration.",
            "checklist_evasion": f"Agent {agent_id} marked task done but checklist incomplete. Enforcing completion.",
        }
        explanation = explanations.get(anomaly.pattern, f"Unknown anomaly: {anomaly.pattern}")

        demonstration = f"Correct approach for {agent_id}: Follow full checklist, verify all outputs, maintain confidence above threshold."

        practice_task = f"Simulated task for {agent_id}: Complete the same task with strict checklist enforcement."

        updated_prompt = f"[CORRECTION APPLIED] {agent_id}: {explanation}\nAlways verify outputs against checklist before marking done."

        return TeachingSession(
            agent_id=agent_id,
            anomaly=anomaly,
            explanation=explanation,
            demonstration=demonstration,
            practice_task=practice_task,
            updated_prompt=updated_prompt,
        )


class SharedKnowledgeBase:
    """Central repository for cross-agent learning."""

    def __init__(self):
        self.insights: List[Dict[str, Any]] = []
        self.collections: Dict[str, List[Dict[str, Any]]] = {
            "corrections": [],
            "best_practices": [],
            "domain_knowledge": [],
            "failure_modes": [],
        }

    def deposit(self, agent_id: str, collection: str, insight: Dict[str, Any]):
        entry = {
            "source_agent": agent_id,
            "collection": collection,
            "content": insight.get("content", ""),
            "timestamp": datetime.utcnow().isoformat(),
            "usage_count": 0,
            "effectiveness_score": insight.get("effectiveness", 0.5),
        }
        self.collections.setdefault(collection, []).append(entry)
        self.insights.append(entry)

    def withdraw(self, query: str, collections: List[str] = None, k: int = 5) -> List[Dict[str, Any]]:
        if collections is None:
            collections = list(self.collections.keys())
        results = []
        for coll in collections:
            for entry in self.collections.get(coll, []):
                if query.lower() in entry["content"].lower():
                    results.append(entry)
        # Sort by effectiveness
        results.sort(key=lambda x: x["effectiveness_score"], reverse=True)
        return results[:k]

    def propagate_lesson(self, lesson: str, from_agent: str, to_agents: List[str]):
        for target in to_agents:
            self.deposit(target, "corrections", {
                "content": f"[From {from_agent}] {lesson}",
                "effectiveness": 0.8,
            })

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_insights": len(self.insights),
            "collections": {k: len(v) for k, v in self.collections.items()},
        }


class ExperienceReplay:
    """Stores and replays episodes for learning."""

    def __init__(self):
        self.episodes: List[Dict[str, Any]] = []
        self.success_patterns: Dict[str, int] = {}
        self.failure_patterns: Dict[str, int] = {}

    def record_episode(self, episode: Dict[str, Any]):
        self.episodes.append(episode)
        quality = episode.get("overall_quality", 0)
        if quality >= 90:
            pattern = self._extract_pattern(episode, "success")
            self.success_patterns[pattern] = self.success_patterns.get(pattern, 0) + 1
        elif quality < 70:
            pattern = self._extract_pattern(episode, "failure")
            self.failure_patterns[pattern] = self.failure_patterns.get(pattern, 0) + 1

    def _extract_pattern(self, episode: Dict[str, Any], outcome: str) -> str:
        agents = episode.get("agents_involved", [])
        anomalies = [a.get("pattern") for a in episode.get("anomalies", [])]
        return f"{outcome}:agents={','.join(agents)}:anomalies={','.join(anomalies)}"

    def retrieve_similar(self, context: Dict[str, Any], k: int = 5) -> List[Dict[str, Any]]:
        # Simple keyword-based retrieval (replace with vector search in production)
        query = json.dumps(context).lower()
        results = []
        for ep in self.episodes:
            ep_text = json.dumps(ep).lower()
            # Simple overlap score
            overlap = len(set(query.split()) & set(ep_text.split()))
            if overlap > 0:
                results.append((overlap, ep))
        results.sort(key=lambda x: x[0], reverse=True)
        return [r[1] for r in results[:k]]

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_episodes": len(self.episodes),
            "success_patterns": len(self.success_patterns),
            "failure_patterns": len(self.failure_patterns),
        }


class MetaLearningOrchestrator(BaseAgent):
    """High-level agent that monitors, teaches, learns, and evolves all agents."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("meta-learning-orchestrator", config)
        self.behavior_monitor = BehaviorMonitor()
        self.correction_engine = CorrectionEngine()
        self.knowledge_base = SharedKnowledgeBase()
        self.experience_replay = ExperienceReplay()
        self.agents: Dict[str, Any] = {}
        self.teaching_log: List[TeachingSession] = []
        self.evolution_log: List[Dict[str, Any]] = []

    def register_agent(self, agent_id: str, agent: Any):
        self.agents[agent_id] = agent
        self.logger.info(f"Registered agent: {agent_id}")

    def execute(self, task: Dict[str, Any]) -> AgentResult:
        action = task.get("action", "monitor")

        if action == "monitor":
            result = self.run_monitoring_cycle(task.get("heartbeats", {}))
        elif action == "teach":
            result = self.teach_agent(task.get("agent_id"), task.get("anomaly"), task.get("context", {}))
        elif action == "learn":
            result = self.learn_from_episode(task.get("episode", {}))
        elif action == "evolve":
            result = self.run_evolution_cycle()
        elif action == "share":
            result = self.share_insights(task.get("from_agent"), task.get("to_agents", []), task.get("lesson", ""))
        else:
            return AgentResult(agent_id=self.agent_id, status="error", output=None, errors=[f"Unknown action: {action}"])

        return AgentResult(
            agent_id=self.agent_id,
            status="success",
            output=result,
            confidence=90.0,
        )

    def run_monitoring_cycle(self, heartbeats: Dict[str, Any]) -> Dict[str, Any]:
        """Monitor all agents for anomalies."""
        anomalies_found = []
        for agent_id, heartbeat in heartbeats.items():
            trajectory = heartbeat.get("trajectory", [])
            anomalies = self.behavior_monitor.detect(agent_id, trajectory)
            for anomaly in anomalies:
                session = self.correction_engine.teach(agent_id, anomaly, heartbeat)
                self.teaching_log.append(session)
                anomalies_found.append({
                    "agent_id": agent_id,
                    "pattern": anomaly.pattern,
                    "severity": anomaly.severity,
                    "taught": True,
                })
                # Propagate lesson to similar agents
                similar_agents = [aid for aid in self.agents if aid != agent_id]
                self.knowledge_base.propagate_lesson(
                    lesson=session.explanation,
                    from_agent=agent_id,
                    to_agents=similar_agents[:3],
                )
        return {
            "agents_monitored": len(heartbeats),
            "anomalies_found": len(anomalies_found),
            "anomalies": anomalies_found,
            "knowledge_base_stats": self.knowledge_base.get_stats(),
        }

    def teach_agent(self, agent_id: str, anomaly: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        if isinstance(anomaly, dict):
            anomaly = Anomaly(
                agent_id=agent_id,
                pattern=anomaly.get("pattern", "unknown"),
                severity=anomaly.get("severity", "medium"),
                suggested_intervention=anomaly.get("intervention", "teach"),
            )
        session = self.correction_engine.teach(agent_id, anomaly, context)
        self.teaching_log.append(session)
        return {
            "teaching_session": {
                "agent_id": session.agent_id,
                "explanation": session.explanation,
                "demonstration": session.demonstration,
                "updated_prompt": session.updated_prompt,
            }
        }

    def learn_from_episode(self, episode: Dict[str, Any]) -> Dict[str, Any]:
        self.experience_replay.record_episode(episode)
        # Deposit insights
        for agent_id in episode.get("agents_involved", []):
            self.knowledge_base.deposit(agent_id, "best_practices", {
                "content": f"Episode {episode.get('run_id')}: quality={episode.get('overall_quality', 0)}",
                "effectiveness": episode.get("overall_quality", 0) / 100.0,
            })
        return {
            "episode_recorded": True,
            "experience_stats": self.experience_replay.get_stats(),
            "knowledge_stats": self.knowledge_base.get_stats(),
        }

    def run_evolution_cycle(self) -> Dict[str, Any]:
        """Daily/weekly evolution of agent prompts and policies."""
        improvements = []

        # Promote success patterns
        for pattern, count in self.experience_replay.success_patterns.items():
            if count >= 3:
                improvements.append({
                    "type": "promote_pattern",
                    "pattern": pattern,
                    "count": count,
                    "action": "Add as few-shot example to relevant agents",
                })

        # Prevent failure patterns
        for pattern, count in self.experience_replay.failure_patterns.items():
            if count >= 2:
                improvements.append({
                    "type": "prevent_pattern",
                    "pattern": pattern,
                    "count": count,
                    "action": "Add as negative example to relevant agents",
                })

        # Generalize high-effectiveness corrections
        for insight in self.knowledge_base.insights:
            if insight.get("effectiveness_score", 0) > 0.8 and insight.get("usage_count", 0) > 3:
                improvements.append({
                    "type": "generalize_correction",
                    "insight": insight["content"],
                    "effectiveness": insight["effectiveness_score"],
                    "action": "Promote to base prompt for all agents",
                })

        self.evolution_log.append({
            "timestamp": datetime.utcnow().isoformat(),
            "improvements": len(improvements),
            "details": improvements,
        })

        return {
            "evolution_cycle": "completed",
            "improvements_identified": len(improvements),
            "improvements": improvements,
            "total_evolution_cycles": len(self.evolution_log),
        }

    def share_insights(self, from_agent: str, to_agents: List[str], lesson: str) -> Dict[str, Any]:
        self.knowledge_base.propagate_lesson(lesson, from_agent, to_agents)
        return {
            "shared": True,
            "from": from_agent,
            "to": to_agents,
            "lesson": lesson,
        }

    def get_status(self) -> Dict[str, Any]:
        return {
            "agents_registered": len(self.agents),
            "teaching_sessions": len(self.teaching_log),
            "evolution_cycles": len(self.evolution_log),
            "knowledge_base": self.knowledge_base.get_stats(),
            "experience_replay": self.experience_replay.get_stats(),
        }

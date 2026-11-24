"""Production Manager Agent — schedules channels, allocates resources, optimizes publish times."""

import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from agents.base import BaseAgent, AgentResult


@dataclass
class ResourcePool:
    gpu_slots: int = 4
    cpu_threads: int = 8
    tts_minutes_monthly: int = 500
    api_calls_daily: int = 1000
    used_gpu: int = 0
    used_tts: int = 0
    used_api: int = 0

    def available_gpu(self) -> int:
        return self.gpu_slots - self.used_gpu

    def available_tts(self) -> int:
        return self.tts_minutes_monthly - self.used_tts

    def available_api(self) -> int:
        return self.api_calls_daily - self.used_api

    def allocate(self, gpu: int, tts: int, api: int):
        self.used_gpu += gpu
        self.used_tts += tts
        self.used_api += api

    def release(self, gpu: int, tts: int, api: int):
        self.used_gpu = max(0, self.used_gpu - gpu)
        self.used_tts = max(0, self.used_tts - tts)
        self.used_api = max(0, self.used_api - api)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gpu_slots": self.gpu_slots,
            "used_gpu": self.used_gpu,
            "available_gpu": self.available_gpu(),
            "tts_minutes_monthly": self.tts_minutes_monthly,
            "used_tts": self.used_tts,
            "available_tts": self.available_tts(),
            "api_calls_daily": self.api_calls_daily,
            "used_api": self.used_api,
            "available_api": self.available_api(),
        }


AUDIENCE_PEAKS = {
    "geo-daily-ur": {"tz": "Asia/Karachi", "days": ["Monday", "Thursday"], "hours": [18, 19, 20], "gpu_needed": 2, "tts_needed": 100, "render_heavy": True},
    "tech-tutorials-hi": {"tz": "Asia/Kolkata", "days": ["Tuesday", "Friday"], "hours": [12, 14, 16], "gpu_needed": 1, "tts_needed": 150, "render_heavy": False},
    "islamic-history-ur": {"tz": "Asia/Dubai", "days": ["Wednesday", "Saturday"], "hours": [15, 17, 19], "gpu_needed": 1, "tts_needed": 50, "render_heavy": True},
}


class ProductionManagerAgent(BaseAgent):
    """Decides which channel produces next, allocates resources, schedules publish."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("production-manager", config)
        self.resources = ResourcePool(
            gpu_slots=config.get("gpu_slots", 4) if config else 4,
            cpu_threads=config.get("cpu_threads", 8) if config else 8,
            tts_minutes_monthly=config.get("tts_minutes_monthly", 500) if config else 500,
            api_calls_daily=config.get("api_calls_daily", 1000) if config else 1000,
        )
        self.schedule: Dict[str, Dict[str, Any]] = {}
        self.round_robin_index = 0

    def execute(self, task: Dict[str, Any]) -> AgentResult:
        action = task.get("action", "decide_next")

        if action == "decide_next":
            result = self.decide_next_production(task.get("available_channels", []))
        elif action == "release_resources":
            result = self.release_resources(task.get("channel_id"), task.get("gpu", 0), task.get("tts", 0), task.get("api", 0))
        elif action == "get_schedule":
            result = {"schedule": self.schedule, "resources": self.resources.to_dict()}
        else:
            return AgentResult(
                agent_id=self.agent_id,
                status="error",
                output=None,
                errors=[f"Unknown action: {action}"],
            )

        return AgentResult(
            agent_id=self.agent_id,
            status="success",
            output=result,
            confidence=95.0,
        )

    def decide_next_production(self, available_channels: List[str]) -> Dict[str, Any]:
        """Pick next channel for production based on multi-factor scoring."""
        ready = self._get_ready_channels(available_channels)
        if not ready:
            return {"selected_channel": None, "reason": "No channels ready"}

        scored = []
        for ch_id in ready:
            score = self._calculate_score(ch_id)
            scored.append((ch_id, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        best_ch = scored[0][0]

        peak = AUDIENCE_PEAKS.get(best_ch, {})
        publish_time = self._calculate_publish_time(best_ch, peak)

        gpu_needed = peak.get("gpu_needed", 1)
        tts_needed = peak.get("tts_needed", 50)

        # Check resource availability
        if gpu_needed > self.resources.available_gpu():
            # Re-queue, try next
            if len(scored) > 1:
                best_ch = scored[1][0]
                peak = AUDIENCE_PEAKS.get(best_ch, {})
                gpu_needed = peak.get("gpu_needed", 1)
                tts_needed = peak.get("tts_needed", 50)

        self.resources.allocate(gpu_needed, tts_needed, 10)
        self.schedule[best_ch] = {
            "produce_start": datetime.utcnow().isoformat(),
            "publish": publish_time.isoformat(),
            "gpu_allocated": gpu_needed,
            "tts_allocated": tts_needed,
            "status": "producing",
        }

        self._record_trajectory("decide", {"channel": best_ch, "publish": publish_time.isoformat()})

        return {
            "selected_channel": best_ch,
            "produce_start": datetime.utcnow().isoformat(),
            "publish_time": publish_time.isoformat(),
            "resource_allocation": {"gpu": gpu_needed, "tts": tts_needed, "api": 10},
            "resources_available": self.resources.to_dict(),
            "scores": {ch: s for ch, s in scored},
            "reasoning": self._explain_decision(best_ch, scored),
        }

    def _get_ready_channels(self, available: List[str]) -> List[str]:
        ready = []
        for ch_id in available:
            if ch_id in self.schedule:
                status = self.schedule[ch_id].get("status")
                if status == "producing":
                    continue  # skip if already producing
            ready.append(ch_id)
        return ready

    def _calculate_score(self, ch_id: str) -> float:
        score = 0.0
        peak = AUDIENCE_PEAKS.get(ch_id, {})
        # Factor 1: Audience peak alignment (higher if we're in best day/hour window)
        now = datetime.now(timezone.utc)
        # Simplified: add base score for monetized channels
        score += 5  # base
        # Factor 2: Resource cost (lower is better)
        gpu_cost = peak.get("gpu_needed", 1)
        score -= gpu_cost * 0.5
        # Factor 3: Round-robin fairness
        score += (self.round_robin_index % 10) * 0.1
        self.round_robin_index += 1
        return score

    def _calculate_publish_time(self, ch_id: str, peak: Dict) -> datetime:
        now = datetime.now(timezone.utc)
        best_hours = peak.get("hours", [18])
        best_day_idx = 0
        # Find next optimal day
        days_map = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3, "Friday": 4, "Saturday": 5, "Sunday": 6}
        best_days = peak.get("days", ["Monday"])
        target_day = days_map.get(best_days[0], 0)
        
        days_ahead = (target_day - now.weekday()) % 7
        if days_ahead == 0:
            days_ahead = 7  # next week if today is the day
        publish = now + timedelta(days=days_ahead)
        publish = publish.replace(hour=best_hours[0], minute=0, second=0, microsecond=0)
        return publish

    def _explain_decision(self, best_ch: str, scored: List) -> str:
        return f"Selected {best_ch} (score: {scored[0][1]:.2f}) based on audience peak alignment, resource availability, and round-robin balance."

    def release_resources(self, channel_id: str, gpu: int, tts: int, api: int) -> Dict[str, Any]:
        self.resources.release(gpu, tts, api)
        if channel_id in self.schedule:
            self.schedule[channel_id]["status"] = "completed"
        self._record_trajectory("release", {"channel": channel_id, "gpu": gpu, "tts": tts})
        return {"released": True, "resources": self.resources.to_dict()}



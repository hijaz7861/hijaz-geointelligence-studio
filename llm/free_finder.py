"""Free LLM Finder — discovers and utilizes free LLM models across providers."""

import os
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Free provider endpoints
FREE_PROVIDERS = {
    "openrouter": {
        "name": "OpenRouter",
        "base_url": "https://openrouter.ai/api/v1",
        "api_key_env": "OPENROUTER_API_KEY",
        "free_models_endpoint": "/models",
        "chat_endpoint": "/chat/completions",
    },
    "ollama": {
        "name": "Ollama (Local)",
        "base_url": "http://localhost:11434",
        "api_key_env": None,
        "free_models_endpoint": "/api/tags",
        "chat_endpoint": "/api/generate",
    },
    "groq": {
        "name": "Groq",
        "base_url": "https://api.groq.com/openai/v1",
        "api_key_env": "GROQ_API_KEY",
        "free_models_endpoint": "/models",
        "chat_endpoint": "/chat/completions",
    },
    "together": {
        "name": "Together AI",
        "base_url": "https://api.together.xyz/v1",
        "api_key_env": "TOGETHER_API_KEY",
        "free_models_endpoint": "/models",
        "chat_endpoint": "/chat/completions",
    },
}


class FreeLLMFinder:
    """Discovers free LLM models across multiple providers."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.discovered_models: Dict[str, List[str]] = {}
        self.last_refresh: Optional[datetime] = None
        self.refresh_interval = timedelta(hours=self.config.get("refresh_interval_hours", 24))

    def discover_all(self) -> Dict[str, List[str]]:
        """Discover free models from all configured providers."""
        results = {}
        for provider_id, provider_info in FREE_PROVIDERS.items():
            api_key = None
            if provider_info["api_key_env"]:
                api_key = os.environ.get(provider_info["api_key_env"])
            if provider_info["api_key_env"] and not api_key:
                logger.info(f"Skipping {provider_id}: no API key")
                continue
            models = self._discover_provider(provider_id, provider_info, api_key)
            if models:
                results[provider_id] = models
                logger.info(f"Found {len(models)} free models on {provider_id}")
        self.discovered_models = results
        self.last_refresh = datetime.utcnow()
        return results

    def _discover_provider(self, provider_id: str, info: Dict, api_key: Optional[str]) -> List[str]:
        """Discover free models from a single provider."""
        try:
            import urllib.request
            url = f"{info['base_url']}{info['free_models_endpoint']}"
            headers = {}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"

            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())

            if provider_id == "openrouter":
                return self._filter_openrouter_free(data)
            elif provider_id == "ollama":
                return [m["name"] for m in data.get("models", [])]
            elif provider_id in ("groq", "together"):
                return [m["id"] for m in data.get("data", []) if "free" in m.get("id", "").lower()]
            return []
        except Exception as e:
            logger.warning(f"Failed to discover models on {provider_id}: {e}")
            return []

    def _filter_openrouter_free(self, data: Dict) -> List[str]:
        """Filter OpenRouter models that are free."""
        free_models = []
        for m in data.get("data", []):
            pricing = m.get("pricing", {})
            prompt_price = float(pricing.get("prompt", "1"))
            completion_price = float(pricing.get("completion", "1"))
            if prompt_price == 0 and completion_price == 0:
                free_models.append(m["id"])
        return free_models

    def get_best_free_model(self, task_type: str = "general") -> Optional[str]:
        """Get the best available free model for a task type."""
        if not self.discovered_models:
            self.discover_all()

        all_models = []
        for provider, models in self.discovered_models.items():
            for m in models:
                all_models.append((provider, m))

        if not all_models:
            # Fallback to known free models
            return "meta-llama/llama-3.1-8b-instruct:free"

        # Prefer larger models for complex tasks
        if task_type in ("script", "analysis", "translation"):
            for provider, model in all_models:
                if "70b" in model or "72b" in model or "large" in model:
                    return f"{provider}:{model}"

        return f"{all_models[0][0]}:{all_models[0][1]}"

    def should_refresh(self) -> bool:
        if self.last_refresh is None:
            return True
        return datetime.utcnow() - self.last_refresh > self.refresh_interval

    def get_discovery_report(self) -> Dict[str, Any]:
        return {
            "last_refresh": self.last_refresh.isoformat() if self.last_refresh else None,
            "providers_discovered": list(self.discovered_models.keys()),
            "total_models": sum(len(m) for m in self.discovered_models.values()),
            "models_by_provider": {k: len(v) for k, v in self.discovered_models.items()},
        }

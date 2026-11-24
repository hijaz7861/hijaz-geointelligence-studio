"""LLM Provider Abstraction — Free OpenRouter + fallback models for all agents."""

import os
import json
import time
import logging
from typing import Any, Dict, List, Optional
from .free_finder import FreeLLMFinder
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    model: str
    content: str
    tokens_used: int = 0
    latency_ms: float = 0.0
    success: bool = True
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


# Free models available on OpenRouter (as of 2026)
FREE_OPENROUTER_MODELS = [
    "meta-llama/llama-3.1-8b-instruct:free",
    "meta-llama/llama-3.2-3b-instruct:free",
    "mistralai/mistral-7b-instruct:free",
    "google/gemma-2-9b-it:free",
    "qwen/qwen-2-1.5b-instruct:free",
    "huggingfaceh4/zephyr-7b-beta:free",
    "openchat/openchat-7b:free",
    "nousresearch/nous-capybara-7b:free",
]

# Free models available via other providers
FREE_MODELS_OTHER = {
    "ollama": ["llama3.1", "mistral", "gemma2", "qwen2.5", "phi3"],
    "groq": ["llama-3.1-8b-instant", "mixtral-8x7b-32768", "gemma2-9b-it"],
    "together": ["meta-llama/Llama-3.1-8B-Instruct-Turbo", "mistralai/Mistral-7B-Instruct-v0.3"],
    "huggingface": ["meta-llama/Llama-3.1-8B-Instruct", "mistralai/Mistral-7B-Instruct-v0.3"],
}


class LLMProvider:
    """Unified LLM provider with free model support and fallback."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.openrouter_api_key = os.environ.get("OPENROUTER_API_KEY", "")
        self.openrouter_base_url = "https://openrouter.ai/api/v1"
        self.preferred_provider = self.config.get("preferred_provider", "openrouter")
        self.model_priority = self.config.get("model_priority", FREE_OPENROUTER_MODELS)
        self.fallback_enabled = self.config.get("fallback_enabled", True)
        self.max_retries = self.config.get("max_retries", 3)
        self.timeout = self.config.get("timeout", 30)
        self._usage_stats: Dict[str, int] = {}
        self._model_health: Dict[str, bool] = {}
        self.free_finder = FreeLLMFinder(config)

    def generate(self, prompt: str, system_prompt: str = "", model: Optional[str] = None,
                 temperature: float = 0.7, max_tokens: int = 2048) -> LLMResponse:
        """Generate text using free LLM with automatic fallback."""
        models_to_try = [model] if model else self.model_priority

        for attempt_model in models_to_try:
            try:
                response = self._call_model(attempt_model, prompt, system_prompt, temperature, max_tokens)
                if response.success:
                    self._record_usage(attempt_model, response.tokens_used)
                    return response
                else:
                    logger.warning(f"Model {attempt_model} failed: {response.error}")
                    self._model_health[attempt_model] = False
            except Exception as e:
                logger.error(f"Exception calling {attempt_model}: {e}")
                self._model_health[attempt_model] = False

        return LLMResponse(
            model="none",
            content="",
            success=False,
            error="All models failed",
        )

    def _call_model(self, model: str, prompt: str, system_prompt: str,
                    temperature: float, max_tokens: int) -> LLMResponse:
        """Call a specific model."""
        start_time = time.time()

        # OpenRouter
        if ":" in model or model in FREE_OPENROUTER_MODELS or "openrouter" in model:
            return self._call_openrouter(model, prompt, system_prompt, temperature, max_tokens, start_time)

        # Ollama (local)
        if model in FREE_MODELS_OTHER.get("ollama", []):
            return self._call_ollama(model, prompt, system_prompt, temperature, max_tokens, start_time)

        # Default: try OpenRouter
        return self._call_openrouter(model, prompt, system_prompt, temperature, max_tokens, start_time)

    def _call_openrouter(self, model: str, prompt: str, system_prompt: str,
                         temperature: float, max_tokens: int, start_time: float) -> LLMResponse:
        """Call OpenRouter API."""
        if not self.openrouter_api_key:
            return LLMResponse(model=model, content="", success=False, error="No OpenRouter API key")

        try:
            import urllib.request
            import urllib.error

            url = f"{self.openrouter_base_url}/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.openrouter_api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://hijaz-geointel.local",
                "X-Title": "Hijaz GeoIntelligence Studio",
            }

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            data = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }

            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode(),
                headers=headers,
                method="POST",
            )

            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                result = json.loads(resp.read().decode())
                content = result["choices"][0]["message"]["content"]
                tokens = result.get("usage", {}).get("total_tokens", 0)
                latency = (time.time() - start_time) * 1000

                return LLMResponse(
                    model=model,
                    content=content,
                    tokens_used=tokens,
                    latency_ms=latency,
                    success=True,
                )

        except Exception as e:
            return LLMResponse(model=model, content="", success=False, error=str(e))

    def _call_ollama(self, model: str, prompt: str, system_prompt: str,
                     temperature: float, max_tokens: int, start_time: float) -> LLMResponse:
        """Call local Ollama instance."""
        try:
            import urllib.request
            url = "http://localhost:11434/api/generate"
            data = {
                "model": model,
                "prompt": prompt,
                "system": system_prompt,
                "stream": False,
                "options": {"temperature": temperature, "num_predict": max_tokens},
            }
            req = urllib.request.Request(url, data=json.dumps(data).encode(), headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                result = json.loads(resp.read().decode())
                content = result.get("response", "")
                latency = (time.time() - start_time) * 1000
                return LLMResponse(model=model, content=content, latency_ms=latency, success=True)
        except Exception as e:
            return LLMResponse(model=model, content="", success=False, error=str(e))

    def _record_usage(self, model: str, tokens: int):
        self._usage_stats[model] = self._usage_stats.get(model, 0) + tokens

    def find_free_models(self) -> List[str]:
        """Discover free models available on OpenRouter."""
        if not self.openrouter_api_key:
            return FREE_OPENROUTER_MODELS
        try:
            import urllib.request
            url = f"{self.openrouter_base_url}/models"
            req = urllib.request.Request(url, headers={"Authorization": f"Bearer {self.openrouter_api_key}"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read().decode())
                free_models = []
                for m in result.get("data", []):
                    pricing = m.get("pricing", {})
                    if pricing.get("prompt") == "0" or pricing.get("completion") == "0":
                        free_models.append(m["id"])
                return free_models if free_models else FREE_OPENROUTER_MODELS
        except Exception:
            return FREE_OPENROUTER_MODELS

    def get_usage_stats(self) -> Dict[str, Any]:
        return {
            "usage_by_model": self._usage_stats,
            "model_health": self._model_health,
            "total_tokens": sum(self._usage_stats.values()),
        }

    def get_best_model(self, task_type: str = "general") -> str:
        """Select best model based on task type and health."""
        healthy = [m for m in self.model_priority if self._model_health.get(m, True)]
        if not healthy:
            healthy = self.model_priority
        # Prefer larger models for complex tasks
        if task_type in ("script", "analysis", "translation"):
            for m in healthy:
                if "70b" in m or "72b" in m or "large" in m:
                    return m
        return healthy[0] if healthy else self.model_priority[0]

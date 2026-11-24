"""LLM-Enhanced Base Agent — adds LLM capabilities to all agents."""

from typing import Any, Dict, List, Optional
from agents.base import BaseAgent, AgentResult
from llm.provider import LLMProvider


class LLMEnhancedAgent(BaseAgent):
    """Base agent with LLM generation capabilities."""

    def __init__(self, agent_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(agent_id, config)
        self.llm = LLMProvider(config.get("llm", {}) if config else {})
        self.system_prompt = config.get("system_prompt", "") if config else ""
        self.use_llm = config.get("use_llm", True) if config else True

    def generate_with_llm(self, prompt: str, task_type: str = "general",
                          temperature: float = 0.7, max_tokens: int = 2048) -> str:
        """Generate text using LLM with automatic fallback."""
        if not self.use_llm:
            return ""

        model = self.llm.get_best_model(task_type)
        response = self.llm.generate(
            prompt=prompt,
            system_prompt=self.system_prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        if response.success:
            return response.content
        else:
            self.logger.warning(f"LLM generation failed: {response.error}")
            return ""

    def extract_with_llm(self, text: str, extraction_prompt: str) -> str:
        """Extract structured info from text using LLM."""
        prompt = f"{extraction_prompt}\n\nText:\n{text}"
        return self.generate_with_llm(prompt, task_type="analysis", temperature=0.3)

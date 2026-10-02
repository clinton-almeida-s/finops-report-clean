import json
import logging
from typing import Any, Dict

from .claude_client import ClaudeClient
from .gemini_client import GeminiClient
from .config import Config
from .prompt_templates import ANALYSIS_PROMPT

logger = logging.getLogger(__name__)

class AgentOrchestrator:
    def __init__(self, config: Config):
        self._claude = None
        self._gemini = None
        if config.claude_api_key:
            self._claude = ClaudeClient(api_key=config.claude_api_key)
        if config.gemini_api_key:
            self._gemini = GeminiClient(api_key=config.gemini_api_key)
        # Skip validation for tests where mock clients are used

    def analyze(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run analysis through available providers with fallback."""
        # Gemini first — we're fetching GCP data, so Google's AI is the natural fit
        providers = [(name, client) for name, client in [("gemini", self._gemini), ("claude", self._claude)] if client]
        if not providers:
            raise ValueError("No AI provider configured. Set ANTHROPIC_API_KEY or GEMINI_API_KEY.")
        data_json = json.dumps(raw_data, indent=2, default=str)
        prompt = ANALYSIS_PROMPT.format(data_json=data_json)
        last_err = None
        for name, client in providers:
            try:
                logger.info("Calling %s for analysis", name)
                text = client.call(prompt, max_tokens=8192)
                result = json.loads(text)
                logger.info("%s analysis completed successfully", name)
                return result
            except Exception as e:
                logger.warning("%s failed: %s", name, e)
                last_err = e
        raise RuntimeError(f"Both providers failed. Last error: {last_err}")

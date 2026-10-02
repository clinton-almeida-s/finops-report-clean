import json
import os
import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None


def _extract_json(text: str) -> str:
    """Extract and fix JSON from potentially truncated LLM output."""
    import re
    text = text.strip()
    # Strip markdown code fences if present
    text = re.sub(r'^```(?:json)?\s*', '', text)
    text = re.sub(r'\s*```\s*$', '', text)
    text = text.strip()
    # If it starts with { and ends with }, try parsing
    if text.startswith('{') and text.endswith('}'):
        try:
            json.loads(text)
            return text
        except json.JSONDecodeError:
            pass
    # Find last complete closing brace
    last_brace = text.rfind('}')
    if last_brace > 0:
        candidate = text[:last_brace + 1]
        try:
            json.loads(candidate)
            return candidate
        except json.JSONDecodeError:
            pass
    raise ValueError(f"Could not extract valid JSON from response: {text[:200]}...")


class ClaudeClient:
    def __init__(self, api_key: Optional[str] = None, timeout: int = 30):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")
        self._timeout = timeout

    def call(self, prompt: str, max_tokens: int = 8192) -> str:
        if Anthropic is None:
            raise RuntimeError(
                "anthropic package not installed. Run: pip install anthropic"
            )
        client = Anthropic(api_key=self.api_key)
        for attempt in range(3):
            try:
                msg = client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=max_tokens,
                    messages=[{"role": "user", "content": prompt}],
                    timeout=self._timeout,
                )
                texts = [b.text for b in msg.content if hasattr(b, 'text') and b.text]
                if not texts:
                    raise ValueError("No text content in response")
                return _extract_json('\n'.join(texts))
            except Exception as e:
                if attempt < 2:
                    continue
                raise e

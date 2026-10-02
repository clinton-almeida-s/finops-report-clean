import json
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

try:
    import google.genai as genai
except ImportError:
    genai = None


def _extract_json(text: str) -> str:
    """Extract and fix JSON from potentially truncated LLM output."""
    import re
    text = text.strip()
    # Strip markdown code fences if present
    text = re.sub(r'^```(?:json)?\s*', '', text)
    text = re.sub(r'\s*```\s*$', '', text)
    text = text.strip()
    if text.startswith('{') and text.endswith('}'):
        try:
            json.loads(text)
            return text
        except json.JSONDecodeError:
            pass
    last_brace = text.rfind('}')
    if last_brace > 0:
        candidate = text[:last_brace + 1]
        try:
            json.loads(candidate)
            return candidate
        except json.JSONDecodeError:
            pass
    raise ValueError(f"Could not extract valid JSON from response: {text[:200]}...")


class GeminiClient:
    def __init__(self, api_key: Optional[str] = None, timeout: int = 30):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not set")
        self._timeout = timeout

    def call(self, prompt: str, max_tokens: int = 8192) -> str:
        if genai is None:
            raise RuntimeError(
                "google-genai package not installed. Run: pip install google-genai"
            )
        client = genai.Client(api_key=self.api_key)
        for attempt in range(3):
            try:
                resp = client.models.generate_content(
                    model="gemini-3.8-flash",
                    contents=prompt,
                    config=genai.types.GenerateContentConfig(
                        max_output_tokens=max_tokens,
                    ),
                )
                text = None
                if hasattr(resp, 'text') and resp.text:
                    text = resp.text
                elif hasattr(resp, 'candidates') and resp.candidates:
                    for candidate in resp.candidates:
                        if candidate and hasattr(candidate, 'content') and candidate.content:
                            if hasattr(candidate.content, 'parts') and candidate.content.parts:
                                for part in candidate.content.parts:
                                    if part and hasattr(part, 'text') and part.text:
                                        text = part.text
                                        break
                        if text:
                            break
                if text:
                    return _extract_json(text)
                raise ValueError("No text content in Gemini response")
            except Exception as e:
                if attempt < 2:
                    continue
                raise e

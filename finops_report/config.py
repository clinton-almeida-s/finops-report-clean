from dataclasses import dataclass
import os

@dataclass(frozen=True)
class Config:
    claude_api_key: str = os.environ.get("ANTHROPIC_API_KEY", "")
    gemini_api_key: str = os.environ.get("GEMINI_API_KEY", "")
    claude_model: str = "claude-sonnet-4-20250514"
    gemini_model: str = "gemini-3.8-flash"
    timeout: int = 30

def load_config() -> Config:
    # Support both ANTHROPIC_API_KEY and ANTHROPIC_AUTH_TOKEN (for proxy setups)
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN", "")
    if not anthropic_key and not os.environ.get("GEMINI_API_KEY"):
        raise ValueError(
            "No AI provider configured. Set ANTHROPIC_API_KEY or GEMINI_API_KEY."
        )
    return Config(
        claude_api_key=anthropic_key,
        gemini_api_key=os.environ.get("GEMINI_API_KEY", ""),
    )
import os
_client = None

def available() -> bool:
    return bool(os.getenv("ANTHROPIC_API_KEY"))

async def complete(system: str, prompt: str, max_tokens: int = 500):
    """Returns None when no key / any error, so every agent has a deterministic fallback (demo never breaks)."""
    global _client
    if not available():
        return None
    try:
        from anthropic import AsyncAnthropic
        _client = _client or AsyncAnthropic()
        r = await _client.messages.create(model=os.getenv("LLM_MODEL", "claude-sonnet-5-5"), max_tokens=max_tokens,
                                          system=system, messages=[{"role": "user", "content": prompt}])
        return r.content[0].text
    except Exception:
        return None

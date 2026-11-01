"""
Hybrid AI Router: Local (LM Studio / Ollama) vs Cloud (OpenRouter Free / Smart).
"""

import time
import httpx
from typing import Dict, Any, Optional

from agent_dispatcher.config import (
    logger,
    BASE_URL,
    DEFAULT_MODEL,
    TIMEOUT_SECONDS,
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    OPENROUTER_FREE_DEFAULT,
    OPENROUTER_SMART_DEFAULT,
    FREE_FALLBACK_CHAIN,
    MAX_RETRIES,
    RETRY_BACKOFF_BASE
)
from agent_dispatcher.audit import (
    record_token_usage,
    check_daily_budget,
    generate_cache_key,
    get_from_cache,
    save_to_cache
)


def get_active_model_id() -> str:
    """Discovers available model on local server or falls back to default."""
    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.get(f"{BASE_URL}/models")
            if resp.status_code == 200:
                data = resp.json()
                models = [m.get("id") for m in data.get("data", []) if m.get("id")]
                if DEFAULT_MODEL in models:
                    return DEFAULT_MODEL
                for m in models:
                    if "qwen" in m.lower() and "coder" in m.lower():
                        return m
                if models:
                    return models[0]
    except Exception as e:
        logger.warning(f"Could not fetch models from {BASE_URL}/models: {e}. Fallback: {DEFAULT_MODEL}")

    return DEFAULT_MODEL


def call_local_ai(
    prompt: str,
    system_prompt: str,
    temperature: float = 0.2,
    max_tokens: int = 3000,
    tool_name: str = "task"
) -> str:
    """Sends request to local OpenAI-compatible inference server and records tokens."""
    model = get_active_model_id()
    endpoint = f"{BASE_URL}/chat/completions"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]

    payload: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }

    logger.info(f"Calling local AI at {endpoint} with '{model}' (Tool: {tool_name})...")
    start_time = time.time()

    try:
        with httpx.Client(timeout=TIMEOUT_SECONDS) as client:
            response = client.post(endpoint, json=payload)
            elapsed_ms = (time.time() - start_time) * 1000

            if response.status_code != 200:
                error_msg = f"HTTP {response.status_code} from local server: {response.text}"
                logger.error(error_msg)
                return f"[LOCAL AI ERROR] {error_msg}"

            data = response.json()
            choices = data.get("choices", [])
            if not choices:
                return "[LOCAL AI ERROR] No choices returned by local model."

            usage = data.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            record_token_usage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                duration_ms=elapsed_ms,
                tool_name=tool_name,
                provider="local",
                model_used=model
            )

            return choices[0].get("message", {}).get("content", "")
    except Exception as e:
        logger.error(f"Failed to connect to local server: {e}")
        return f"[LOCAL AI ERROR] {e}"


def call_openrouter_ai(
    prompt: str,
    system_prompt: str,
    model: str = "",
    temperature: float = 0.2,
    max_tokens: int = 4000,
    tool_name: str = "task",
    is_smart_tier: bool = False
) -> str:
    """Sends request to OpenRouter API with retry backoff and token auditing."""
    if not OPENROUTER_API_KEY:
        return "[OPENROUTER ERROR] OPENROUTER_API_KEY not configured."

    target_model = model or (OPENROUTER_SMART_DEFAULT if is_smart_tier else OPENROUTER_FREE_DEFAULT)
    models_to_try = [target_model]
    if not is_smart_tier:
        for fb in FREE_FALLBACK_CHAIN:
            if fb not in models_to_try:
                models_to_try.append(fb)

    endpoint = f"{OPENROUTER_BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://github.com/delmo85/agent-token-auditor",
        "X-Title": "Antigravity Token Auditor & Dispatcher",
        "Content-Type": "application/json"
    }

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]

    for model_candidate in models_to_try:
        payload = {
            "model": model_candidate,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        for attempt in range(MAX_RETRIES):
            start_time = time.time()
            try:
                with httpx.Client(timeout=TIMEOUT_SECONDS) as client:
                    resp = client.post(endpoint, headers=headers, json=payload)
                    elapsed_ms = (time.time() - start_time) * 1000

                    if resp.status_code == 200:
                        data = resp.json()
                        choices = data.get("choices", [])
                        if not choices:
                            break
                        usage = data.get("usage", {})
                        record_token_usage(
                            prompt_tokens=usage.get("prompt_tokens", 0),
                            completion_tokens=usage.get("completion_tokens", 0),
                            duration_ms=elapsed_ms,
                            tool_name=tool_name,
                            provider="openrouter_smart" if is_smart_tier else "openrouter_free",
                            model_used=model_candidate
                        )
                        return choices[0].get("message", {}).get("content", "")

                    if resp.status_code == 429:
                        wait = RETRY_BACKOFF_BASE * (2 ** attempt)
                        logger.warning(f"429 rate limit on {model_candidate}. Retrying in {wait}s...")
                        time.sleep(wait)
                        continue

                    logger.error(f"OpenRouter HTTP {resp.status_code}: {resp.text}")
                    break
            except Exception as e:
                logger.error(f"Request error on {model_candidate}: {e}")
                break

    return "[OPENROUTER ERROR] All model candidates failed or rate limited."


def call_routed_ai(
    prompt: str,
    system_prompt: str,
    complexity: str = "local",
    model_override: Optional[str] = None,
    temperature: float = 0.2,
    max_tokens: int = 3500,
    tool_name: str = "task"
) -> str:
    """Routes prompt based on complexity tier, checks cache and budget."""
    target_model = model_override or ("qwen-local" if complexity == "local" else OPENROUTER_FREE_DEFAULT)
    cache_key = generate_cache_key(target_model, tool_name, prompt, system_prompt)
    cached = get_from_cache(cache_key)
    if cached is not None:
        return cached

    complexity_norm = complexity.lower().strip()

    if complexity_norm == "local":
        resp = call_local_ai(prompt, system_prompt, temperature, max_tokens, tool_name)
        if not resp.startswith("[LOCAL AI ERROR]"):
            save_to_cache(cache_key, resp, target_model, tool_name)
            return resp
        logger.warning("Local AI failed. Falling back to OpenRouter free tier...")
        complexity_norm = "openrouter_free"

    if complexity_norm in ("openrouter_smart", "smart"):
        allowed, msg = check_daily_budget()
        if not allowed:
            return msg
        resp = call_openrouter_ai(
            prompt, system_prompt, model=model_override or OPENROUTER_SMART_DEFAULT,
            temperature=temperature, max_tokens=max_tokens, tool_name=tool_name, is_smart_tier=True
        )
        if not resp.startswith("[OPENROUTER ERROR]"):
            save_to_cache(cache_key, resp, target_model, tool_name)
        return resp

    # Default OpenRouter free
    resp = call_openrouter_ai(
        prompt, system_prompt, model=model_override or OPENROUTER_FREE_DEFAULT,
        temperature=temperature, max_tokens=max_tokens, tool_name=tool_name, is_smart_tier=False
    )
    if not resp.startswith("[OPENROUTER ERROR]"):
        save_to_cache(cache_key, resp, target_model, tool_name)
    return resp


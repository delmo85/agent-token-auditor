"""
Local AI & Hybrid Dispatcher MCP Package
Hybrid agent routing between local LLMs (LM Studio/Ollama) and Cloud (OpenRouter),
with token auditing, caching, and budget guardrails.
"""

from agent_dispatcher.config import (
    mcp,
    logger,
    MODEL_CATALOG,
    BASE_URL,
    OPENROUTER_BASE_URL,
    OPENROUTER_FREE_DEFAULT,
    OPENROUTER_SMART_DEFAULT
)
from agent_dispatcher.audit import (
    get_model_rates,
    record_token_usage
)
from agent_dispatcher.router import (
    call_routed_ai,
    call_local_ai,
    call_openrouter_ai,
    get_active_model_id
)
import agent_dispatcher.tools as tools

__all__ = [
    "mcp",
    "logger",
    "MODEL_CATALOG",
    "BASE_URL",
    "OPENROUTER_BASE_URL",
    "OPENROUTER_FREE_DEFAULT",
    "OPENROUTER_SMART_DEFAULT",
    "get_model_rates",
    "record_token_usage",
    "call_routed_ai",
    "call_local_ai",
    "call_openrouter_ai",
    "get_active_model_id",
    "tools"
]


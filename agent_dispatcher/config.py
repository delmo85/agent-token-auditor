"""
Configuration, constants and model catalog for FastMCP Dispatcher.
"""

import os
import sys
import logging
from typing import Dict, Any

# Logging strictly to stderr to keep stdout pure for JSON-RPC MCP stdio transport
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [FastMCP] %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stderr
)
logger = logging.getLogger("AgentDispatcher")

# Import FastMCP
try:
    from mcp.server.mcpserver import MCPServer as FastMCP
except ImportError:
    try:
        from mcp.server.fastmcp import FastMCP
    except (ImportError, ModuleNotFoundError):
        try:
            from fastmcp import FastMCP
        except ImportError:
            logger.error("FastMCP library not found. Run: pip install mcp")
            sys.exit(1)

mcp = FastMCP("local-ai-dispatcher")

# Local AI Server (LM Studio / Ollama / vLLM / LocalAI)
BASE_URL = os.environ.get("LOCAL_AI_BASE_URL", "http://localhost:1234/v1").rstrip("/")
DEFAULT_MODEL = os.environ.get("LOCAL_AI_MODEL", "qwen/qwen2.5-coder-7b-instruct")
TIMEOUT_SECONDS = float(os.environ.get("LOCAL_AI_TIMEOUT", "120.0"))

# OpenRouter (Hybrid Routing)
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").rstrip("/")
OPENROUTER_FREE_DEFAULT = os.environ.get("OPENROUTER_FREE_MODEL", "qwen/qwen3.8-27b:free")
OPENROUTER_SMART_DEFAULT = os.environ.get("OPENROUTER_SMART_MODEL", "deepseek/deepseek-r1")

# Fallback chain for free-tier models (tried in sequence on 429 rate limit)
FREE_FALLBACK_CHAIN = [
    "qwen/qwen3.8-27b:free",
    "google/gemma-4-26b-a4b-it:free",
    "cohere/north-mini-code:free",
    "nvidia/nemotron-3.5-lightning:free"
]

MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 1.0

# Paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
METRICS_FILE = os.path.join(PROJECT_ROOT, ".agents", "local_ai_metrics.json")
LOCAL_AUDIT_CSV = os.path.join(PROJECT_ROOT, "local_ai_audit.csv")
LOCAL_AUDIT_JSON = os.path.join(PROJECT_ROOT, "local_ai_audit.json")
BUDGET_FILE = os.path.join(PROJECT_ROOT, ".agents", "ai_budget.json")
CACHE_DIR = os.path.join(PROJECT_ROOT, ".agents", "cache")

# Pricing benchmarks per 1M tokens (USD)
PRICING_TABLE = {
    "claude_3_5_sonnet": {"in": 3.00, "out": 15.00},
    "gpt_4o": {"in": 2.50, "out": 10.00},
    "gemini_2_0_flash": {"in": 0.10, "out": 0.40}
}
BRL_RATE = float(os.environ.get("CURRENCY_RATE_USD", "5.75"))

# Model catalog
MODEL_CATALOG: Dict[str, Dict[str, Any]] = {
    "qwen/qwen2.5-coder-7b-instruct": {
        "tier": "local",
        "name": "Qwen 2.5 Coder 7B (Local LM Studio)",
        "price_in": 0.00,
        "price_out": 0.00,
        "context": "32k",
        "description": "Local free model. Ideal for DTOs, syntax validation, boilerplate and CRUDs."
    },
    "qwen/qwen3.8-27b:free": {
        "tier": "openrouter_free",
        "name": "Qwen 3.8 27B (Free)",
        "price_in": 0.00,
        "price_out": 0.00,
        "context": "32k",
        "description": "Zero cost OpenRouter free tier for medium logic refactoring."
    },
    "google/gemma-4-26b-a4b-it:free": {
        "tier": "openrouter_free",
        "name": "Google Gemma 4 26B (Free)",
        "price_in": 0.00,
        "price_out": 0.00,
        "context": "16k",
        "description": "Zero cost fallback for code explanations and unit test generation."
    },
    "deepseek/deepseek-r1": {
        "tier": "openrouter_smart",
        "name": "DeepSeek R1 (Smart / Reasoning)",
        "price_in": 0.55,
        "price_out": 2.19,
        "context": "64k",
        "description": "High-tier analytical reasoning model for architecture, security audits and concurrency."
    },
    "anthropic/claude-sonnet-5": {
        "tier": "openrouter_smart",
        "name": "Claude 3.5/3.7 Sonnet (Smart)",
        "price_in": 3.00,
        "price_out": 15.00,
        "context": "200k",
        "description": "Elite coding and reasoning model for mission-critical tasks."
    }
}


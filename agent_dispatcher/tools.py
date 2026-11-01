"""
FastMCP Tool definitions for local coding, DTOs, tests, syntax validation and token metrics.
"""

import os
import json
import httpx
from typing import Optional

from agent_dispatcher.config import (
    mcp,
    BASE_URL,
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    OPENROUTER_FREE_DEFAULT,
    OPENROUTER_SMART_DEFAULT,
    MODEL_CATALOG,
    METRICS_FILE,
    BRL_RATE
)
from agent_dispatcher.router import (
    get_active_model_id,
    call_routed_ai
)


@mcp.tool()
def get_token_usage_report() -> str:
    """
    Returns full token usage report for local AI (LM Studio/Ollama) and OpenRouter,
    including input/output tokens, tier breakdown, actual costs, and accumulated savings.
    """
    if not os.path.exists(METRICS_FILE):
        return json.dumps({
            "status": "empty",
            "message": "No calls recorded yet by the dispatcher."
        }, indent=2)

    try:
        with open(METRICS_FILE, "r", encoding="utf-8") as f:
            metrics = json.load(f)

        p_tokens = metrics.get("total_prompt_tokens", 0)
        c_tokens = metrics.get("total_completion_tokens", 0)
        tot_tokens = metrics.get("total_tokens", 0)
        reqs = metrics.get("total_requests", 0)
        local_reqs = metrics.get("local_requests", 0)
        or_free_reqs = metrics.get("openrouter_free_requests", 0)
        or_paid_reqs = metrics.get("openrouter_paid_requests", 0)
        cost_real = metrics.get("total_cost_real_usd", 0.0)
        saved_claude = metrics.get("total_saved_vs_claude_usd", 0.0)

        report = {
            "summary": {
                "total_requests": reqs,
                "local_ai_requests": local_reqs,
                "openrouter_free_requests": or_free_reqs,
                "openrouter_paid_requests": or_paid_reqs,
                "input_tokens": p_tokens,
                "output_tokens": c_tokens,
                "total_tokens": tot_tokens,
                "real_cost_total_usd": f"${cost_real:.4f}",
                "real_cost_total_local": f"{cost_real * BRL_RATE:.2f}",
                "total_savings_vs_claude_usd": f"${saved_claude:.4f}",
                "total_savings_vs_claude_local": f"{saved_claude * BRL_RATE:.2f}"
            },
            "connected_servers": {
                "local_ai": {
                    "model": get_active_model_id(),
                    "endpoint": BASE_URL,
                    "cost": "Free / Offline"
                },
                "openrouter": {
                    "endpoint": OPENROUTER_BASE_URL,
                    "default_free_model": OPENROUTER_FREE_DEFAULT,
                    "default_smart_model": OPENROUTER_SMART_DEFAULT
                }
            },
            "recent_calls": metrics.get("history", [])[-5:]
        }
        return json.dumps(report, indent=2, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
def list_available_models(tier: str = "all") -> str:
    """
    Lists models supported by the hybrid dispatcher, their tier, context window, and pricing.

    Args:
        tier: Filter by tier ('all', 'local', 'openrouter_free', 'openrouter_smart').
    """
    t_filter = (tier or "all").lower().strip()
    result = {}
    for model_id, info in MODEL_CATALOG.items():
        if t_filter == "all" or info["tier"] == t_filter:
            result[model_id] = {
                "tier": info["tier"],
                "name": info["name"],
                "context": info["context"],
                "price_1m_input_usd": f"${info['price_in']:.2f}",
                "price_1m_output_usd": f"${info['price_out']:.2f}",
                "description": info["description"]
            }
    return json.dumps(result, indent=2, ensure_ascii=False)


@mcp.tool()
def classify_task_complexity(task_description: str) -> str:
    """
    Analyzes task description and suggests ideal AI tier and model to minimize costs.

    Args:
        task_description: Description of the task to be performed.
    """
    t_lower = (task_description or "").lower()

    smart_triggers = [
        "architecture", "security", "cryptography", "vulnerability",
        "redesign", "deadlock", "concurrency", "deepseek-r1", "audit trail"
    ]
    free_triggers = [
        "refactor", "optimize", "improve", "simplify",
        "integration test", "code review", "explain"
    ]

    for trigger in smart_triggers:
        if trigger in t_lower:
            return json.dumps({
                "suggested_tier": "openrouter_smart",
                "recommended_model": "deepseek/deepseek-r1",
                "reason": f"Task contains critical keyword ('{trigger}') requiring analytical reasoning or security rigor.",
                "requires_user_confirmation": True
            }, indent=2, ensure_ascii=False)

    for trigger in free_triggers:
        if trigger in t_lower:
            return json.dumps({
                "suggested_tier": "openrouter_free",
                "recommended_model": "qwen/qwen3.8-27b:free",
                "reason": f"Task involves intermediate logic ('{trigger}') suitable for free 27B+ models.",
                "requires_user_confirmation": False
            }, indent=2, ensure_ascii=False)

    return json.dumps({
        "suggested_tier": "local",
        "recommended_model": "qwen/qwen2.5-coder-7b-instruct",
        "reason": "Routine or mechanical coding task ideal for fast offline execution with zero API cost.",
        "requires_user_confirmation": False
    }, indent=2, ensure_ascii=False)


@mcp.tool()
def run_local_code_task(
    instruction: str,
    context_code: str = "",
    complexity: str = "local",
    model_override: Optional[str] = None
) -> str:
    """
    Executes a coding instruction using the hybrid router (local LLM or cloud).

    Args:
        instruction: What to implement or generate.
        context_code: Optional existing code snippet or context.
        complexity: 'local' (offline free), 'openrouter_free' ($0 cloud) or 'openrouter_smart' (DeepSeek-R1, Sonnet).
        model_override: Optional specific model ID.
    """
    system_prompt = (
        "You are an expert software engineer assistant.\n"
        "Provide clean, well-structured, production-ready code with concise explanations."
    )

    user_prompt = instruction
    if context_code:
        user_prompt += f"\n\nProvided context:\n```\n{context_code}\n```"

    return call_routed_ai(
        prompt=user_prompt,
        system_prompt=system_prompt,
        complexity=complexity,
        model_override=model_override,
        temperature=0.1,
        tool_name="run_local_code_task"
    )


@mcp.tool()
def generate_ts_dtos(
    schema_or_sql: str,
    additional_requirements: str = "",
    complexity: str = "local",
    model_override: Optional[str] = None
) -> str:
    """
    Converts SQL table schemas (CREATE TABLE), database definitions or JSON objects into clean TypeScript interfaces and DTOs.

    Args:
        schema_or_sql: SQL DDL, schema, or JSON object example.
        additional_requirements: Optional additional typing requirements.
        complexity: 'local', 'openrouter_free' or 'openrouter_smart'.
        model_override: Optional specific model ID.
    """
    system_prompt = (
        "You are an expert TypeScript architect.\n"
        "Rules:\n"
        "1. Generate strict TypeScript interfaces (entity, create DTO without ID, update DTO as Partial).\n"
        "2. Ensure accurate typing (string, number, boolean, Date).\n"
        "Return clean, production-ready TypeScript code."
    )

    user_prompt = f"Generate TypeScript interfaces and DTOs for the following schema:\n\n```sql\n{schema_or_sql}\n```"
    if additional_requirements:
        user_prompt += f"\n\nRequirements: {additional_requirements}"

    return call_routed_ai(
        prompt=user_prompt,
        system_prompt=system_prompt,
        complexity=complexity,
        model_override=model_override,
        temperature=0.1,
        tool_name="generate_ts_dtos"
    )


@mcp.tool()
def validate_code_syntax(
    code_content: str,
    language: str = "typescript",
    complexity: str = "local",
    model_override: Optional[str] = None
) -> str:
    """
    Performs static and syntax audit on a code snippet. Checks typing, security, and potential errors.

    Args:
        code_content: Code to inspect.
        language: Programming language (default: 'typescript').
        complexity: 'local', 'openrouter_free' or 'openrouter_smart'.
        model_override: Optional specific model ID.
    """
    system_prompt = (
        f"You are a senior {language} code reviewer.\n"
        "Analyze the code and verify syntax correctness, potential null reference bugs, security concerns and code smells.\n"
        "Provide bullet points of findings and corrected code if needed."
    )

    user_prompt = f"Review the following {language} code:\n\n```{language}\n{code_content}\n```"
    return call_routed_ai(
        prompt=user_prompt,
        system_prompt=system_prompt,
        complexity=complexity,
        model_override=model_override,
        temperature=0.1,
        tool_name="validate_code_syntax"
    )


@mcp.tool()
def generate_unit_tests(
    code_snippet: str,
    test_framework: str = "jest",
    complexity: str = "local",
    model_override: Optional[str] = None
) -> str:
    """
    Generates a complete unit test suite for a given function, model or service.

    Args:
        code_snippet: Code to test.
        test_framework: 'jest', 'vitest', 'pytest' or 'mocha'.
        complexity: 'local', 'openrouter_free' or 'openrouter_smart'.
        model_override: Optional specific model ID.
    """
    system_prompt = (
        f"You are a test automation specialist using {test_framework}.\n"
        "Generate comprehensive unit tests covering:\n"
        "1. Happy path scenarios.\n"
        "2. Edge cases, empty inputs, null values.\n"
        "3. Error handling and thrown exceptions.\n"
        "Organize with clear describe and test/it blocks."
    )

    user_prompt = f"Generate unit tests for the following code:\n\n```\n{code_snippet}\n```"
    return call_routed_ai(
        prompt=user_prompt,
        system_prompt=system_prompt,
        complexity=complexity,
        model_override=model_override,
        temperature=0.1,
        tool_name="generate_unit_tests"
    )


@mcp.tool()
def check_local_ai_health() -> str:
    """
    Checks connectivity and health of local inference server (LM Studio / Ollama)
    and OpenRouter cloud gateway.
    """
    result = {
        "local_server": {},
        "openrouter_gateway": {}
    }

    # 1. Local server check
    try:
        with httpx.Client(timeout=4.0) as client:
            resp = client.get(f"{BASE_URL}/models")
            if resp.status_code == 200:
                data = resp.json()
                models = [m.get("id") for m in data.get("data", [])]
                result["local_server"] = {
                    "status": "online",
                    "base_url": BASE_URL,
                    "active_model": get_active_model_id(),
                    "available_models_count": len(models)
                }
            else:
                result["local_server"] = {
                    "status": "error",
                    "http_status": resp.status_code
                }
    except Exception as e:
        result["local_server"] = {
            "status": "offline",
            "base_url": BASE_URL,
            "error": str(e),
            "tip": "Start LM Studio or Ollama with API server enabled on the configured port."
        }

    # 2. OpenRouter gateway check
    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.get(
                f"{OPENROUTER_BASE_URL}/models",
                headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
            )
            if resp.status_code == 200:
                result["openrouter_gateway"] = {
                    "status": "online",
                    "endpoint": OPENROUTER_BASE_URL,
                    "catalog_models_count": len(MODEL_CATALOG)
                }
            else:
                result["openrouter_gateway"] = {
                    "status": "error",
                    "http_status": resp.status_code
                }
    except Exception as e:
        result["openrouter_gateway"] = {
            "status": "offline",
            "error": str(e)
        }

    return json.dumps(result, indent=2, ensure_ascii=False)

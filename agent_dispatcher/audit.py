"""
Audit module and token/cost tracking for FastMCP Dispatcher.
"""

import os
import json
import csv as csv_mod
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

from agent_dispatcher.config import (
    logger,
    METRICS_FILE,
    LOCAL_AUDIT_CSV,
    LOCAL_AUDIT_JSON,
    BUDGET_FILE,
    CACHE_DIR,
    MODEL_CATALOG,
    PRICING_TABLE,
    BRL_RATE
)


def get_model_rates(model_id: str) -> Dict[str, float]:
    """Returns price per 1M tokens (in/out) for the specified model."""
    if model_id in MODEL_CATALOG:
        return {
            "in": MODEL_CATALOG[model_id]["price_in"],
            "out": MODEL_CATALOG[model_id]["price_out"]
        }
    lower = model_id.lower()
    if ":free" in lower:
        return {"in": 0.0, "out": 0.0}
    if "r1" in lower or "deepseek" in lower:
        return {"in": 0.55, "out": 2.19}
    if "claude" in lower and "sonnet" in lower:
        return {"in": 3.00, "out": 15.00}
    if "opus" in lower:
        return {"in": 5.00, "out": 25.00}
    if "gpt-4o" in lower:
        return {"in": 2.50, "out": 10.00}
    return {"in": 1.00, "out": 3.00}


def record_token_usage(
    prompt_tokens: int,
    completion_tokens: int,
    duration_ms: float = 0.0,
    tool_name: str = "task",
    provider: str = "local",
    model_used: str = ""
):
    """
    Records token consumption in:
    1. local_ai_audit.csv with savings calculated against Claude 3.5 Sonnet / GPT-4o.
    2. local_ai_audit.json and .agents/local_ai_metrics.json.
    """
    total_tokens = prompt_tokens + completion_tokens
    now = datetime.now()
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")
    model = model_used or ("qwen-local" if provider == "local" else "openrouter")

    try:
        os.makedirs(os.path.dirname(METRICS_FILE), exist_ok=True)
        c_in_m = prompt_tokens / 1_000_000
        c_out_m = completion_tokens / 1_000_000

        # Calculate actual cost
        if provider in ("local", "openrouter_free"):
            cost_real = 0.00
        else:
            rates = get_model_rates(model)
            cost_real = (c_in_m * rates["in"]) + (c_out_m * rates["out"])

        # Equivalent benchmark costs
        cost_claude = (c_in_m * PRICING_TABLE["claude_3_5_sonnet"]["in"]) + (c_out_m * PRICING_TABLE["claude_3_5_sonnet"]["out"])
        cost_gpt4o = (c_in_m * PRICING_TABLE["gpt_4o"]["in"]) + (c_out_m * PRICING_TABLE["gpt_4o"]["out"])
        cost_gemini = (c_in_m * PRICING_TABLE["gemini_2_0_flash"]["in"]) + (c_out_m * PRICING_TABLE["gemini_2_0_flash"]["out"])

        saved_vs_claude = max(0.0, cost_claude - cost_real)

        csv_header = [
            "timestamp", "tool_name", "provider", "model",
            "prompt_tokens", "completion_tokens", "total_tokens",
            "duration_ms", "cost_real_usd", "equiv_claude_sonnet_usd",
            "equiv_gpt4o_usd", "equiv_gemini_flash_usd", "saved_usd", "saved_currency"
        ]

        need_header = not os.path.exists(LOCAL_AUDIT_CSV)

        with open(LOCAL_AUDIT_CSV, "a", encoding="utf-8", newline="") as f:
            writer = csv_mod.writer(f)
            if need_header:
                writer.writerow(csv_header)
            writer.writerow([
                now_str,
                tool_name,
                provider,
                model,
                prompt_tokens,
                completion_tokens,
                total_tokens,
                f"{duration_ms:.2f}",
                f"{cost_real:.6f}",
                f"{cost_claude:.6f}",
                f"{cost_gpt4o:.6f}",
                f"{cost_gemini:.6f}",
                f"{saved_vs_claude:.6f}",
                f"{saved_vs_claude * BRL_RATE:.2f}"
            ])

        metrics: Dict[str, Any] = {
            "total_requests": 0,
            "local_requests": 0,
            "openrouter_free_requests": 0,
            "openrouter_paid_requests": 0,
            "total_prompt_tokens": 0,
            "total_completion_tokens": 0,
            "total_tokens": 0,
            "total_cost_real_usd": 0.0,
            "total_saved_vs_claude_usd": 0.0,
            "history": []
        }

        if os.path.exists(METRICS_FILE):
            try:
                with open(METRICS_FILE, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    metrics.update(loaded)
            except Exception:
                pass

        metrics["total_requests"] = metrics.get("total_requests", 0) + 1
        if provider == "local":
            metrics["local_requests"] = metrics.get("local_requests", 0) + 1
        elif provider == "openrouter_free":
            metrics["openrouter_free_requests"] = metrics.get("openrouter_free_requests", 0) + 1
        else:
            metrics["openrouter_paid_requests"] = metrics.get("openrouter_paid_requests", 0) + 1

        metrics["total_prompt_tokens"] = metrics.get("total_prompt_tokens", 0) + prompt_tokens
        metrics["total_completion_tokens"] = metrics.get("total_completion_tokens", 0) + completion_tokens
        metrics["total_tokens"] = metrics.get("total_tokens", 0) + total_tokens
        metrics["total_cost_real_usd"] = round(metrics.get("total_cost_real_usd", 0.0) + cost_real, 6)

        tot_saved = metrics.get("total_saved_vs_claude_usd", 0.0) + saved_vs_claude
        metrics["total_saved_vs_claude_usd"] = round(tot_saved, 6)
        metrics["total_saved_vs_claude_currency"] = round(tot_saved * BRL_RATE, 2)

        history = metrics.get("history", [])
        history.append({
            "timestamp": now.isoformat(),
            "tool": tool_name,
            "provider": provider,
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "duration_ms": round(duration_ms, 2),
            "cost_real_usd": round(cost_real, 6),
            "equiv_claude_usd": round(cost_claude, 6),
            "saved_vs_claude_usd": round(saved_vs_claude, 6)
        })
        metrics["history"] = history[-100:]

        with open(METRICS_FILE, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2)

        with open(LOCAL_AUDIT_JSON, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2, ensure_ascii=False)

        logger.info(
            f"[METRICS] [{provider.upper()}] Tool: {tool_name} | Model: {model} | In: {prompt_tokens} | Out: {completion_tokens} | "
            f"Real Cost: ${cost_real:.5f} | Saved vs Claude: ${saved_vs_claude:.5f}"
        )
    except Exception as e:
        logger.warning(f"Failed to record token metrics: {e}")


def check_daily_budget() -> Tuple[bool, str]:
    """
    Checks if daily budget limit in USD (.agents/ai_budget.json) has been exceeded.
    Returns (allowed: bool, message: str).
    """
    if not os.path.exists(BUDGET_FILE):
        return True, ""
    try:
        with open(BUDGET_FILE, "r", encoding="utf-8") as f:
            b_data = json.load(f)
        daily_limit = float(b_data.get("daily_budget_usd", 1.00))
        hard_stop = bool(b_data.get("hard_stop", True))
        alert_pct = float(b_data.get("alert_threshold_pct", 80))

        today_str = datetime.now().strftime("%Y-%m-%d")
        today_spent = 0.0
        if os.path.exists(METRICS_FILE):
            with open(METRICS_FILE, "r", encoding="utf-8") as mf:
                m_data = json.load(mf)
            for h in m_data.get("history", []):
                ts = h.get("timestamp", "")
                if ts.startswith(today_str):
                    today_spent += float(h.get("cost_real_usd", 0.0))

        if hard_stop and today_spent >= daily_limit:
            msg = (
                f"[BUDGET EXCEEDED] Daily limit of ${daily_limit:.2f} USD reached today "
                f"(Spent today: ${today_spent:.4f} USD). Paid call blocked."
            )
            logger.error(msg)
            return False, msg

        if today_spent >= (daily_limit * (alert_pct / 100)):
            logger.warning(
                f"[BUDGET WARNING] Daily spend of ${today_spent:.4f} USD reached {alert_pct:.0f}% of limit (${daily_limit:.2f} USD)."
            )

        return True, ""
    except Exception as e:
        logger.warning(f"Error checking daily budget: {e}")
        return True, ""


def generate_cache_key(model: str, tool_name: str, prompt: str, system_prompt: str) -> str:
    """Generates unique SHA256 cache key based on prompt, model and tool."""
    content = f"{model}:::{tool_name}:::{system_prompt}:::{prompt}"
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def get_from_cache(cache_key: str) -> Optional[str]:
    """Retrieves cached response if present."""
    cache_path = os.path.join(CACHE_DIR, f"{cache_key}.json")
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            logger.info(f"[CACHE HIT] Response retrieved from cache (key: {cache_key[:8]}...)")
            return data.get("response")
        except Exception as e:
            logger.warning(f"Error reading cache: {e}")
    return None


def save_to_cache(cache_key: str, response: str, model: str, tool_name: str):
    """Saves response to local JSON cache."""
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        cache_path = os.path.join(CACHE_DIR, f"{cache_key}.json")
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "model": model,
                "tool": tool_name,
                "response": response
            }, f, indent=2, ensure_ascii=False)
        logger.info(f"[CACHE SAVED] Response saved to cache (key: {cache_key[:8]}...)")
    except Exception as e:
        logger.warning(f"Error saving to cache: {e}")

#!/usr/bin/env python3
"""
Savings & Efficiency Report Generator
Consolidates metrics from local AI, OpenRouter, and Antigravity cloud conversations.
Outputs a clean Markdown report to docs/reports/savings_report.md and prints summary.
"""

import os
import sys
import json
import csv
from datetime import datetime

# Force UTF-8 on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
METRICS_FILE = os.path.join(PROJECT_ROOT, ".agents", "local_ai_metrics.json")
LOCAL_CSV = os.path.join(PROJECT_ROOT, "local_ai_audit.csv")
CLOUD_CSV = os.path.join(PROJECT_ROOT, "tokens_audit.csv")
REPORTS_DIR = os.path.join(PROJECT_ROOT, "docs", "reports")
REPORT_MD = os.path.join(REPORTS_DIR, "savings_report.md")

BRL_USD = float(os.environ.get("CURRENCY_RATE_USD", "5.75"))


def generate_report():
    os.makedirs(REPORTS_DIR, exist_ok=True)
    now = datetime.now()
    now_str = now.strftime("%Y-%m-%d %H:%M")

    local_metrics = {}
    if os.path.exists(METRICS_FILE):
        try:
            with open(METRICS_FILE, "r", encoding="utf-8") as f:
                local_metrics = json.load(f)
        except Exception:
            pass

    total_local_reqs = local_metrics.get("total_requests", 0)
    local_offline_reqs = local_metrics.get("local_requests", 0)
    or_free_reqs = local_metrics.get("openrouter_free_requests", 0)
    or_paid_reqs = local_metrics.get("openrouter_paid_requests", 0)
    local_in = local_metrics.get("total_prompt_tokens", 0)
    local_out = local_metrics.get("total_completion_tokens", 0)
    local_total = local_metrics.get("total_tokens", 0)
    cost_real = local_metrics.get("total_cost_real_usd", 0.0)
    saved_claude = local_metrics.get("total_saved_vs_claude_usd", 0.0)

    cloud_turns = 0
    cloud_in = 0
    cloud_out = 0
    cloud_cost = 0.0
    models_used = set()

    if os.path.exists(CLOUD_CSV):
        try:
            with open(CLOUD_CSV, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                if header:
                    for r in reader:
                        if len(r) >= 8:
                            cloud_turns += 1
                            models_used.add(r[3])
                            cloud_in += int(r[4]) if r[4].isdigit() else 0
                            cloud_out += int(r[5]) if r[5].isdigit() else 0
                            try:
                                cloud_cost += float(r[7])
                            except ValueError:
                                pass
        except Exception:
            pass

    cloud_total = cloud_in + cloud_out
    grand_total_tokens = local_total + cloud_total

    # Cost if everything was run on Claude 3.5 Sonnet
    equiv_claude_total = ((grand_total_tokens / 1_000_000) * 0.4 * 3.0) + ((grand_total_tokens / 1_000_000) * 0.6 * 15.0)
    real_spent_total = cost_real + cloud_cost
    net_savings_usd = max(0.0, equiv_claude_total - real_spent_total)

    md_content = f"""# AI Token & Cost Efficiency Report

**Generated at:** {now_str}  
**Exchange rate reference:** 1 USD = {BRL_USD:.2f} BRL  

---

## 1. Executive Summary

| Metric | Local AI (MCP) | Cloud Agent Sessions | Consolidated Total |
|---|---|---|---|
| **Requests / Turns** | {total_local_reqs} | {cloud_turns} | {total_local_reqs + cloud_turns} |
| **Input Tokens** | {local_in:,} | {cloud_in:,} | {local_in + cloud_in:,} |
| **Output Tokens** | {local_out:,} | {cloud_out:,} | {local_out + cloud_out:,} |
| **Total Tokens** | {local_total:,} | {cloud_total:,} | {grand_total_tokens:,} |
| **Real Cost (USD)** | ${cost_real:.4f} | ${cloud_cost:.4f} | ${real_spent_total:.4f} |
| **Real Cost (BRL)** | R$ {cost_real * BRL_USD:.2f} | R$ {cloud_cost * BRL_USD:.2f} | R$ {real_spent_total * BRL_USD:.2f} |

---

## 2. Savings Benchmark

- **Theoretical Cost on Claude 3.5 Sonnet:** ${equiv_claude_total:.2f} USD (~R$ {equiv_claude_total * BRL_USD:.2f})
- **Actual Total Expenditure:** ${real_spent_total:.2f} USD (~R$ {real_spent_total * BRL_USD:.2f})
- **Net Savings:** **${net_savings_usd:.2f} USD** (~**R$ {net_savings_usd * BRL_USD:.2f}**)

---

## 3. Distribution & Routing

- **Local Offline Requests (LM Studio / Ollama):** {local_offline_reqs} (100% Free)
- **OpenRouter Free Tier:** {or_free_reqs} (100% Free)
- **OpenRouter Paid / Smart Tier:** {or_paid_reqs}
- **Active Cloud Models in Sessions:** {', '.join(sorted(models_used)) if models_used else 'N/A'}

---
*Report generated automatically by Antigravity Token Auditor.*
"""

    with open(REPORT_MD, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"Report successfully written to {REPORT_MD}")
    print(f"Total Net Savings: ${net_savings_usd:.2f} USD (~R$ {net_savings_usd * BRL_USD:.2f})")


if __name__ == "__main__":
    generate_report()

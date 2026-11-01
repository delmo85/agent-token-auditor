#!/usr/bin/env python3
"""
CLI Token & Cost Analyzer
Quickly inspect session tokens, cost estimates, and savings.
"""

import os
import sys
import json
import csv
import glob

# Force UTF-8 on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIT_CSV = os.path.join(PROJECT_ROOT, "tokens_audit.csv")
LOCAL_CSV = os.path.join(PROJECT_ROOT, "local_ai_audit.csv")

BRL_USD = float(os.environ.get("CURRENCY_RATE_USD", "5.75"))

# Benchmark rates per 1M tokens (USD)
BENCHMARKS = {
    "gemini_flash": {"in": 0.15, "out": 0.60, "name": "Google Gemini 2.5/3.8 Flash"},
    "claude_sonnet": {"in": 3.00, "out": 15.00, "name": "Anthropic Claude 3.5 Sonnet"},
    "claude_opus": {"in": 5.00, "out": 25.00, "name": "Anthropic Claude 3 Opus"},
    "gpt_4o": {"in": 2.50, "out": 10.00, "name": "OpenAI GPT-4o"},
    "qwen_local": {"in": 0.00, "out": 0.00, "name": "Local Qwen 2.5 Coder (LM Studio/Ollama)"}
}


def print_banner():
    print("=" * 70)
    print("           AI TOKEN & COST AUDITOR SUMMARY")
    print("=" * 70)


def analyze():
    print_banner()

    cloud_turns = 0
    cloud_in = 0
    cloud_out = 0
    cloud_cost = 0.0

    if os.path.exists(AUDIT_CSV):
        with open(AUDIT_CSV, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            if header:
                for r in reader:
                    if len(r) >= 8:
                        cloud_turns += 1
                        cloud_in += int(r[4]) if r[4].isdigit() else 0
                        cloud_out += int(r[5]) if r[5].isdigit() else 0
                        try:
                            cloud_cost += float(r[7])
                        except ValueError:
                            pass

    local_calls = 0
    local_in = 0
    local_out = 0
    local_saved_usd = 0.0

    if os.path.exists(LOCAL_CSV):
        with open(LOCAL_CSV, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            if header:
                for r in reader:
                    if len(r) >= 13:
                        local_calls += 1
                        local_in += int(r[4]) if r[4].isdigit() else 0
                        local_out += int(r[5]) if r[5].isdigit() else 0
                        try:
                            local_saved_usd += float(r[12])
                        except ValueError:
                            pass

    total_in = cloud_in + local_in
    total_out = cloud_out + local_out
    total_all = total_in + total_out

    print(f"\n[1] ANTIGRAVITY CLOUD SESSIONS ({AUDIT_CSV})")
    print(f"  • Total Turns Audited:    {cloud_turns}")
    print(f"  • Input Tokens (Prompts): {cloud_in:,}")
    print(f"  • Output Tokens:          {cloud_out:,}")
    print(f"  • Total Cloud Tokens:     {cloud_in + cloud_out:,}")
    print(f"  • Total Real Cost:        ${cloud_cost:.4f} USD (~R$ {cloud_cost * BRL_USD:.2f})")

    print(f"\n[2] LOCAL AI / MCP OFFLOADED TASKS ({LOCAL_CSV})")
    print(f"  • Total Local Tasks:      {local_calls}")
    print(f"  • Offline Prompt Tokens:  {local_in:,}")
    print(f"  • Offline Output Tokens:  {local_out:,}")
    print(f"  • Total Local Tokens:     {local_in + local_out:,} (100% Free)")
    print(f"  • Savings vs Claude:      ${local_saved_usd:.4f} USD (~R$ {local_saved_usd * BRL_USD:.2f})")

    print("\n[3] EQUIVALENT COST IF RUN 100% ON PROPRIETARY MODELS")
    in_m = total_in / 1_000_000
    out_m = total_out / 1_000_000

    for key, spec in BENCHMARKS.items():
        c = (in_m * spec["in"]) + (out_m * spec["out"])
        print(f"  • {spec['name']:<42} : ${c:8.4f} USD (~R$ {c * BRL_USD:7.2f})")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    analyze()

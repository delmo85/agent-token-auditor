#!/usr/bin/env python3
"""
Antigravity Token & Model Auditor Hook
Executed after each turn (Stop / PostInvocation) by Google Antigravity via hooks.json.
Captures active model, input tokens, output tokens, thinking process, tool calls and costs.
Saves logs to tokens_audit.csv and tokens_audit.json.
Also supports full historical sync via `--sync`.
"""

import sys
import os
import json
import glob
import re
import csv as csv_mod
from datetime import datetime

# Force UTF-8 output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIT_CSV = os.path.join(PROJECT_ROOT, "tokens_audit.csv")
AUDIT_JSON = os.path.join(PROJECT_ROOT, "tokens_audit.json")

# Benchmark reference pricing per 1M tokens (USD)
PRICING = {
    "gemini-2.0-flash": {"in": 0.10, "out": 0.40},
    "gemini-2.5-flash": {"in": 0.15, "out": 0.60},
    "gemini-3.8-flash": {"in": 0.15, "out": 0.60},
    "gemini": {"in": 0.15, "out": 0.60},
    "claude-opus": {"in": 5.00, "out": 25.00},
    "claude-3-5-sonnet": {"in": 3.00, "out": 15.00},
    "claude-sonnet-4": {"in": 3.00, "out": 15.00},
    "claude-sonnet-5": {"in": 2.00, "out": 10.00},
    "claude-sonnet": {"in": 3.00, "out": 15.00},
    "gpt-4o": {"in": 2.50, "out": 10.00},
    "gpt-5": {"in": 1.25, "out": 10.00},
    "o3": {"in": 2.00, "out": 8.00},
    "o3-mini": {"in": 1.10, "out": 4.40},
    "deepseek-r1": {"in": 0.70, "out": 2.50},
    "default": {"in": 0.15, "out": 0.60}
}


def calculate_cost(model_name: str, in_tokens: int, out_tokens: int) -> float:
    """Calculates approximate USD cost based on model name and token volume."""
    name_lower = (model_name or "").lower()
    rates = PRICING["default"]
    if "opus" in name_lower:
        rates = PRICING["claude-opus"]
    elif "sonnet-5" in name_lower or "sonnet 5" in name_lower:
        rates = PRICING["claude-sonnet-5"]
    elif "sonnet" in name_lower:
        rates = PRICING["claude-sonnet"]
    elif "gpt-5" in name_lower:
        rates = PRICING["gpt-5"]
    elif "gpt-4o" in name_lower:
        rates = PRICING["gpt-4o"]
    elif "o3-mini" in name_lower:
        rates = PRICING["o3-mini"]
    elif "o3" in name_lower:
        rates = PRICING["o3"]
    elif "deepseek" in name_lower or "r1" in name_lower:
        rates = PRICING["deepseek-r1"]
    elif "gemini" in name_lower:
        rates = PRICING["gemini-3.8-flash"]
    return (in_tokens / 1_000_000 * rates["in"]) + (out_tokens / 1_000_000 * rates["out"])


def find_latest_transcript() -> str:
    """Finds the most recent Antigravity conversation transcript."""
    possible_roots = []

    # 1. Environment variable if set
    env_dir = os.environ.get("ANTIGRAVITY_DATA_DIR")
    if env_dir and os.path.exists(env_dir):
        possible_roots.append(env_dir)

    # 2. Standard user home directories
    home = os.path.expanduser("~")
    possible_roots.extend([
        os.path.join(home, ".gemini", "antigravity", "brain"),
        os.path.join(home, ".gemini", "antigravity-ide", "brain"),
        os.path.join(home, ".antigravity", "brain")
    ])

    candidates = []
    for root in possible_roots:
        if os.path.exists(root):
            candidates.extend(glob.glob(os.path.join(root, "*", ".system_generated", "logs", "transcript_full.jsonl")))
            candidates.extend(glob.glob(os.path.join(root, "*", ".system_generated", "logs", "transcript.jsonl")))

    if candidates:
        candidates.sort(key=os.path.getmtime, reverse=True)
        return candidates[0]

    return None


def sync_full_history(transcript_path: str = None, model_name: str = None) -> int:
    """Reads full transcript, parses turns, detects model changes, and writes to CSV/JSON."""
    if not transcript_path or not os.path.exists(transcript_path):
        transcript_path = find_latest_transcript()

    if not transcript_path or not os.path.exists(transcript_path):
        return 0

    conv_id = os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(transcript_path))))
    turns = []
    current_user = None
    current_model_content = ""
    current_model_thinking = ""
    current_tools_chars = 0
    step_idx = 0
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    current_model = model_name or "Gemini 3.8 Flash (High)"
    turn_model = current_model

    with open(transcript_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                d = json.loads(line)
                src = d.get("source")
                stype = d.get("type")
                content = d.get("content", "") or ""
                thinking = d.get("thinking", "") or ""
                tcalls = json.dumps(d.get("tool_calls", [])) if d.get("tool_calls") else ""

                # Detect dynamic model switch events in system messages
                if "Model Selection" in content:
                    m = re.search(r"Model Selection[`\s]*from\s+(.+?)\s+to\s+(.+?)(?:\.\s*(?:No need|\n|<)|$)", content)
                    if m:
                        current_model = m.group(2).strip("`").strip()

                if src == "USER_EXPLICIT" or stype == "USER_INPUT":
                    if current_user is not None:
                        turns.append({
                            "step": step_idx,
                            "timestamp": current_time,
                            "model": turn_model,
                            "user_chars": len(current_user),
                            "model_chars": len(current_model_content) + len(current_model_thinking) + current_tools_chars,
                            "prompt_snippet": current_user[:60].replace("\n", " ")
                        })
                    current_user = content
                    turn_model = current_model
                    if d.get("created_at"):
                        try:
                            dt = datetime.fromisoformat(d.get("created_at").replace("Z", "+00:00"))
                            current_time = dt.strftime("%Y-%m-%d %H:%M:%S")
                        except Exception:
                            pass
                    current_model_content = ""
                    current_model_thinking = ""
                    current_tools_chars = 0
                    step_idx = d.get("step_index", 0)
                else:
                    current_model_content += content
                    current_model_thinking += thinking
                    current_tools_chars += len(tcalls)
            except Exception:
                pass

    if current_user is not None:
        turns.append({
            "step": step_idx,
            "timestamp": current_time,
            "model": turn_model,
            "user_chars": len(current_user),
            "model_chars": len(current_model_content) + len(current_model_thinking) + current_tools_chars,
            "prompt_snippet": current_user[:60].replace("\n", " ")
        })

    CSV_HEADER = [
        "timestamp", "conversation_id", "step_idx", "model",
        "input_tokens", "output_tokens", "total_tokens",
        "cost_usd", "estimation_method", "prompt_preview"
    ]

    # Map of calculated turns
    turns_map = {}
    for t in turns:
        # 3.8 chars per token is standard empirical average for code + multilingual text
        in_t = max(1, int(t["user_chars"] / 3.8))
        out_t = max(1, int(t["model_chars"] / 3.8))
        tot_t = in_t + out_t
        cost = calculate_cost(t["model"], in_t, out_t)
        turns_map[(conv_id, t["step"])] = [
            t["timestamp"],
            conv_id,
            str(t["step"]),
            t["model"],
            str(in_t),
            str(out_t),
            str(tot_t),
            f"{cost:.6f}",
            "heuristic_3.8",
            t["prompt_snippet"]
        ]

    existing_rows = []
    seen_keys = set()

    if os.path.exists(AUDIT_CSV):
        try:
            with open(AUDIT_CSV, "r", encoding="utf-8") as f:
                reader = csv_mod.reader(f)
                header = next(reader, None)
                if header:
                    conv_col = header.index("conversation_id") if "conversation_id" in header else 1
                    step_col = header.index("step_idx") if "step_idx" in header else 2

                    for row in reader:
                        if len(row) > max(conv_col, step_col):
                            c_id = row[conv_col]
                            s_idx = int(row[step_col]) if row[step_col].isdigit() else row[step_col]
                            key = (c_id, s_idx)
                            if key in turns_map:
                                existing_rows.append(turns_map[key])
                                seen_keys.add(key)
                            else:
                                existing_rows.append(row)
                                seen_keys.add(key)
        except Exception as e:
            sys.stderr.write(f"[TokenAuditor] Error reading existing CSV: {e}\n")

    for key, row_data in turns_map.items():
        if key not in seen_keys:
            existing_rows.append(row_data)

    with open(AUDIT_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv_mod.writer(f)
        writer.writerow(CSV_HEADER)
        writer.writerows(existing_rows)

    json_records = []
    for row in existing_rows:
        if len(row) >= 10:
            json_records.append({
                "timestamp": row[0],
                "conversation_id": row[1],
                "step_idx": int(row[2]) if row[2].isdigit() else row[2],
                "model": row[3],
                "input_tokens": int(row[4]) if row[4].isdigit() else 0,
                "output_tokens": int(row[5]) if row[5].isdigit() else 0,
                "total_tokens": int(row[6]) if row[6].isdigit() else 0,
                "cost_usd": float(row[7]) if row[7].replace(".", "", 1).isdigit() else 0.0,
                "estimation_method": row[8],
                "prompt_preview": row[9]
            })

    with open(AUDIT_JSON, "w", encoding="utf-8") as jf:
        json.dump(json_records, jf, indent=2, ensure_ascii=False)

    return len(turns)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--sync":
        total = sync_full_history()
        print(f"Sync complete: {total} turns recorded in {AUDIT_CSV}")
        return

    raw_input = ""
    try:
        raw_input = sys.stdin.read()
    except Exception:
        pass

    payload = {}
    if raw_input.strip():
        try:
            payload = json.loads(raw_input)
        except Exception:
            pass

    transcript_path = payload.get("transcriptPath")
    model_name = payload.get("modelName") or "gemini-3.8-flash"

    try:
        sync_full_history(transcript_path, model_name)
        sys.stderr.write(f"[TokenAuditor] Synchronized conversation turns in {AUDIT_CSV}\n")
    except Exception as e:
        sys.stderr.write(f"[TokenAuditor] Error: {e}\n")

    # Antigravity hook response protocol
    res = {"decision": "allow", "injectSteps": []}
    sys.stdout.write(json.dumps(res))
    sys.stdout.flush()


if __name__ == "__main__":
    main()


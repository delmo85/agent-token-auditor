# 💡 Practical Examples & Usage Guide / Exemplos Práticos de Uso

This guide provides real-world examples of how to use the **Agent Token Auditor & FastMCP Dispatcher** across different IDEs, workflows, and standalone environments.

---

## 📑 Table of Contents / Índice
1. [Example 1: Automatic Live Token Tracking in Google Antigravity](#example-1-automatic-live-token-tracking-in-google-antigravity)
2. [Example 2: FastMCP Integration with Cursor IDE](#example-2-fastmcp-integration-with-cursor-ide)
3. [Example 3: Offloading Boilerplate & Tests in VS Code (Cline / Roo Code)](#example-3-offloading-boilerplate--tests-in-vs-code-cline--roo-code)
4. [Example 4: Claude Desktop Integration & Token Telemetry](#example-4-claude-desktop-integration--token-telemetry)
5. [Example 5: Standalone CLI Analytics & Savings Reports](#example-5-standalone-cli-analytics--savings-reports)
6. [Example 6: Programmatic Python Usage in Custom Agents (LangChain, CrewAI, LiteLLM)](#example-6-programmatic-python-usage-in-custom-agents)

---

## Example 1: Automatic Live Token Tracking in Google Antigravity

In Google Antigravity, token tracking is **100% automated**. You don't have to invoke anything manually.

### 1. File Placement
Ensure your project contains:
```text
my-project/
├── .agents/
│   ├── hooks.json
│   ├── run_auditor.cmd      # (Windows)
│   └── run_auditor.sh       # (Linux/macOS)
└── scripts/
    └── log_iteration_tokens.py
```

### 2. What Happens Behind the Scenes
- Every time you send a prompt and the agent finishes replying or stops, Antigravity triggers `Stop` or `PostInvocation` from `hooks.json`.
- The hook parses the latest `transcript_full.jsonl`, calculates tokens (inputs, outputs, tools, reasoning), estimates costs in USD, and logs the result.

### 3. Output in `tokens_audit.csv`
A new line is appended automatically after each turn:
```csv
timestamp,conversation_id,step_idx,model,input_tokens,output_tokens,total_tokens,cost_usd,estimation_method,prompt_preview
2026-11-01 14:30:15,fa8a78df-c77c-42d8-94d6-2677ff4ddcdf,0,Gemini 3.8 Flash,319,1850,2169,0.001158,heuristic_3.8,"Refactor the authentication middleware to use JWT"
2026-11-01 14:35:40,fa8a78df-c77c-42d8-94d6-2677ff4ddcdf,12,Claude Sonnet 3.5,190,4200,4390,0.063570,heuristic_3.8,"Add unit tests covering edge cases for token expiration"
```

### 4. Output in `tokens_audit.json`
Provides structured JSON data ready for consumption by BI dashboards, Grafana, or custom webhooks:
```json
[
  {
    "timestamp": "2026-11-01 14:30:15",
    "conversation_id": "fa8a78df-c77c-42d8-94d6-2677ff4ddcdf",
    "step_idx": 0,
    "model": "Gemini 3.8 Flash",
    "input_tokens": 319,
    "output_tokens": 1850,
    "total_tokens": 2169,
    "cost_usd": 0.001158,
    "estimation_method": "heuristic_3.8",
    "prompt_preview": "Refactor the authentication middleware to use JWT"
  }
]
```

---

## Example 2: FastMCP Integration with Cursor IDE

Cursor natively supports MCP servers. You can use the local AI dispatcher directly in Cursor Composer or Chat.

### 1. Configuration in Cursor
Add to your Cursor MCP settings (`~/.cursor/mcp.json` or through Cursor Settings > Features > MCP):

```json
{
  "mcpServers": {
    "local-dispatcher": {
      "command": "python",
      "args": ["C:/caminho/para/agent-token-auditor/server.py"]
    }
  }
}
```

### 2. Usage in Cursor Chat
In the Cursor Chat/Composer, invoke the tools:

> **User Prompt:**  
> `@local-dispatcher classify_task_complexity task_description="Generate TypeScript interfaces for a users table and validate syntax"`

**Cursor Response:**
```json
{
  "suggested_tier": "local",
  "recommended_model": "qwen/qwen2.5-coder-7b-instruct",
  "reason": "Routine or mechanical coding task ideal for fast offline execution with zero API cost.",
  "requires_user_confirmation": false
}
```

> **User Prompt:**  
> `@local-dispatcher generate_ts_dtos schema_or_sql="CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(100), email VARCHAR(255), active BOOLEAN);"`

The task is executed locally by your **Qwen 2.5 Coder** model in LM Studio/Ollama, generating strict TypeScript DTOs at **$0.00 cost**, and recording the tokens saved into `local_ai_audit.csv`.

---

## Example 3: Offloading Boilerplate & Tests in VS Code (Cline / Roo Code)

In VS Code, extensions like **Cline** or **Roo Code** allow you to connect MCP servers and delegate routine coding tasks to local LLMs to avoid burning cloud credits.

### 1. Configuration in Cline (`cline_mcp_settings.json`)
```json
{
  "mcpServers": {
    "local-ai": {
      "command": "python",
      "args": ["C:/Users/YourUser/agent-token-auditor/server.py"],
      "alwaysAllow": [
        "run_local_code_task",
        "generate_unit_tests",
        "generate_ts_dtos",
        "validate_code_syntax"
      ]
    }
  }
}
```

### 2. Practical Workflow in Cline
When you ask Cline:
> *"Create unit tests with Jest for this user repository function."*

Cline can execute the MCP tool `generate_unit_tests` against your local model. 
- Prompt tokens: ~1,200 tokens
- Completion tokens: ~1,800 tokens
- **Actual Cost:** **$0.00**
- **Savings vs Claude 3.5 Sonnet:** **~$0.0306 USD** (recorded in `local_ai_audit.csv`)

---

## Example 4: Claude Desktop Integration & Token Telemetry

You can use the FastMCP server in **Claude Desktop** to track and inspect token efficiency directly from Anthropic's native desktop application.

### 1. Configuration (`claude_desktop_config.json`)
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "token-auditor": {
      "command": "python",
      "args": ["/absolute/path/to/agent-token-auditor/server.py"]
    }
  }
}
```

### 2. Inspecting Token Telemetry in Claude Desktop
Ask Claude:
> *"What is our token usage and accumulated savings so far?"*

Claude calls `get_token_usage_report` and responds with a formatted breakdown:
```markdown
### Token & Cost Audit Summary
- **Total Requests Handled:** 48
- **Local AI Tasks (LM Studio):** 36 (100% Free / $0.00)
- **OpenRouter Free Tier:** 10 (100% Free / $0.00)
- **Paid / Smart Tier:** 2 ($0.0124 USD)
- **Tokens Processed Locally:** 142,390 tokens
- **Total Savings vs Claude 3.5 Sonnet:** $2.14 USD (~R$ 12.30)
```

---

## Example 5: Standalone CLI Analytics & Savings Reports

You can run CLI commands anytime in your terminal to inspect metrics or generate reports.

### 1. View Session Token Breakdown
```bash
python scripts/measure_tokens.py
```

**Output:**
```text
======================================================================
           AI TOKEN & COST AUDITOR SUMMARY
======================================================================

[1] ANTIGRAVITY CLOUD SESSIONS (tokens_audit.csv)
  • Total Turns Audited:    52
  • Input Tokens (Prompts): 21,450
  • Output Tokens:          184,320
  • Total Cloud Tokens:     205,770
  • Total Real Cost:        $0.1142 USD (~R$ 0.66)

[2] LOCAL AI / MCP OFFLOADED TASKS (local_ai_audit.csv)
  • Total Local Tasks:      38
  • Offline Prompt Tokens:  48,200
  • Offline Output Tokens:  62,100
  • Total Local Tokens:     110,300 (100% Free)
  • Savings vs Claude:      $1.0761 USD (~R$ 6.19)

[3] EQUIVALENT COST IF RUN 100% ON PROPRIETARY MODELS
  • Google Gemini 2.5/3.8 Flash                : $  0.1583 USD (~R$    0.91)
  • OpenAI GPT-4o                              : $  2.6384 USD (~R$   15.17)
  • Anthropic Claude 3.5 Sonnet                : $  3.9052 USD (~R$   22.45)
  • Anthropic Claude 3 Opus                    : $  6.5097 USD (~R$   37.43)
======================================================================
```

### 2. Generate Markdown Savings Report
```bash
python scripts/generate_savings_report.py
```
Outputs a formatted markdown file to `docs/reports/savings_report.md` ready to be committed, reviewed in PRs, or shared with stakeholders.

### 3. Re-sync Full History from Scratch
If you ever want to re-parse all previous chat transcripts:
```bash
python scripts/log_iteration_tokens.py --sync
```

---

## Example 6: Programmatic Python Usage in Custom Agents

You can import and use the auditor functions in your own Python projects (LangChain, AutoGen, CrewAI, LiteLLM or FastAPI backends).

### Example: Tracking Tokens in a Custom LLM Wrapper
```python
from agent_dispatcher.audit import record_token_usage
import time

def call_my_agent(prompt: str):
    start = time.time()
    
    # Example: call your model (OpenAI, Anthropic, Ollama, etc.)
    # response = client.chat.completions.create(...)
    
    # Dummy usage example:
    prompt_tokens = 350
    completion_tokens = 420
    elapsed_ms = (time.time() - start) * 1000

    # Record token usage into CSV & JSON automatically
    record_token_usage(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        duration_ms=elapsed_ms,
        tool_name="custom_agent_turn",
        provider="local",              # or "openrouter_smart", "cloud"
        model_used="qwen-2.5-coder-7b"
    )

    print("Turn successfully audited!")

if __name__ == "__main__":
    call_my_agent("Write a python script to validate emails")
```
Every call will be appended to `local_ai_audit.csv` with calculated savings and timestamps.

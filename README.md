# 📊 Antigravity Token Auditor & FastMCP Hybrid Local AI Dispatcher

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Protocol: MCP](https://img.shields.io/badge/protocol-FastMCP-green.svg)](https://modelcontextprotocol.io/)

A complete, lightweight toolkit to **track, audit and minimize token consumption and LLM costs** in Agentic IDEs (like **Google Antigravity**, **Cursor**, **VS Code**, **Windsurf**, and **Claude Desktop**).

---

## 🚀 O que este projeto faz? / What does it do?

1. **Auditoria de Mensagens em Tempo Real (Turn-by-Turn Auditor)**:
   - Intercepta cada interação do agente através de hooks de ciclo de vida (`Stop` e `PostInvocation`).
   - Analisa o transcript da conversa (prompts do usuário, respostas do modelo, raciocínio `thinking`, chamadas de ferramentas).
   - Rastreia trocas dinâmicas de modelo (Gemini Flash, Claude Sonnet/Opus, GPT-4o, DeepSeek-R1).
   - Calcula tokens de entrada, tokens de saída e custo estimado em USD/moeda local.
   - Salva automaticamente em `tokens_audit.csv` e `tokens_audit.json`.

2. **Despachante FastMCP Híbrido com IA Local (Zero-Cost Offloading)**:
   - Servidor FastMCP que delega tarefas mecânicas (geração de DTOs, testes unitários, validação de sintaxe, boilerplate) para uma LLM local offline (ex: Qwen 2.5 Coder 7B via LM Studio ou Ollama) com **R$ 0,00 de custo**.
   - Roteamento híbrido inteligente: fallback automático para OpenRouter (free tier ou modelos avançados como DeepSeek-R1) caso a IA local esteja offline ou a tarefa exija raciocínio profundo.
   - Mede e compara a economia exata de tokens e dólares contra modelos como Claude 3.5 Sonnet e GPT-4o.

---

## ❓ Perguntas Frequentes / FAQ

### 1. Ele funciona em qualquer IDE?
- **O Despachante FastMCP (`server.py`)**: **SIM! Funciona em QUALQUER IDE ou cliente compatível com o protocolo MCP (Model Context Protocol)**:
  - **Google Antigravity**
  - **Cursor**
  - **VS Code** (com extensões Cline, Roo Code, GitHub Copilot Agent)
  - **Windsurf**
  - **Zed**
  - **Claude Desktop**
- **O Hook de Auditoria Automática Turn-by-Turn (`hooks.json`)**:
  - O gatilho automático via hook é nativo do **Google Antigravity IDE** (que dispara scripts nos eventos de ciclo de vida do agente).
  - No entanto, o script auditor (`scripts/log_iteration_tokens.py`) também funciona via **linha de comando manual** (`--sync`), podendo ler transcripts de conversas ou ser chamado por hooks equivalentes de outros agentes (ex: Claude Code CLI, Aider, scripts de CI).

### 2. Quais são os pré-requisitos para usar?
- **Python 3.10 ou superior** (recomendado Python 3.12).
- Dependências Python: `pip install -r requirements.txt` (`mcp`, `httpx`, `python-dotenv`).
- **Para IA Local (opcional, para custo zero)**:
  - Qualquer servidor de inferência compatível com a API da OpenAI rodando localmente na porta 1234 ou 11434 (ex: [LM Studio](https://lmstudio.ai/) ou [Ollama](https://ollama.com/)).
  - Modelo recomendado: `Qwen 2.5 Coder 7B Instruct` ou `14B`.
- **Para fallback em nuvem (opcional)**:
  - Uma chave gratuita do [OpenRouter](https://openrouter.ai/) em `OPENROUTER_API_KEY`.

---

## 📁 Estrutura do Projeto / Project Structure

```text
antigravity-token-auditor/
├── .agents/
│   ├── hooks.json              # Configuração de hooks do Antigravity
│   ├── run_auditor.cmd         # Script de execução para Windows
│   └── run_auditor.sh          # Script de execução para Linux / macOS
├── agent_dispatcher/           # Pacote Python do Servidor FastMCP
│   ├── __init__.py
│   ├── __main__.py
│   ├── config.py               # Catálogo de modelos, preços e configurações
│   ├── router.py               # Roteamento inteligente (Local vs OpenRouter)
│   ├── audit.py                # Gravação de métricas, cache e teto de gastos
│   └── tools.py                # Ferramentas expostas via FastMCP (@mcp.tool)
├── scripts/
│   ├── log_iteration_tokens.py # Auditor de transcript disparado pelo hook
│   ├── measure_tokens.py       # CLI para visualizar consumo e custos de sessões
│   └── generate_savings_report.py # Gerador de relatório de economia em Markdown
├── .env.example                # Variáveis de ambiente de exemplo
├── .gitignore                  # Ignora dados sensíveis e CSVs com prompts
├── requirements.txt            # Dependências Python
├── server.py                   # Ponto de entrada do servidor FastMCP
├── LICENSE                     # Licença MIT
└── README.md
```

---

## 🛠️ Como Instalar e Usar / Quickstart

### Passo 1: Clonar o repositório e instalar dependências

```bash
git clone https://github.com/delmo85/antigravity-token-auditor.git
cd antigravity-token-auditor

# Criar ambiente virtual (opcional)
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Instalar bibliotecas
pip install -r requirements.txt

# Configurar variáveis de ambiente
cp .env.example .env
```

---

### Passo 2: Configurar a Auditoria no Google Antigravity

Se você utiliza o **Google Antigravity**:

1. Copie a pasta `.agents/` e a pasta `scripts/` para a raiz do seu projeto que você abre no Antigravity.
2. Certifique-se de que o arquivo `.agents/hooks.json` contém:
```json
{
  "token-auditor": {
    "enabled": true,
    "Stop": [
      {
        "type": "command",
        "command": "run_auditor.cmd",
        "timeout": 15
      }
    ],
    "PostInvocation": [
      {
        "type": "command",
        "command": "run_auditor.cmd",
        "timeout": 15
      }
    ]
  }
}
```
*(No Linux ou macOS, substitua `run_auditor.cmd` por `run_auditor.sh`).*

3. **Pronto!** A cada mensagem ou turno do agente, o hook será disparado automaticamente e criará os arquivos:
   - `tokens_audit.csv`: Planilha tabular com data, modelo, tokens in/out, custo estimado e resumo do prompt.
   - `tokens_audit.json`: Histórico estruturado em JSON para dashboards.

---

### Passo 3: Configurar o Servidor FastMCP nas suas IDEs

O FastMCP expõe ferramentas de codificação local e relatórios de tokens.

#### No Google Antigravity
Adicione ao arquivo `.antigravity/mcp.json` ou configure nas ferramentas do Antigravity:
```json
{
  "mcpServers": {
    "local-ai-dispatcher": {
      "command": "python",
      "args": ["/caminho/absoluto/antigravity-token-auditor/server.py"]
    }
  }
}
```

#### No Cursor (`~/.cursor/mcp.json` ou Configurações do Cursor)
```json
{
  "mcpServers": {
    "local-ai-dispatcher": {
      "command": "python",
      "args": ["/caminho/absoluto/antigravity-token-auditor/server.py"]
    }
  }
}
```

#### No VS Code (com extensão Cline ou Roo Code)
Adicione em `cline_mcp_settings.json`:
```json
{
  "mcpServers": {
    "local-ai-dispatcher": {
      "command": "python",
      "args": ["/caminho/absoluto/antigravity-token-auditor/server.py"]
    }
  }
}
```

#### No Claude Desktop (`claude_desktop_config.json`)
```json
{
  "mcpServers": {
    "local-ai-dispatcher": {
      "command": "python",
      "args": ["/caminho/absoluto/antigravity-token-auditor/server.py"]
    }
  }
}
```

---

## 💻 Ferramentas CLI Disponíveis

### 1. Medir consumo e custos da sessão atual
```bash
python scripts/measure_tokens.py
```
*Exibe um resumo detalhado no terminal com total de tokens gastos em nuvem, tarefas executadas na IA local e a comparação de custo contra Claude Sonnet / GPT-4o.*

### 2. Gerar relatório de economia em Markdown
```bash
python scripts/generate_savings_report.py
```
*Gera o arquivo `docs/reports/savings_report.md` com tabelas consolidadas de ROI e economia financeira.*

### 3. Sincronizar histórico manualmente
```bash
python scripts/log_iteration_tokens.py --sync
```
*Lê todo o histórico do transcript atual e regenera o `tokens_audit.csv`.*

---

## 🔒 Privacidade e Segurança

- Os arquivos `tokens_audit.csv`, `tokens_audit.json` e `.env` estão devidamente incluídos no `.gitignore`.
- Prompts de conversas nunca são compartilhados ou enviados a servidores de terceiros além das APIs oficiais configuradas pelo usuário.

---

## 📄 Licença

Distribuído sob a licença **MIT**. Veja [LICENSE](LICENSE) para mais informações.

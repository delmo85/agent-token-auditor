# 📊 Universal AI Agent Token Auditor & Local LLM FastMCP Dispatcher

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Protocol: MCP](https://img.shields.io/badge/protocol-FastMCP-green.svg)](https://modelcontextprotocol.io/)

A universal, lightweight toolkit to **track, audit, and minimize token consumption and LLM costs** across agentic coding IDEs (**Cursor**, **VS Code**, **Google Antigravity**, **Windsurf**, and **Claude Desktop**) and custom Python agents.

---

## 🌟 Principais Recursos / Key Features

1. **Auditoria de Mensagens em Tempo Real (Turn-by-Turn Token Tracking)**:
   - Mede tokens de entrada (prompts), tokens de saída, raciocínio (`thinking`) e chamadas de ferramentas.
   - Detecta trocas dinâmicas de modelo durante as conversas (Gemini Flash, Claude Sonnet/Opus, GPT-4o, DeepSeek-R1).
   - Calcula custos reais em USD e moeda local com base em tabelas de preços transparentes.
   - Registra dados estruturados em `tokens_audit.csv` e `tokens_audit.json`.

2. **Despachante FastMCP Híbrido com IA Local (Zero-Cost Local AI Offloading)**:
   - Servidor FastMCP padrão que delega tarefas rotineiras de código (DTOs, testes unitários, validação de sintaxe, boilerplate) para uma LLM local offline (ex: **Qwen 2.5 Coder 7B** no LM Studio ou Ollama) com **custo zero ($0.00)**.
   - Roteamento híbrido inteligente com fallback automático para OpenRouter (free tier ou modelos avançados).
   - Compara a economia real gerada contra modelos pagos (Claude 3.5 Sonnet, GPT-4o).

3. **Compatibilidade Ampla (Universal Compatibility)**:
   - Funciona via protocolo aberto FastMCP em **qualquer IDE ou cliente compatível com MCP**.
   - Inclui automação por hooks nativos para o **Google Antigravity**, suporte a **Cursor**, **VS Code** (Cline / Roo Code), **Claude Desktop**, e modo **CLI / Scripts Python**.

---

## 📖 Exemplos Práticos / Practical Examples

Consulte o arquivo dedicado com exemplos passo a passo para cada ambiente:
👉 **[Ver Guia Completo de Exemplos (EXAMPLES.md)](EXAMPLES.md)**

- **Exemplo 1:** Auditoria automática por turno no Google Antigravity
- **Exemplo 2:** Uso do servidor FastMCP no Cursor IDE
- **Exemplo 3:** Delegação de testes e código no VS Code (Cline / Roo Code)
- **Exemplo 4:** Telemetria de tokens no Claude Desktop
- **Exemplo 5:** Relatórios e métricas via CLI no terminal
- **Exemplo 6:** Integração programática em agentes Python (LangChain, CrewAI, LiteLLM)

---

## ❓ Perguntas Frequentes / FAQ

### Ele funciona em qualquer IDE?
- **O Servidor FastMCP (`server.py`)**: **SIM! Funciona em qualquer IDE ou cliente compatível com o protocolo MCP**:
  - **Cursor**
  - **VS Code** (via extensões Cline, Roo Code, Copilot Agent)
  - **Google Antigravity**
  - **Windsurf**
  - **Zed**
  - **Claude Desktop**
- **O Hook Automático por Turno (`hooks.json`)**:
  - A execução transparente a cada mensagem é suportada nativamente no **Google Antigravity IDE** através de lifecycle hooks.
  - Para outros ambientes, o script `scripts/log_iteration_tokens.py` pode ser executado via CLI (`--sync`), integrado a webhooks ou chamado dentro do seu loop de agente em Python.

### Quais são os pré-requisitos?
- **Python 3.10 ou superior** (recomendado Python 3.12).
- Dependências: `pip install -r requirements.txt` (`mcp`, `httpx`, `python-dotenv`).
- **Para IA Local (opcional, para custo zero)**:
  - [LM Studio](https://lmstudio.ai/) ou [Ollama](https://ollama.com/) rodando localmente na porta `1234` ou `11434` (modelo sugerido: `Qwen 2.5 Coder 7B Instruct` ou `14B`).
- **Para fallback em nuvem (opcional)**:
  - Chave de API da [OpenRouter](https://openrouter.ai/) em `OPENROUTER_API_KEY`.

---

## 📁 Estrutura do Projeto / Project Structure

```text
agent-token-auditor/
├── .agents/
│   ├── hooks.json              # Configuração de hooks do Antigravity
│   ├── run_auditor.cmd         # Script de execução para Windows
│   └── run_auditor.sh          # Script de execução para Linux / macOS
├── agent_dispatcher/           # Pacote Python do Servidor FastMCP
│   ├── __init__.py
│   ├── __main__.py
│   ├── config.py               # Catálogo de modelos, preços e configurações
│   ├── router.py               # Roteador híbrido (Local vs OpenRouter)
│   ├── audit.py                # Gravação de métricas, cache e teto de gastos
│   └── tools.py                # Ferramentas expostas via FastMCP (@mcp.tool)
├── scripts/
│   ├── log_iteration_tokens.py # Auditor de transcripts disparado por hook ou CLI
│   ├── measure_tokens.py       # CLI para visualizar consumo e custos de sessões
│   └── generate_savings_report.py # Gerador de relatório de economia em Markdown
├── .env.example                # Variáveis de ambiente de exemplo
├── .gitignore                  # Ignora dados sensíveis e CSVs com prompts
├── requirements.txt            # Dependências Python
├── server.py                   # Ponto de entrada do servidor FastMCP
├── EXAMPLES.md                 # Exemplos detalhados de uso em várias IDEs
├── LICENSE                     # Licença MIT
└── README.md
```

---

## 🛠️ Como Instalar e Usar / Quickstart

### Passo 1: Clonar o repositório e instalar dependências

```bash
git clone https://github.com/delmo85/agent-token-auditor.git
cd agent-token-auditor

# Criar ambiente virtual (opcional)
python -m venv .venv

# Ativar ambiente virtual:
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente
cp .env.example .env
```

---

### Passo 2: Configurar o Servidor FastMCP nas suas IDEs

O FastMCP expõe ferramentas de codificação local e relatórios de tokens.

#### No Cursor (`~/.cursor/mcp.json`)
```json
{
  "mcpServers": {
    "local-dispatcher": {
      "command": "python",
      "args": ["/caminho/absoluto/agent-token-auditor/server.py"]
    }
  }
}
```

#### No VS Code (Cline ou Roo Code)
Adicione em `cline_mcp_settings.json`:
```json
{
  "mcpServers": {
    "local-dispatcher": {
      "command": "python",
      "args": ["/caminho/absoluto/agent-token-auditor/server.py"]
    }
  }
}
```

#### No Claude Desktop (`claude_desktop_config.json`)
```json
{
  "mcpServers": {
    "local-dispatcher": {
      "command": "python",
      "args": ["/caminho/absoluto/agent-token-auditor/server.py"]
    }
  }
}
```

#### No Google Antigravity
Copie as pastas `.agents/` e `scripts/` para o seu projeto e configure o MCP em `.antigravity/mcp.json`.

---

## 💻 Comandos CLI Disponíveis

### 1. Medir consumo e custos da sessão atual
```bash
python scripts/measure_tokens.py
```
*Exibe um resumo detalhado no terminal com total de tokens gastos em nuvem, tarefas executadas na IA local e a comparação de custo contra Claude Sonnet e GPT-4o.*

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

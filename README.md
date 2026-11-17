# FedAura — local agent development

Run a small agent loop, a loan assistant and external MCP tools using local
Ollama inference. All application data is synthetic.

Requires Podman, Ollama, uv, Node.js and npm. This setup was verified on macOS
with Apple Silicon. Run all commands from the repository root.

## Setup

```bash
podman machine start                 # If your existing Podman machine is stopped.
ollama serve                         # In a separate terminal, if Ollama is not running.
bash fedaura/demo.sh setup           # Install dependencies, create .env and download qwen3.5:9b.
bash fedaura/demo.sh up assistant    # Start database, storage, API and UI without external MCP.
bash fedaura/demo.sh check           # Verify local services and synthetic data.
```

Open the application at **http://127.0.0.1:3100**. API documentation:
**http://127.0.0.1:8100/docs**.

## Model and basic agent

```bash
ollama run qwen3.5:9b                            # Chat directly with the model; /bye exits.
fedaura/.venv/bin/python fedaura/scripts/intro.py # Run the small catalog tool-calling loop.
```

In the Ollama chat, try:

```text
Explain what a mortgage is in two sentences.
```

The Python script submits its catalog question automatically; no prompt entry is
needed.

## Application tools

Use the public chat in the browser, or run these predefined prompts through the
application's chat endpoint:

```bash
bash fedaura/demo.sh chat products       # Retrieve the FedAura product catalog.
bash fedaura/demo.sh chat affordability  # Calculate affordability for a synthetic borrower.
```

Example prompts for the public browser chat:

**Product catalog**

```text
What mortgage products does Fedaura offer? Look up the product catalog and summarize three options briefly.
```

**Affordability calculator**

```text
Use the affordability calculator for this synthetic example: gross annual income $102,000, monthly debt payments $2,400, down payment $80,000, interest rate 6.5%, and a 30-year loan. Give the estimated maximum loan, purchase price and monthly payment. Keep it brief.
```

Watch tool execution in another terminal:

```bash
tail -f fedaura/runtime/api.log | rg --line-buffered 'FEDAURA tool_(start|end)'
```

Look for matching `tool_start` and `tool_end` entries. The affordability
calculator runs inside the application; it is not an MCP tool.

## External MCP tools

```bash
bash fedaura/demo.sh stage mcp  # Start the risk MCP server and restart the API with its tools.
bash fedaura/demo.sh mcp        # Inspect MCP tool discovery and schemas.
bash fedaura/demo.sh chat risk  # Run a synthetic risk assessment using external tools.
```

MCP code to explore:

| File | What it shows |
|---|---|
| [mcp_server.py](fedaura/app/packages/api/src/mcp_server.py#L65) | `@mcp.tool()` exposes a risk calculation as an MCP tool. |
| [mcp_integration.py](fedaura/app/packages/api/src/agents/mcp_integration.py#L19) | `MultiServerMCPClient` connects over `streamable_http`; `get_tools()` discovers the server's tools. |
| [underwriter_assistant.py](fedaura/app/packages/api/src/agents/underwriter_assistant.py#L27) | `get_mcp_tools()` makes the discovered tools available to the underwriter agent. |

Refresh the browser after switching stages. For browser-based risk assessment,
select the development underwriter persona. Successful MCP tool executions are
recorded in `fedaura/runtime/mcp-calls.jsonl`.

Example prompt for the underwriter chat after enabling MCP:

```text
For a standalone synthetic example, use your external risk tools to calculate DTI and LTV and evaluate credit risk: monthly income $8,500, monthly debts $2,400, loan amount $320,000, property value $400,000, and self-reported credit score 742. Give the three values and their risk ratings. Do not make a lending decision or look up an application.
```

## Status, logs and shutdown

```bash
bash fedaura/demo.sh status     # Show running services.
bash fedaura/demo.sh logs api   # Follow API logs; Ctrl+C stops watching.
bash fedaura/demo.sh logs mcp   # Follow MCP server logs.
bash fedaura/demo.sh test       # Run local checks and calculator tests.
bash fedaura/demo.sh down       # Stop local services and retain synthetic data.
```


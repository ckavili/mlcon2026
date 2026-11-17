# Fedaura — progressive local loan-agent demo

A self-contained local copy of your loan-origination application for the
MLcon presentation. Your original repository and cluster setup are unchanged.

**Presenter script:** [DEMO-SCRIPT.md](DEMO-SCRIPT.md)  
**What was tested:** [VERIFICATION.md](VERIFICATION.md)  
**Source and modifications:** [SOURCE.md](SOURCE.md)

## Quick start on this laptop

From the parent `localagents` directory:

```bash
bash fedaura/demo.sh up assistant
```

Open **http://127.0.0.1:3100**. The services are already installed in this copy.

To add the external MCP tools during the presentation:

```bash
bash fedaura/demo.sh stage mcp
bash fedaura/demo.sh mcp
```

To stop only this local stack, retaining synthetic data:

```bash
bash fedaura/demo.sh down
```

## The progression

| Scene | What you show | New concept |
|---|---|---|
| 0 | Small Python agent loop, same product catalog | Model + tool + loop |
| 1 | Public assistant in the existing UI | LangGraph and application integration |
| 2 | Affordability calculator | Deterministic business calculations |
| 3 | Enable MCP, inspect discovery/schema, ask underwriter | External tools over a protocol |
| 4 | Optional seeded queue | Tools retrieving application data; rehearse separately |
| 5 | Switch browser to your existing cluster app | MaaS, MLflow and enterprise platform features |

No code needs to be edited live. `assistant` and `mcp` are real startup modes:
the first does not connect to or start the external risk service; the second
starts it and reloads the API so MCP discovery and agent graphs are rebuilt.
The pages/personas are not hidden between stages. These modes control the demo
composition; they are not authorization boundaries.

## Architecture

```text
Browser :3100
   │ HTTP + WebSocket, proxied by Vite
   ▼
FastAPI + LangGraph :8100 ──────────► native Ollama :11434 / Qwen3.5 9B
   │
   ├── PostgreSQL + pgvector :55433    [Podman]
   ├── S4 object storage :19090        [Podman, AMD64 emulation on Apple Silicon]
   └── MCP risk server :8181           [only in mcp stage]
          └── six deterministic calculators / risk functions
```

The UI, API, and MCP service run natively. PostgreSQL and S4 run in Podman.
This preserves native Apple GPU inference and avoids building the full backend
container for the laptop demonstration. It does not claim that the entire
application stack has been containerized locally.

## Commands

Run from the parent directory unless you adjust the path:

```bash
bash fedaura/demo.sh setup          # First installation on another machine
bash fedaura/demo.sh up assistant   # Native public assistant, no risk MCP
bash fedaura/demo.sh stage mcp      # Add MCP service and rebuild agent graphs
bash fedaura/demo.sh status
bash fedaura/demo.sh check          # Infrastructure + real protocol checks; no LLM
bash fedaura/demo.sh intro          # Minimal agent loop using local product catalog
bash fedaura/demo.sh mcp            # List MCP tools, show schema, invoke DTI directly
bash fedaura/demo.sh chat products
bash fedaura/demo.sh chat affordability
bash fedaura/demo.sh chat risk      # Requires mcp stage
bash fedaura/demo.sh chat queue     # Optional seeded queue
bash fedaura/demo.sh test           # Existing calculator unit tests
bash fedaura/demo.sh logs api       # Follow API tool-call activity; Ctrl-C exits tail
bash fedaura/demo.sh logs mcp
bash fedaura/demo.sh down
```

`chat` rehearsals use the same WebSocket endpoints as the UI. Each gets a fresh
synthetic identity, avoiding remembered tool results from previous rehearsals.
They record events and check that the required tools were actually called.
They do not automatically prove that every sentence in the answer is correct.

In the UI, use **Clear chat history** before repeating an authenticated scene.
Otherwise, an agent may answer from a previous tool result rather than call it
again. That is conversation persistence, not proof of a new tool execution.

## Installation elsewhere

Requires macOS/Linux, Node.js 22+, npm, uv, Podman with a running machine, and
Ollama supporting Qwen3.5. Python 3.13 is provisioned by uv. This copy has been
tested on Apple Silicon; S4 uses the source application's AMD64 image.

```bash
bash fedaura/demo.sh setup
bash fedaura/demo.sh up assistant
```

Setup installs dependencies only inside `.venv`, `.tools`, and `app/node_modules`,
apart from standard package-manager caches and Ollama's model cache. It pulls
the approximately 7.6 GB model if needed. Podman images and named data volumes
live in the Podman machine. Installation and image/model downloads need internet.
Air-gapped execution has not been verified.

Use the supplied scripts rather than the copied application's workspace
`setup`/`dev` commands. Those upstream commands target its complete development
environment. The copied `uv.lock` files are upstream references; this demo uses
the top-level `requirements.lock` for its reduced Python environment.

## Ports and data

| Service | Address |
|---|---|
| UI | http://127.0.0.1:3100 |
| API / docs | http://127.0.0.1:8100/docs |
| MCP risk service | http://127.0.0.1:8181/mcp |
| MCP health | http://127.0.0.1:8181/health |
| PostgreSQL | 127.0.0.1:55433 |
| S4 S3 endpoint | http://127.0.0.1:19090 |
| S4 console | http://127.0.0.1:19091 |

The local demo uses dedicated ports. Data is isolated in the
`fedaura-local` Compose project. `down` stops services without deleting volumes.
The launcher only stops native processes recorded in its own PID files, checking
process creation time to avoid acting on a reused PID.

The fixtures use `FEDAURA_DEMO_DATE=2026-11-15` to keep relative timestamps and
fixture hashes stable across stage changes. Changing fixture content/date can
trigger the upstream auto-reseed logic and replace this copy's synthetic data.
Pick application IDs from the current queue; don't hardcode old rehearsal IDs.

## Local scope

Included: existing UI, product catalog, calculator, seeded database, persistent
conversations, role-specific assistant selection, MCP discovery and risk tools.

Intentionally omitted from the local installation: Keycloak, MLflow, cluster
pipelines, compliance embeddings/KB ingestion, predictive model integration,
and a separate vision workflow. The local underwriter has a reduced tool list
and cannot issue loan decisions through its agent tools.

Authentication is bypassed for the synthetic local demo. The sign-in page's
persona cards select development users; this is not an enterprise identity demo.
Switch to your existing cluster setup for real authentication, MaaS, MLflow and
evaluation scenes. No cluster resources or credentials are modified here.

## Configuration and evidence

`.env` is local and Git-ignored. `.env.example` contains only local demo values.
The launcher explicitly requires a loopback model endpoint. It does not route
the local scenario to a cloud API as a fallback.

Evidence is written under Git-ignored `runtime/`:

* `api.log`, `mcp.log`, `ui.log`: service logs.
* `mcp-calls.jsonl`: actual completed external tool calls (names/times, no inputs).
* `chat-*.json`: actual rehearsal events, tool inputs/results and final answers.
* `stage`: selected local mode.

The API forwards tool-start/result events to the existing UI's tool badges.
Open a chat after changing stages, and refresh the page if its WebSocket was
disconnected during the API restart.

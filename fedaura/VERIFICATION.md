# Local verification — 15 November 2026

## Environment

* Apple M1 Pro laptop, 32 GB memory.
* Native Ollama 0.40.16, `qwen3.5:9b`, Apple GPU/MLX inference.
* Isolated Python 3.13.4 environment, dependencies recorded in `requirements.lock`.
* Node.js 24.2.0 and project-local pnpm 9.15.9.
* PostgreSQL/pgvector and S4 in the isolated `fedaura-local` Podman project.
* Source repository left unchanged; no cluster resources or credentials used.

## Passed checks

| Check | Observed result |
|---|---|
| Packaged setup command rerun | Dependencies already satisfied; locked UI installation passed; model available |
| Assistant startup | UI and API reachable; MCP intentionally disabled |
| Database migrations and seed | 38 applications: 10 active, 28 historical; 10 borrowers |
| S3-compatible storage | Documents bucket exists and responds to a real HEAD request |
| MCP stage startup | Separate service started; API discovered six tools |
| MCP protocol | Real HTTP initialization, discovery and calculator invocation |
| Minimal agent loop | Requested `product_info`, read local catalog, produced an answer |
| Product agent | Actual `product_info` call and catalog-based response |
| Affordability agent | Actual `affordability_calc` call; numerical result matched expected values |
| Underwriter agent | Actual external DTI, LTV and credit tool calls; values and ratings matched |
| Narrow optional queue prompt | Actual queue tool call, count/IDs/names returned |
| UI WebSocket proxy | Product chat completed through port 3100, with tool events and final response |
| UI production build | Vite build passed |
| UI type check | `tsc --noEmit` passed |
| Existing MCP calculator suite | 31 tests passed |
| Return to opening stage | MCP stopped; API restarted; UI remained reachable |
| Seed stability across final stage switch | Existing fixture hash recognized; no re-seed |
| Shell / whitespace checks | Passed |
| Git exclusions | `.env`, runtime artifacts, Python and Node environments excluded |

## Observed rehearsal outputs

See [recorded rehearsals](examples/REHEARSALS.md) for actual saved responses.
The machine-readable runtime evidence is in `runtime/chat-*.json`.

| Scene | Observed duration | Main evidence |
|---|---:|---|
| Products through UI proxy | 6.9 seconds | `product_info` observed |
| Affordability | 11.1 seconds | $198,554.58 loan, $278,554.58 price, $1,255 payment |
| External risk factors | 8.0 seconds | DTI 28.2% Low; LTV 80% Medium; credit 742 Low |
| Narrow queue question | 4.1 seconds | Queue tool observed; three applications listed |

These are individual warm-model observations, not latency guarantees or a
statistical reliability measurement. Initial/cold runs were slower.

## Findings that changed the local package

* An inherited shell `DEBUG=release` prevented startup. The local environment
  now explicitly supplies `DEBUG=false`.
* Model config loading eagerly imported the embedding model package. The copy
  now uses a lazy import and skips knowledge-base ingestion during seeding.
* The original fixture timestamps changed on every process import, changing
  hashes and triggering re-seeds. The local copy uses a stable explicit date.
* The first affordability rehearsal skipped the calculator and invented values.
  The local public prompt was shortened and retested; the final observed result
  used the calculator and returned its correct values.
* Repeating an authenticated risk question reused earlier conversation evidence
  without new tool calls. Rehearsal scripts now use fresh synthetic identities;
  the UI script calls for clearing chat history before repeating the scene.
* A broad queue summary introduced an incorrect credit-risk label. The optional
  queue prompt is now restricted to count, IDs and names, and the main script
  avoids asking for that broad interpretation.
* The API previously did not forward tool events to UI badges. The local copy
  now sends the events expected by the existing UI components.

## Practical limits

Visual browser QA was not available: the in-app browser connection returned
unavailable. HTTP serving, frontend compilation/types and real WebSocket paths
were checked, but the complete visual click-through still needs your rehearsal.

The copied app's complete API/UI suites were not run. The selected calculator
suite, protocol checks and live scenarios cover the local demonstration scope.
Some SDK deprecation warnings occur. The MCP SDK also logged an SSE connection
closure error while cleaning up a session; tested discovery and calls still
completed. Use the concise `mcp-calls.jsonl` execution record for presentation.

Agent tool-call checks establish actual invocation; they do not automatically
validate every sentence of generated prose. Keep the known numerical answers
available and distinguish demo risk ratings from a complete lending decision.

Local authentication is bypassed, and the underwriter tool set and prompts are
reduced. Compliance retrieval, document uploads/extraction, predictive models,
identity-provider enforcement, MLflow and cluster operation were not validated
here. Use the existing deployed application for the platform portion.

All financial data is synthetic. No real borrower or cluster data was imported.
The local inference configuration has no hosted fallback. External network
isolation was not tested, and dependency/image/model downloads need internet.

## Current ready state

The package was left running in **assistant** mode:

* UI: http://127.0.0.1:3100
* API: http://127.0.0.1:8100
* External MCP service: intentionally stopped until `stage mcp`.

Re-running `up assistant` recreates the managed processes as needed, preserving
this copy's synthetic volumes. Run `down` to stop them when finished.

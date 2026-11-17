# MLcon presenter script — Fedaura, laptop to platform

Use one fictional lending application throughout the talk. The local section
shows the agent mechanism, application orchestration and external tools. Then
switch to your existing cluster deployment for MaaS, MLflow and evaluations.

**Local target:** 12–15 minutes. Keep at least 15 minutes for your platform
section and time for questions. Install, download and rehearse before presenting.

## Quick command card

All commands below run from the parent `localagents` directory.

```bash
# Before the talk
bash fedaura/demo.sh up assistant
bash fedaura/demo.sh check

# On stage
bash fedaura/demo.sh intro
# Open http://127.0.0.1:3100 and use the public chat.
bash fedaura/demo.sh stage mcp
bash fedaura/demo.sh mcp
# Sign in as the development underwriter and use its chat.

# If the browser is inconvenient, these use the actual application endpoints:
bash fedaura/demo.sh chat products
bash fedaura/demo.sh chat affordability
bash fedaura/demo.sh chat risk

# After the session
bash fedaura/demo.sh down
```

`stage mcp` restarts the API. Refresh the UI and reconnect the chat afterward.
The frontend remains on the same port. Database and conversations persist.

## Preparation checklist

1. Run the two preflight commands above. Confirm 38 seeded applications.
2. Confirm `ollama list` includes `qwen3.5:9b`.
3. Open http://127.0.0.1:3100 in a fresh browser session, or sign out of any
   saved persona so the public assistant is shown first.
4. Keep your existing cluster application and MLflow pages open in separate,
   clearly labeled tabs. Authenticate to them before presenting.
5. Open `fedaura/scripts/intro.py`, `fedaura/app/packages/api/src/agents/base.py`,
   `fedaura/app/packages/api/src/mcp_server.py`, and
   `fedaura/app/packages/api/src/agents/mcp_integration.py` in your editor.
6. Keep this script and the four prompt files available for copying.
7. Rehearse the actual browser interaction. Browser visual QA was unavailable
   during setup; API, WebSocket, build and type checks were performed.

Use separate terminals for commands and optional logs. For a readable tool
execution record, show:

```bash
tail -f fedaura/runtime/mcp-calls.jsonl
```

Start that after the first MCP tool call has created the file. Unlike verbose
SDK logs, this file lists only successful tool names and timestamps.

## Scene 0 — make the loop visible (2 minutes)

**Say**

> Let's begin with the mechanism. An agent needs a model, tools, and a loop.
> The model requests an action; application code executes it and sends the
> result back. This is the minimal pattern many of us started with.

**Do**

```bash
bash fedaura/demo.sh intro
```

The question is “What mortgage products does Fedaura offer?” The tool retrieves
the same local fictional catalog used by the application.

**Look for**

```text
[step 1] tool: product_info
ANSWER: ...
```

**Show** `fedaura/scripts/intro.py` and point to:

* The model request with a tool schema.
* The application executing `product_info`.
* The result being appended as a tool message.
* The bounded loop.

**Say**

> There is no agent framework in this small script. The local model cannot
> know our private product catalog without the tool. Notice that inference
> and the tool are separate responsibilities.

Don't explain every line. This introductory tool uses a normal local REST
endpoint; it is not MCP. That distinction makes the later MCP scene clearer.

## Scene 1 — put the agent in an application (2–3 minutes)

**Say**

> A real application also needs a user experience, conversation state, tool
> execution and application data. We can reuse an orchestration framework
> rather than grow this little loop indefinitely. This application uses LangGraph.

**Do**

Open **http://127.0.0.1:3100**. Use the public chat button. The existing
“Explore Products” button also opens chat and submits a catalog question.
For the rehearsed wording, paste `fedaura/prompts/products.txt`:

```text
What mortgage products does Fedaura offer? Look up the product catalog and summarize three options briefly.
```

**Look for**

The final chat message includes the existing UI's `Used: product_info` badge.
It should describe the fictional catalog. Expected example values:

| Product | Typical demo rate | Minimum down payment |
|---|---:|---:|
| 30-Year Fixed Conventional | 6.5% | 3% |
| 15-Year Fixed Conventional | 5.75% | 3% |
| FHA | 6.25% | 3.5% |

These are synthetic catalog values, not live market quotes.

**Show briefly** `app/packages/api/src/agents/base.py`:

```text
input → agent → tools → agent → output
```

**Say**

> It's the same basic mechanism, inside an application. LangGraph manages the
> graph; the backend integrates conversation persistence and role-specific tools.
> The product lookup is still an in-process application tool. We haven't
> introduced an MCP service yet.

For this local stage, optional safety shields are unconfigured; don't imply
they are enforcing policy just because the graph contains shield nodes.

## Scene 2 — let application code own the math (2 minutes)

**Do**

First, open a second terminal at the project root and watch tool execution:

```bash
tail -f fedaura/runtime/api.log |
  rg --line-buffered 'FEDAURA tool_(start|end)'
```

Leave this running while you submit the prompt. To see the full API log instead,
use `bash fedaura/demo.sh logs api`. Ctrl+C stops watching; the app keeps running.

In the public chat, paste `fedaura/prompts/affordability.txt`:

```text
Use the affordability calculator for this synthetic example: gross annual income $102,000, monthly debt payments $2,400, down payment $80,000, interest rate 6.5%, and a 30-year loan. Give the estimated maximum loan, purchase price and monthly payment. Keep it brief.
```

**Verify the tool call in the second terminal.** Expect lines shaped like:

```text
FEDAURA tool_start session=… tool=affordability_calc
FEDAURA tool_end session=… tool=affordability_calc
```

`tool_start` records the requested execution; `tool_end` records completion.
Check that both belong to the same session and appeared after your new prompt.
The UI may also show `Used: affordability_calc`; use the logs to verify execution
if the chat only displays the final answer. The answer alone is not proof of a
calculator call.

To review recent calculator calls afterward:

```bash
rg 'FEDAURA tool_(start|end).*tool=affordability_calc' fedaura/runtime/api.log | tail -10
```

**Look for these results in the answer:**

| Output | Expected value |
|---|---:|
| Maximum loan | $198,554.58 |
| Estimated purchase price | $278,554.58 |
| Estimated monthly payment | $1,255.00 |
| Total DTI | 43.0% |

**Say**

> The model selects the calculator and supplies its arguments. Our application
> owns the formula. We can test that formula independently of the model.
> A plausible-looking number without a tool call would fail this demonstration.
> These log lines show the tool starting and completing; the final text is the
> model summarizing its result.

**Keep the boundary clear:** `affordability_calc` is a Python tool inside the
application, not an MCP call. Its execution appears in `fedaura/runtime/api.log`,
not `fedaura/runtime/mcp-calls.jsonl`. Introduce the separate MCP server and its
execution record in the next scene.

**Optional code view:** show `affordability_calc` in
`app/packages/api/src/agents/tools.py`, then the pure calculation in
`app/packages/api/src/services/calculator.py`.

The model initially skipped this tool during setup; a shorter local system
prompt improved the tested behavior. Temperature zero is not a correctness
guarantee. If it skips the tool live, identify the failure; use the saved
rehearsal evidence or explicitly request the tool rather than endorsing its answer.

## Scene 3 — introduce a real MCP boundary (3 minutes)

**Say**

> Now we want tools that can run outside this application and be discovered
> through a shared protocol. We'll add a separate risk-calculation service
> using MCP. The model still selects tools, and the harness executes them.

**Do — terminal**

```bash
bash fedaura/demo.sh stage mcp
bash fedaura/demo.sh mcp
```

**Look for**

Six discovered tools, followed by the `calculate_dti` JSON input schema and a
real calculation:

```text
calculate_dti
calculate_ltv
evaluate_credit_risk
assess_income_stability
assess_asset_sufficiency
generate_risk_recommendation

calculate_dti(monthly_income=8500, monthly_debts=2400)
value: 28.2
rating: Low
```

**Say**

> This small inspection client just initialized a connection, listed tools,
> read their input schemas and called one. No language model was involved.
> MCP describes how clients discover and invoke capabilities; it doesn't
> provide the reasoning model or guarantee the tool's correctness.

**Show briefly**

* `app/packages/api/src/mcp_server.py`: an `@mcp.tool()` function and the HTTP server.
* `app/packages/api/src/agents/mcp_integration.py`: `MultiServerMCPClient`,
  `get_tools()`, and the tool list passed into the underwriter's graph.

**Say**

> The native catalog/calculator tools and the MCP tools reach the graph through
> different integrations. The MCP server is a separate process with an HTTP
> endpoint. It could later run as its own service on a cluster.

## Scene 4 — let the underwriter use the external tools (2–3 minutes)

**Do — browser**

1. Refresh after the stage change if the old WebSocket disconnected.
2. Choose **Sign In**.
3. In **Persona Demo Login**, select **Underwriter**, then submit the form.
   The development identity is Maria Chen (`maria.chen@example.com`), with
   the prefilled demo password `demo1234`.
4. In the underwriter chat sidebar, use **Clear chat history** before a repeat
   rehearsal. Stay on the queue page rather than selecting an application;
   the next question is a standalone calculation with explicit inputs.

**Say**

> This local sign-in selects a development persona; it is not Keycloak
> authentication. We'll show enterprise identity in the existing cluster app.
> The underwriter has a different set of tools from the public assistant.

Paste `fedaura/prompts/risk.txt`:

```text
For a standalone synthetic example, use your external risk tools to calculate DTI and LTV and evaluate credit risk: monthly income $8,500, monthly debts $2,400, loan amount $320,000, property value $400,000, and self-reported credit score 742. Give the three values and their risk ratings. Do not make a lending decision or look up an application.
```

**Look for**

Actual badges for `calculate_dti`, `calculate_ltv`, `evaluate_credit_risk`.
The MCP execution file should show the corresponding completed calls.

| Tool | Expected result | Demo rating |
|---|---:|---|
| DTI | 28.2% | Low |
| LTV | 80.0% | Medium |
| Credit risk | 742, self-reported | Low |

**Say**

> Those ratios came from the external service. The model turns the returned
> data into an explanation. We can inspect the input schema, test the
> calculation, and observe that the service was actually called.

Do not describe this as a complete underwriting decision. It is three risk
factors using synthetic inputs. The laptop agent cannot issue decisions through
its reduced tool set.

**Rehearsal note**

An authenticated conversation persists. Repeating the same question in the same
conversation can reuse previous tool evidence without calling the service again.
Clear history before demonstrating new execution. Terminal `chat risk` uses a
fresh synthetic identity automatically.

## Optional scene — connect it to seeded application data (1 minute)

Prefer browsing the existing queue UI: it displays seeded application records
without asking the model to summarize every detail. There are 38 total seeded
applications (10 active, 28 historical); the underwriting queue is a subset.

If you want an agent-driven queue scene, rehearse the current prompt in
`prompts/queue.txt` first. It asks only for the count, actual IDs and names.
Do not hardcode an ID from an old run. An earlier broad queue response
misstated a credit-risk label, so the main live script avoids that summary.

## Scene 5 — switch to the existing cluster application (1 minute)

**Say**

> We've built the behavior locally: application UI, agent orchestration,
> deterministic tools, and a separate MCP service. The next questions are about
> operating it for a team: managed model access, identity, visibility and quality.
>
> I already have this application deployed on our platform. Let's move to that
> environment and look at MaaS, MLflow traces, and evaluations.

**Do**

Switch to your pre-opened cluster application tab. Make the environment change
explicit. Run the equivalent rehearsed task there, then use your existing
MLflow/evaluation views.

Do not imply the local database was migrated live or that the two deployments
share conversation state. Match prompts to the selected environment's data.
The standalone calculator prompt is useful because its inputs are explicit.

Suggested platform narrative:

| Question | Existing cluster capability to show |
|---|---|
| How does the application obtain model access? | MaaS endpoint and access configuration |
| Who can access which experience? | Your deployed identity/role setup |
| What did the agent actually do? | MLflow trace and tool spans actually captured |
| Did a change improve quality? | Existing evaluation dataset and completed results |

No cluster installation, deployment or credential changes are part of this
local demo package. Use your existing platform material and verified features.

## Recovery card

| Problem | Action |
|---|---|
| App isn't ready | Run `demo.sh status` and `demo.sh check`; inspect `runtime/startup.log` and `runtime/api.log`. |
| Podman cannot connect | Start your Podman machine before `up`. The scripts do not reset or recreate it. |
| Model missing | Run `ollama pull qwen3.5:9b` before the talk. |
| UI chat disconnected after stage switch | Refresh and reconnect. |
| No fresh tools on a repeated underwriter question | Clear authenticated chat history before repeating. |
| Model invents a number / skips tools | Treat the run as failed. Show deterministic checks or labeled saved evidence. |
| Browser interaction fails | Use `demo.sh chat products`, `chat affordability`, or `chat risk` against the same real endpoints. |
| Need to prove MCP separately | `demo.sh mcp` works without a model call. |
| Need to revert to opening scene | `demo.sh stage assistant`, sign out, refresh. |

Keep the rehearsal JSON files in `runtime/chat-*.json` available. If showing a
saved result, identify it as a previous run, rather than presenting it as live.

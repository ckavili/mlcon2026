# Source and local adaptations

Source repository:
`/Users/ckavili/RedHat/Tech/multi-agent-loan-origination`

Source HEAD when copied:
`16eecabc8b23b1ab97ca41b0e42f9fbafc50d468`

`SOURCE.json` records the copy. The copy used working-tree contents of tracked
application files, not a clean Git archive; the revision is provenance, not a
claim that every copied byte matched HEAD. The original checkout was not edited.

Copied under `app/`: API, UI, database, shared workspace configs, agent/model
configuration, synthetic data, workspace manifests, locks, and original license.
No `.git`, personal `.env`, cloud credentials, agent settings, or original
runtime environments were copied. The cluster deployment is deliberately absent.

Local changes:

* Added independent lifecycle scripts and Compose infrastructure, on separate ports.
* Moved MLflow/pipeline packages into the API's optional `platform` extra and
  sentence-transformer dependencies into `knowledge`; neither is installed locally.
* Skipped KB embedding ingestion during local data seeding and made embedding
  model imports lazy. KB workflows are outside the rehearsed local scope.
* Stabilized synthetic fixture timestamps using an explicit demo date.
* Added `assistant` / `mcp` startup composition and fail-fast discovery/seed checks.
* Reduced the local underwriter to read-only queue/detail tools plus MCP calculators.
  Loan decisions, document handling and compliance workflows are not part of it.
* Shortened local public/underwriter prompts for the laptop model; full cluster
  prompts remain in the original application.
* Set local model temperature to zero and disabled reasoning effort, with a request
  timeout and limited retry. These are local-copy model settings.
* Forwarded existing tool events over WebSocket to the UI's existing tool badges.
  Retained only the final model response, excluding intermediate tool narration.
* Added actual MCP execution records without logging financial input values.
* Pointed Vite and service links to the local ports and supplied Fedaura branding.

Reused rather than rewritten: LangGraph orchestration, native product/calculator
tools, MCP risk functions, FastAPI routes, database migrations, synthetic fixtures,
UI pages and components, conversation persistence, and existing calculator tests.

This is a presentation adaptation of the application, not an upstream release
or a replacement for the deployed cluster configuration. Preserve the original
license at `app/LICENSE` when redistributing the copied code.

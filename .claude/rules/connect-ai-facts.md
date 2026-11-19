---
paths:
  - "app/agent.py"
  - "app/config.py"
  - "app/errors.py"
  - "app/live.py"
  - "tests/**"
---

# Connect AI facts worth not re-deriving

Verified against a live workspace, 2026-10-13 and 2026-10-14 unless noted.

- **The gateway URL** `https://cloud.cdata.com/gateway/v1` works with or without `/v1`, from both the Anthropic and OpenAI SDKs. Overhead was about 0.2 s on a small call.
- **The routing rule decides the model, not the request.** Any model name sent (even a made-up one, or `gpt-4o` from the OpenAI SDK) was served by the rule's first model. `LLM_MODEL` becomes a label.
- **Budget headers** on every gateway response: `x-project-budget-limit-usd`, `-used-usd`, `-remaining-usd`, `-period`.
- **Current Claude models reject `temperature`** with a 400, direct or through the gateway. `build_agent` only sends it for other providers.
- **`?ops=` on the MCP URL scopes tools:** 13 become 6, dropping `execute_insert`, `execute_update`, and `executeProcedure`.
- **Data Security rules apply to connector query results, not prompts.** A fake SSN typed into a prompt went through the LLM Gateway untouched. Rule changes take effect on the next query. Rows built to test edge cases (`000-` and `666-` SSNs, cards that fail Luhn) are correctly not masked, but look like leaks on a projector.
- **A restart rereads `.env`.** compose reads `env_file` only when it creates the container, so `live.load_workspace_env()` applies the mounted file at startup; without it, `docker compose restart agent` kept the old credentials (found 2026-10-27).
- **The agent's data access is the PAT user's access.** Each connection's **Permissions** tab has per-user Select, Insert, Update, Delete, and Execute. With Select unchecked, the agent can't see the connection at all on its next query.
- **MCP Logs only records traffic through an MCP Gateway Tool Server.** This app calls `mcp.cloud.cdata.com/mcp` directly, so MCP Logs stays empty; the Query Log still records every SQL statement with the user.
- **Asked casually for PII, the agent declines to query it** (it finds the dataset's own redaction policy table). That is the model being careful, not the platform. The scripted questions ask for the exact query and raw result so the platform's masking is what the audience sees.
- MCP auth is HTTP Basic with base64 of `email:PAT`. Tables are `[Catalog].[Schema].[Table]`, and the catalog is the connection name.
- Tool errors such as bad SQL never reach `/chat`: `langchain-mcp-adapters` returns them to the model as a `ToolMessage` with `status="error"`. Only transport failures escape.
- `getTables` unfiltered can return over 100K tokens on a large source. `TruncateToolOutput` caps each result at `TOOL_OUTPUT_MAX_CHARS` and tells the model how to narrow the call.
- The agent loads its MCP tools at startup and on each `.env` reload, so bad credentials fail the boot (or the reload) rather than the first request.

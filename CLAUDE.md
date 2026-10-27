# Working in this repo

A public demo that anyone with a Connect AI account can run: a LangGraph agent over CData Connect AI's MCP server, with a chat page, that gets governed live by editing `.env` (LLM Gateway, read-only tools) and flipping console switches (Data Security masking, per-user permissions). The README walks a stranger through it with the sample data in `sample-data/`. Weigh every change against whether that walkthrough still works from a fresh clone.

It started as the agent from the developer session at CData Foundations 2026, split out of `connect-ai-render-starter` (the Render partnership starter) on 2026-10-26 from its `foundations-gateway-demo` branch. The presenter tooling (stage script, `/?demo` mode, run of show, spoken script) was removed on 2026-10-27; it's still on that branch if a talk needs it again. Leave that repo alone: it backs a separate blog partnership. Fixes that apply to both are copied by hand.

Ignore `../AGENTS.md`. It describes a Mintlify documentation site in the parent directory, not this project.

`README.md` is the user-facing setup and walkthrough, and `CONTRIBUTING.md` the change checklist. This file holds what neither makes obvious.

## Layout

| Path | Role |
| --- | --- |
| `app/main.py` | FastAPI app: startup (Postgres check, agent build, `.env` watcher, retention task), `/chat`, `/chat/stream`, `/status`, `/healthz`, `/tools`, the chat page at `/` |
| `app/live.py` | Watches `.env`, rebuilds the agent on change, and describes the live route (gateway or direct, key kind, model, tool scope) for the header |
| `app/agent.py` | `create_agent` over MCP tools; `TruncateToolOutput` middleware caps tool results |
| `app/config.py` | Env parsing and validation; `LLM_API_KEYS` maps provider to key variable |
| `app/errors.py` | `SetupError`, `root_cause()`, `describe_mcp_error()`, `describe_llm_error()` |
| `app/steps.py` | Human labels for tool calls; extracts this turn's SQL (`queries_in`) |
| `app/suggest.py` | One extra LLM call after each streamed answer for three follow-up questions |
| `app/retention.py` | Deletes conversations idle past `CONVERSATION_RETENTION_DAYS` |
| `app/static/index.html` | Single-file chat page; reads `/chat/stream`, polls `/status` for the header pills |
| `app/static/vendor/` | marked and DOMPurify, copied unmodified from npm; versions, hashes, and licenses in its README |
| `app/static/brand/` | CData logos, favicon, and DM fonts from the brand kit; sources and rules in its README |
| `sample-data/` | 50 synthetic customers (SQL and CSV) for the walkthrough; the README's questions name customer 1004 and the top five by lifetime value |
| `compose.yaml`, `Dockerfile`, `.dockerignore` | The local stack (agent plus Postgres) |
| `requirements.in` → `requirements.txt` | Top-level deps → compiled exact pins |
| `tests/`, `pytest.ini`, `requirements-dev.*` | Test suite and its pinned dependencies |
| `.github/workflows/ci.yml` | Tests, pin check, and Docker build on each PR |

## How the live swap works

compose mounts the project at `/workspace`. `app/live.py` polls `/workspace/.env` every 0.5 s by content hash (file events don't cross Colima's VM boundary, and editors that replace the file can leave the mtime unchanged through a mount), waits 0.3 s for the save to finish, applies the file to `os.environ`, and builds a new agent. Requests already running finish on the agent they started with. A bad edit keeps the old agent and sets `live_error`, which the header shows as **Reload failed, see logs**.

- Variables compose sets under `environment:` (`DATABASE_URL`, `WATCHFILES_FORCE_POLLING`, `LIVE_WORKSPACE`) are `PINNED` and always win over `.env`.
- A variable removed from `.env` is removed from `os.environ`, so commenting out `ANTHROPIC_BASE_URL` really sends the next call direct.
- The header calls the route "Connect AI LLM Gateway" when the base URL's host is `cloud.cdata.com` and its path starts with `/gateway`, and "virtual key" when the key starts with `cgw_`. It never shows a key, only its kind.
- `/status` reports `served_model`, the model named in the last response's metadata. Through a gateway routing rule it can differ from `LLM_MODEL`.

## Connect AI facts worth not re-deriving

Verified against a live workspace, 2026-10-13 and 2026-10-14 unless noted.

- **The gateway URL** `https://cloud.cdata.com/gateway/v1` works with or without `/v1`, from both the Anthropic and OpenAI SDKs. Overhead was about 0.2 s on a small call.
- **The routing rule decides the model, not the request.** Any model name sent (even a made-up one, or `gpt-4o` from the OpenAI SDK) was served by the rule's first model. `LLM_MODEL` becomes a label.
- **Budget headers** on every gateway response: `x-project-budget-limit-usd`, `-used-usd`, `-remaining-usd`, `-period`.
- **Current Claude models reject `temperature`** with a 400, direct or through the gateway. `build_agent` only sends it for other providers.
- **`?ops=` on the MCP URL scopes tools:** 13 become 6, dropping `execute_insert`, `execute_update`, and `executeProcedure`.
- **Data Security rules apply to connector query results, not prompts.** A fake SSN typed into a prompt went through the LLM Gateway untouched. Rule changes take effect on the next query. Rows built to test edge cases (`000-` and `666-` SSNs, cards that fail Luhn) are correctly not masked, but look like leaks on a projector.
- **The agent's data access is the PAT user's access.** Each connection's **Permissions** tab has per-user Select, Insert, Update, Delete, and Execute. With Select unchecked, the agent can't see the connection at all on its next query.
- **MCP Logs only records traffic through an MCP Gateway Tool Server.** This app calls `mcp.cloud.cdata.com/mcp` directly, so MCP Logs stays empty; the Query Log still records every SQL statement with the user.
- **Asked casually for PII, the agent declines to query it** (it finds the dataset's own redaction policy table). That is the model being careful, not the platform. The scripted questions ask for the exact query and raw result so the platform's masking is what the audience sees.
- MCP auth is HTTP Basic with base64 of `email:PAT`. Tables are `[Catalog].[Schema].[Table]`, and the catalog is the connection name.
- Tool errors such as bad SQL never reach `/chat`: `langchain-mcp-adapters` returns them to the model as a `ToolMessage` with `status="error"`. Only transport failures escape.
- `getTables` unfiltered can return over 100K tokens on a large source. `TruncateToolOutput` caps each result at `TOOL_OUTPUT_MAX_CHARS` and tells the model how to narrow the call.
- The agent loads its MCP tools at startup and on each `.env` reload, so bad credentials fail the boot (or the reload) rather than the first request.

## Local development

- **Docker engine.** Colima (`brew install colima docker docker-compose docker-buildx`), with `"cliPluginsExtraDirs": ["/opt/homebrew/lib/docker/cli-plugins"]` in `~/.docker/config.json`. Colima shares only `$HOME` with its VM: a bind mount from `/tmp` or a scratchpad is silently empty inside the container (`Could not import module "app.main"`).
- **Hot reload** of code relies on `WATCHFILES_FORCE_POLLING`; without it `--reload` never fires on Colima. `.env` changes are picked up by `app/live.py` instead, with no restart.
- **The agent healthcheck** exists because under `--reload` a failed startup leaves the container running. With it, `docker compose ps` says `unhealthy`.
- **Ports** are `AGENT_PORT` (8000) and `DB_PORT` (5432), overridable in `.env`.
- **Do not print resolved config.** `docker compose config` expands `.env` into the output, secrets included.

## Tests

`.venv/bin/pytest` (about a minute; `docker compose up -d db` first for the database tests). `CONTRIBUTING.md` describes the layers and the live opt-in.

- **Fakes, not network.** `tests/fakes.py` has `FakeMCPClient` (patched over `app.agent.MultiServerMCPClient`) and `ScriptedModel`. `make_client` in `conftest.py` stubs the lifespan for route tests; `test_startup.py` runs the real lifespan against real Postgres.
- **Realistic failures.** Build them from the real types: `openai.AuthenticationError(..., response=httpx.Response(401, ...))`, `httpx.HTTPStatusError` inside nested `ExceptionGroup`s, `McpError`.
- **Environment is cleared before every test** (`clean_env`, from `APP_ENV_VARS` in `conftest.py`), so `.env` never leaks in. Add any new variable there.
- **Database tests use `agent_test`**, created on first use; they never touch the `agent` database.
- **Browser tests** run `tests/ui_server.py` under uvicorn with the internet blocked, using the installed Chrome if present, else Playwright's Chromium.
- **In CI, missing Postgres or browser fails** instead of skipping (`skip_or_fail`).
- When fixing a bug, check the new test fails without the fix.

## Conventions

- **Never commit credentials.** `.env` and `.env.*` are gitignored except `.env.example`. The header shows a key's kind, never the key; keep anything new that displays `.env` masked too.
- **`APP_API_KEY` is optional.** Empty disables the bearer check on `/chat` and `/tools`. That's only safe because `compose.yaml` publishes ports on `127.0.0.1`; keep it that way.
- **Operator-fixable failures raise `SetupError`** with a message naming the variable to change. Extend `describe_mcp_error` and `describe_llm_error` for new failure modes rather than catching locally.
- **Model output is hostile.** The page sets every server string with `textContent`; only the reply goes through marked and DOMPurify.
- **Strip every env var before use**, and keep `.env` comments on their own lines (python-dotenv reads an inline comment after an empty value as the value).
- **Never hand-edit `requirements.txt`.** The compile command is at the top of `requirements.in`.
- **Branding:** Agility yellow `#FFE500` is an accent, never text, and only with Depth `#15151C` on it. Navy fills take white text. `test_text_contrast_meets_wcag_aa` fails on a colour change that breaks AA. Rules are in `app/static/brand/README.md`.

## Public repo

- The repo URL `CDataSoftware/connect-ai-gateway-demo` is hardcoded in the README clone command, the chat page footer, `REPO` in `tests/test_ui.py`, and `.github/ISSUE_TEMPLATE/config.yml`. Change them together.
- Private vulnerability reporting, secret scanning, and push protection are on; `SECURITY.md` and the issue chooser link to private reporting.
- `sample-data/` must stay synthetic: made-up names, random SSNs, and the card networks' published test numbers. The README's walkthrough questions depend on its customer IDs.

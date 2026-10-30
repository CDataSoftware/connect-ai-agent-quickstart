# Working in this repo

A public demo that anyone with a Connect AI account can run: a LangGraph agent over CData Connect AI's MCP server, with a chat page, that gets governed live by editing `.env` (LLM Gateway, read-only tools) and flipping console switches (Data Security masking, per-user permissions). The README walks a stranger through it with the sample data in `sample-data/`. The quick start sends model calls through the Connect AI LLM Gateway with a virtual key by default, so a user needs no model provider key; keep it that way (Joe, 2026-10-27). Weigh every change against whether that walkthrough still works from a fresh clone.

It started as the agent from the developer session at CData Foundations 2026, split out of `connect-ai-render-starter` (the Render partnership starter) on 2026-10-26 from its `foundations-gateway-demo` branch. The presenter tooling (stage script, `/?demo` mode, run of show, spoken script) lives on this repo's `foundations-demo` branch; `main` stays a getting-started guide for anyone setting up Connect AI with a chat interface. Fixes to shared code go on `main` first, then get cherry-picked to `foundations-demo` when the demo needs them. Leave that repo alone: it backs a separate blog partnership. Fixes that apply to both are copied by hand.

`README.md` is the user-facing setup and walkthrough, and `CONTRIBUTING.md` the change checklist. This file holds what neither makes obvious; area detail loads from `.claude/rules/` when you touch matching files.

## Tests

`.venv/bin/pytest` (about a minute; `docker compose up -d db` first for the database tests). `CONTRIBUTING.md` describes the layers and the live opt-in.

## Conventions

- **Never commit credentials.** `.env` and `.env.*` are gitignored except `.env.example`. The header shows a key's kind, never the key; keep anything new that displays `.env` masked too.
- **`APP_API_KEY` is optional.** Empty disables the bearer check on `/chat` and `/tools`. That's only safe because `compose.yaml` publishes ports on `127.0.0.1`; keep it that way.
- **Operator-fixable failures raise `SetupError`** with a message naming the variable to change. Extend `describe_mcp_error` and `describe_llm_error` for new failure modes rather than catching locally.
- **Model output is hostile.** The page sets every server string with `textContent`; only the reply goes through marked and DOMPurify.
- **Strip every env var before use**, and keep `.env` comments on their own lines (python-dotenv reads an inline comment after an empty value as the value).
- **Never hand-edit `requirements.txt`.** The compile command is at the top of `requirements.in`.
- **Do not print resolved config.** `docker compose config` expands `.env` into the output, secrets included.

## Public repo

- `sample-data/customers.csv`: never rename or move it. The quick start has Connect AI read it from its raw GitHub URL on `main`, so a rename breaks step 1.
- The repo URL `CDataSoftware/connect-ai-agent-quickstart` is hardcoded in the README clone command, the chat page footer, `REPO` in `tests/test_ui.py`, and `.github/ISSUE_TEMPLATE/config.yml`. Change them together.
- Private vulnerability reporting, secret scanning, and push protection are on; `SECURITY.md` and the issue chooser link to private reporting.
- `sample-data/` must stay synthetic: made-up names, random SSNs, and the card networks' published test numbers. The README's walkthrough questions depend on its customer IDs.

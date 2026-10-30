---
paths:
  - "tests/**"
---

# Tests

- **Fakes, not network.** `tests/fakes.py` has `FakeMCPClient` (patched over `app.agent.MultiServerMCPClient`) and `ScriptedModel`. `make_client` in `conftest.py` stubs the lifespan for route tests; `test_startup.py` runs the real lifespan against real Postgres.
- **Realistic failures.** Build them from the real types: `openai.AuthenticationError(..., response=httpx.Response(401, ...))`, `httpx.HTTPStatusError` inside nested `ExceptionGroup`s, `McpError`.
- **Environment is cleared before every test** (`clean_env`, from `APP_ENV_VARS` in `conftest.py`), so `.env` never leaks in. Add any new variable there.
- **Database tests use `agent_test`**, created on first use; they never touch the `agent` database.
- **Browser tests** run `tests/ui_server.py` under uvicorn with the internet blocked, using the installed Chrome if present, else Playwright's Chromium.
- **In CI, missing Postgres or browser fails** instead of skipping (`skip_or_fail`).
- When fixing a bug, check the new test fails without the fix.

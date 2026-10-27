# Contributing

Thanks for helping improve the Connect AI Agent Quickstart. Its job is to let anyone see, in their own Connect AI workspace, what changes when an agent's model calls and data access go through CData Connect AI. Before you change anything, check that the README walkthrough still works from a fresh clone.

## Set up

Follow the [Quick start](README.md#quick-start) in the README:

```bash
cp .env.example .env    # set CDATA_USERNAME, CDATA_PAT, and ANTHROPIC_API_KEY
docker compose up       # http://localhost:8000, reloads on edits under app/ and .env
```

Use a sandbox Connect AI workspace. With the default MCP endpoint, the agent can query every connection your PAT can see, and query results go to your LLM provider.

## Making a change

1. Branch from `main`.
2. Keep the change focused, and match the surrounding code's style and comment density.
3. Verify it (below), then open a pull request that says what changed, why, and how you checked it.

Rules of the road:

- **Never commit credentials.** Only `.env.example` is committed, with empty values. Search your diff for keys before pushing.
- **Keep secrets masked on screen.** Anything that prints or displays `.env` masks keys, the way the header does. People share their screens while they try this.
- **Make failures say how to fix them.** Raise `SetupError` (from `app/errors.py`) for anything an operator can correct, with a message naming the variable to change.
- **Don't hand-edit `requirements.txt`.** Edit `requirements.in`, then run the compile command at the top of that file (it needs [uv](https://docs.astral.sh/uv/)). Commit both files.
- **Don't weaken local-only auth.** An empty `APP_API_KEY` disables the API key check, which is only safe because `compose.yaml` binds ports to `127.0.0.1`.

## Verifying a change

### Run the tests

```bash
uv venv --python 3.12 .venv   # uv fetches Python 3.12 if you don't have it
uv pip install --python .venv -r requirements.txt -r requirements-dev.txt
docker compose up -d db       # for the database tests
.venv/bin/pytest              # about a minute
```

The suite runs offline, with fakes standing in for the MCP server and the model.

| Layer | Files | Needs |
| --- | --- | --- |
| Unit | `test_config`, `test_errors`, `test_agent`, `test_routes`, `test_stream`, `test_steps`, `test_suggest`, `test_live_reload` | Nothing |
| Database (`-m db`) | `test_startup`, `test_retention` | Postgres; uses a separate `agent_test` database |
| Browser (`-m ui`) | `test_ui` | Chrome, or `.venv/bin/playwright install chromium`; runs with the internet blocked |
| Live (`-m live`) | `test_live` | A real Connect AI account; opt in with `RUN_LIVE_TESTS=1` |

Database and browser tests skip locally when their dependency is missing, and fail in CI instead. To check against real Connect AI (the live tests don't call an LLM):

```bash
set -a; source .env; set +a
RUN_LIVE_TESTS=1 .venv/bin/pytest -m live
```

### Check by hand

- [ ] **It boots:** `docker compose up` logs `Loaded N tools` and `Live reload on`, and `curl localhost:8000/healthz` reports `mcp_tools` above 0.
- [ ] **The swap works** if you touched `app/live.py` or `.env.example`: switch to the gateway lines in `.env`, save, and watch the header's LLM pill change with no restart.
- [ ] **The chat page looks right** in a browser if you touched `app/static/`. The tests check behaviour, not appearance.

## Documentation

Update the docs in the same pull request: `README.md` for anything a user sees (including the walkthrough), and `CLAUDE.md` for anything a maintainer would otherwise rediscover the hard way.

## Reporting a security issue

Don't open a public issue for a vulnerability. See [SECURITY.md](SECURITY.md).

## License

By contributing, you agree to license your contributions under the [MIT License](LICENSE).

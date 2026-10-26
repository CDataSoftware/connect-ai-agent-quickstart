# Connect AI Gateway Demo

An AI agent that starts out the way many agents ship today (a raw provider key, every MCP tool including writes, and no record of who asked what) and gets governed by CData Connect AI with three lines in `.env` and two switches in the console. It's the agent from the developer segment of CData Foundations 2026.

The agent is a LangGraph loop over Connect AI's remote MCP server, with a chat page so you can watch each tool call and the SQL it runs. The same setup runs behind Slack bots, scheduled jobs, and internal tools; the chat page is only a viewer.

## What the demo shows

| Step | Change | What you get |
| --- | --- | --- |
| 1. Start direct | `ANTHROPIC_API_KEY` is a raw provider key, and the MCP server hands the agent 13 tools, including `execute_insert`, `execute_update`, and `executeProcedure` | No log of who asked what, no spend cap, and no fallback if the provider goes down |
| 2. Route models through the gateway | Two lines: `ANTHROPIC_BASE_URL` points at the Connect AI LLM Gateway, and `ANTHROPIC_API_KEY` becomes a gateway virtual key | Every model call logged with tokens, cost, latency, and user; a routing rule that picks the model and fails over; a hard monthly budget; a virtual key you can revoke without redeploying |
| 3. Read-only tools | One line: `CDATA_MCP_URL` with `?ops=` lists the six read tools | The agent can no longer insert, update, or run stored procedures |
| 4. Mask sensitive data | Two switches under **Data Security** in Connect AI | Social Security and credit card numbers come back as `XXXX` in every query result, for every agent in the workspace, before the model sees them |
| 5. Scope to the user | Uncheck **Select** for your user on the connection's **Permissions** tab | The agent signs in as you with your personal access token, so it loses the connection on its next query |

The app watches `.env` and rebuilds the agent within about a second of a save, so every step happens live with no restart. The header shows where model calls go, which model answered, and how many tools the agent has, and it flashes when any of them change.

## What you need

1. **A CData Connect AI account** with at least one connection. The recorded demo uses a Postgres database of synthetic customers with fake Social Security and card numbers; any connection works for steps 1 through 3 and 5, and step 4 needs a table with values the Data Security rules detect.
2. **A Connect AI personal access token (PAT)**, from **Settings** > **Access Tokens** ([how](https://docs.cloud.cdata.com/en/Settings/Personal-Access-Tokens)).
3. **An Anthropic API key** for step 1, from the [Anthropic console](https://console.anthropic.com/settings/keys).
4. **For step 2, a Connect AI LLM Gateway project** with your Anthropic key added as a provider, a routing rule, and a virtual key (it starts `cgw_`). A budget on the project is optional but makes the demo.
5. **[Docker](https://docs.docker.com/get-started/get-docker/)** ([no Docker on your Mac?](#no-docker-on-your-mac)).

## Run it

```bash
git clone https://github.com/CDataSoftware/connect-ai-gateway-demo.git
cd connect-ai-gateway-demo
cp .env.example .env    # fill in CDATA_USERNAME, CDATA_PAT, and ANTHROPIC_API_KEY
docker compose up
```

Open <http://localhost:8000> and ask a question about your data. The first `docker compose up` takes about 20 seconds to build; later starts take a few seconds. If startup fails, the log's `Startup failed:` line names the variable to fix.

Then work through the steps in `.env`, which already has the gateway and read-only lines in place, commented out:

1. **Gateway:** comment out the first `ANTHROPIC_API_KEY`, uncomment `ANTHROPIC_BASE_URL` and the second `ANTHROPIC_API_KEY`, paste your virtual key, and save. The header's LLM pill switches to **Connect AI LLM Gateway, virtual key**. Ask the same question and find the call under **Logs** in Connect AI.
2. **Read-only:** uncomment `CDATA_MCP_URL` and save. Click the Tools pill in the header: 13 tools become six.
3. **Masking:** in Connect AI, open **Data Security**, turn on the Credit Card Number and US Social Security Number rules, and save. Ask for a customer's SSN and card number.
4. **Per-user access:** open your connection under **Sources**, go to **Permissions**, uncheck **Select** on your own row, and save. Ask again. Check it again afterward, especially on a shared connection.

## Presenting it

`demo/` holds what the live presentation uses:

- `demo/FOUNDATIONS.md` is the run of show, the exact questions, and what was verified (and what wasn't) about the gateway, masking, and permissions.
- `demo/SCRIPT.md` is the spoken script with every cue, formatted for a teleprompter.
- `demo/stage.py` rewrites `.env` to each step's layout from secrets in a gitignored `.env.foundations`, and prints the change with secrets masked:

  ```bash
  python demo/stage.py direct     # step 1
  python demo/stage.py gateway    # step 2
  python demo/stage.py governed   # steps 2 and 3
  ```

Open <http://localhost:8000/?demo> for demo mode: ⌥ → runs the next step (sends the scripted question or opens the next console page), ⌥ R resets `.env` and the chat, and ⌥ H hides the step hint.

**Keep keys off the screen.** `.env` holds a live provider key and a virtual key in plain text. Before you record or share your screen, open `.env` with the keys scrolled out of view or use `demo/stage.py`, which masks them when it prints. Revoke any key that shows up in a recording.

## How it works

| Piece | What it does |
| --- | --- |
| `app/agent.py` | Builds the agent: Connect AI's MCP tools, the model from `LLM_MODEL`, and a cap on tool output so a large table listing can't overflow the context window |
| `app/live.py` | Watches `.env`, rebuilds the agent when it changes, and reports the live route, model, and tool scope to the header |
| `app/main.py` | The API (`/chat`, `/chat/stream`, `/tools`, `/status`, `/healthz`) and the chat page |
| `app/static/` | The chat page: live steps, the SQL behind each answer, and follow-up suggestions |
| Postgres | Conversation history, so chats survive restarts; idle conversations are deleted after 30 days |

The agent signs in to Connect AI over HTTP Basic auth with your username and PAT, so it gets exactly your access. Connect AI applies Data Security rules to query results on the way out, so the masked value is what the agent and the model receive. The database still stores the real values.

The routing rule, not the request, decides which model answers: `LLM_MODEL` becomes a label, and `/status` reports the model that was actually served. The gateway also accepts the OpenAI SDK at the same URL, so an agent written for OpenAI moves over with the same two-line change (`OPENAI_BASE_URL` and `OPENAI_API_KEY`, with `LLM_MODEL=openai:<model>`).

## Use the API

The chat page is a thin client over the API, documented at <http://localhost:8000/docs>.

```bash
curl http://localhost:8000/healthz
# {"status":"ok","mcp_tools":13,"llm_model":"anthropic:claude-sonnet-5-5","auth_required":false}

curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What data sources can you reach?"}'
```

The reply includes `queries`, the SQL the agent ran. Send the returned `thread_id` back with follow-up messages to continue a conversation. `/chat/stream` takes the same body and returns newline-delimited JSON events (`start`, `step`, `step_done`, `done`, then an optional `suggestions`, or `error` if the run fails).

Through the gateway, every model response also carries budget headers (`x-project-budget-limit-usd`, `-used-usd`, `-remaining-usd`, and `-period`), so an app can see a hard limit coming before it hits.

## Local development

```bash
docker compose logs -f agent            # follow the agent's logs
docker compose exec db psql -U agent    # inspect the database
docker compose down                     # stop; add -v to also wipe the database
```

Edits under `app/` reload on their own. To run the tests, see [CONTRIBUTING.md](CONTRIBUTING.md).

### No Docker on your Mac?

[Colima](https://github.com/abiosoft/colima) is a free, lightweight engine:

```bash
brew install colima docker docker-compose docker-buildx
colima start
```

Then add `"cliPluginsExtraDirs": ["/opt/homebrew/lib/docker/cli-plugins"]` to `~/.docker/config.json` so `docker compose` is found. Colima shares only your home directory with containers, so keep the repo under `~`.

## Troubleshooting

| Message | Fix |
| --- | --- |
| `Connect AI rejected the credentials (HTTP 401)` | `CDATA_USERNAME` must be your login email and `CDATA_PAT` a current token. |
| `LLM_MODEL=... needs ANTHROPIC_API_KEY` | Set the key, or uncomment the gateway lines. |
| `The LLM provider rejected the API key` | The provider key or virtual key is wrong or revoked. |
| `Could not connect to Postgres` | Run `docker compose up -d db`. |
| The header shows **Reload failed, see logs** after a save | The new `.env` didn't load, so the previous agent is still answering. `docker compose logs agent` shows a `Reload from .env failed` line with the reason. |
| The agent refuses instead of querying | The model is being careful, which hides what the platform does. Ask for the exact query and its raw result; `demo/FOUNDATIONS.md` has wording that works. |
| `port is already allocated` | Set `AGENT_PORT` or `DB_PORT` in `.env`, for example `DB_PORT=5433`. |

## License

[MIT](LICENSE) © CData Software, Inc. The CData name and logos are trademarks of CData Software and aren't covered by the license; see [app/static/brand](app/static/brand/README.md).

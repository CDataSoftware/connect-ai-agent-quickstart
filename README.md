# Connect AI Gateway Demo

Run an AI agent against your own data the way many agents go to production today: with a raw provider key, write access through every MCP tool, and no record of who asked what. Then put CData Connect AI in front of its model calls and its data, one step at a time, while it keeps running. Each step is a line or two in `.env` or a switch in the Connect AI console. The code stays the same and the app never restarts.

The agent is a LangGraph loop over Connect AI's remote MCP server, with a chat page that shows each tool call and the SQL it runs. It's the agent from the developer session at CData Foundations 2026, set up so you can try the same thing in your own workspace in about 20 minutes.

## What you'll try

| Step | You change | What you get |
| --- | --- | --- |
| 1. Start direct | Nothing yet: `ANTHROPIC_API_KEY` is a raw provider key, and the agent has all 13 MCP tools, including `execute_insert`, `execute_update`, and `executeProcedure` | A working agent with no log of who asked what, no spend cap, and no fallback if the provider goes down |
| 2. Route models through the gateway | Two lines in `.env`: `ANTHROPIC_BASE_URL` points at the Connect AI LLM Gateway, and `ANTHROPIC_API_KEY` becomes a gateway virtual key | Every model call logged with tokens, cost, latency, and user; a routing rule that picks the model and fails over; a hard monthly budget; a key you can revoke without touching the provider key |
| 3. Make the tools read-only | One line in `.env`: `CDATA_MCP_URL` with `?ops=` lists the six read tools | The agent can no longer insert, update, or run stored procedures |
| 4. Mask sensitive data | Two rules under **Data Security** in Connect AI | Social Security and credit card numbers come back as `XXXX` in every query result, for every agent in the workspace, before the model sees them |
| 5. Scope to the user | Uncheck **Select** for yourself on the connection's **Permissions** tab | The agent signs in as you, so it loses the connection on its next query |

The app watches `.env` and rebuilds the agent within about a second of a save. The header shows where model calls go, which model answered, and how many tools the agent has, and it flashes when any of them change.

## What you need

- **A CData Connect AI account.** A [free trial](https://www.cdata.com/ai/?utm_source=github&utm_medium=readme&utm_campaign=connect-ai&utm_content=connect-ai-gateway-demo) works.
- **A Connect AI personal access token (PAT)**, from **Settings** > **Access Tokens** ([how](https://docs.cloud.cdata.com/en/Settings/Personal-Access-Tokens)).
- **An Anthropic API key**, from the [Anthropic console](https://console.anthropic.com/settings/keys).
- **A Postgres database that Connect AI can reach** for the sample data, such as a free Neon or Supabase project. Any connection works for steps 1, 2, 3, and 5; step 4 needs data with Social Security and card numbers in it, which the sample data has.
- **[Docker](https://docs.docker.com/get-started/get-docker/)** ([no Docker on your Mac?](#no-docker-on-your-mac)).

## Set up

### 1. Load the sample data

[`sample-data/customers.sql`](sample-data/customers.sql) creates a `customers` table of 50 made-up people, each with a city, a lifetime value, a Social Security number, and a credit card number. The names and SSNs are random, and the card numbers are the card networks' published test numbers. A CSV copy is next to it if you'd rather import it another way.

```bash
psql "postgresql://<user>:<password>@<host>/<database>" -f sample-data/customers.sql
```

Then add the database to Connect AI: open **Sources**, add a PostgreSQL connection with the same host and credentials, and save and test it. The connection name is what the agent sees as the catalog, so a short one such as `DemoCustomers` reads well in the chat.

Use a workspace you can experiment in. Step 5 changes your own permissions on this connection.

### 2. Start the agent

```bash
git clone https://github.com/CDataSoftware/connect-ai-gateway-demo.git
cd connect-ai-gateway-demo
cp .env.example .env    # fill in CDATA_USERNAME, CDATA_PAT, and ANTHROPIC_API_KEY
docker compose up
```

Open <http://localhost:8000>. The first start takes about 20 seconds to build. Later starts take a few seconds. If startup fails, the log's `Startup failed:` line names the variable to fix.

### 3. Create an LLM Gateway project (for step 2)

In Connect AI, set up the gateway the agent will switch to:

1. Add your Anthropic key as a provider.
2. Under **Routing** > **Routing Rules**, create a rule. Priority failover from `claude-sonnet-5-5` to `claude-haiku-5-5` shows failover well.
3. Under **Projects**, create a project that uses the rule. Give it a small monthly budget, such as $25, with a hard limit.
4. On the project's **Virtual Keys** tab, create a key. It starts with `cgw_`. Keep it handy; you'll paste it in step 2.

## Walk through it

Keep `.env` open in an editor next to the chat page. Each step is a save, and the header picks it up without a restart.

### Step 1: The ungoverned agent

Ask a question about your data:

> Which five customers in DemoCustomers have the highest lifetime value? Show their name, city, and lifetime value.

Then ask for the sensitive columns:

> Select the customer ID, full name, SSN, and credit card from the customers table in DemoCustomers for customer 1004, and show me exactly what the query returns.

Both come back in full. Click the **Tools** pill in the header: the agent has 13 tools, including three that write.

### Step 2: Route model calls through the gateway

In `.env`, comment out the first `ANTHROPIC_API_KEY`, uncomment `ANTHROPIC_BASE_URL` and the second `ANTHROPIC_API_KEY`, paste your virtual key, and save. The header's LLM pill switches to **Connect AI LLM Gateway, virtual key**.

Ask the top-customers question again. You get the same answer from the same code. In Connect AI, open **Logs**, then **LLM Logs**: the call is there with tokens, cost, latency, and your user, and the model requested sits next to the model the routing rule served. The project shows what you've spent against the budget.

### Step 3: Make the agent read-only

Uncomment `CDATA_MCP_URL` and save. Click the **Tools** pill again: 13 tools become six, and the write tools are gone. Ask the agent to delete customer 1004; it no longer has a tool that can.

### Step 4: Mask Social Security and card numbers

In Connect AI, open **Data Security**, turn on the **US Social Security Number** and **Credit Card Number** rules, and save. Ask the customer 1004 question again. The SSN and card come back as `XXXX`.

The table still stores the real values. Connect AI masks query results on the way out. The model receives `XXXX`, and any other agent or tool that queries this workspace gets the same masked values.

### Step 5: Scope access to the user

The agent signs in to Connect AI with your username and PAT, so it gets exactly your access. Open **Sources**, open your connection, go to **Permissions**, uncheck **Select** on your own row, and save. Ask the top-customers question again: the agent can't find the data.

Check **Select** again when you're done.

## Clean up

- Turn the Data Security rules back off if other people use the workspace and don't expect masking.
- Delete the gateway project, routing rule, and virtual key if you made them only for this.
- Revoke the PAT and Anthropic key if you created them for this, and `docker compose down -v` to remove the containers and conversation history.

**Keep keys off your screen.** `.env` holds a live provider key and a virtual key in plain text. If you record or share your screen while you try this, scroll the keys out of view, and revoke any key that shows up in a recording.

## How it works

| Piece | What it does |
| --- | --- |
| `app/agent.py` | Builds the agent: Connect AI's MCP tools, the model from `LLM_MODEL`, and a cap on tool output so a large table listing can't overflow the context window |
| `app/live.py` | Watches `.env`, rebuilds the agent when it changes, and reports the live route, model, and tool scope to the header |
| `app/main.py` | The API (`/chat`, `/chat/stream`, `/tools`, `/status`, `/healthz`) and the chat page |
| `app/static/` | The chat page: live steps, the SQL behind each answer, and follow-up suggestions |
| Postgres | Conversation history, so chats survive restarts. The app deletes conversations idle for 30 days |

The routing rule, not the request, decides which model answers: `LLM_MODEL` becomes a label, and `/status` reports the model that was actually served. The gateway also accepts the OpenAI SDK at the same URL, so an agent written for OpenAI moves over with the same two-line change (`OPENAI_BASE_URL` and `OPENAI_API_KEY`, with `LLM_MODEL=openai:<model>`).

Through the gateway, every model response also includes budget headers (`x-project-budget-limit-usd`, `-used-usd`, `-remaining-usd`, and `-period`), so an app can see a hard limit coming before it hits.

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
| The agent declines to query the SSN or card columns | The model is being careful, which hides what the platform does. Ask for the exact query and its raw result, as in the step 1 question. |
| The SSN or card still shows after you turn on the rules | Check that you saved on **Data Security**, then ask again; rules apply from the next query. |
| `port is already allocated` | Set `AGENT_PORT` or `DB_PORT` in `.env`, for example `DB_PORT=5433`. |

## License

[MIT](LICENSE) © CData Software, Inc. The CData name and logos are trademarks of CData Software and aren't covered by the license; see [app/static/brand](app/static/brand/README.md).

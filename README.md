# Connect AI Gateway Demo

A sample AI agent that answers questions about your business data through CData Connect AI, with each layer of governance a configuration change away. Route its model calls through the Connect AI LLM Gateway, limit it to read-only tools, mask sensitive values, and scope its access to the signed-in user, without changing the agent's code.

The agent is a LangGraph loop over Connect AI's remote MCP server. A chat page shows each tool call and the SQL behind every answer, and the header shows where model calls go, which model answered, and how many tools the agent has.

## What you can do with it

| Control | Where you set it | What it does |
| --- | --- | --- |
| [LLM Gateway](#send-model-calls-through-the-llm-gateway) | `ANTHROPIC_BASE_URL` and a virtual key in `.env` | Logs every model call with tokens, cost, latency, and user; picks the model and fails over with a routing rule; enforces a monthly budget; replaces the provider key with one you can revoke on its own |
| [Read-only tools](#limit-the-agent-to-read-only-tools) | `CDATA_MCP_URL` in `.env` | Removes the MCP tools that insert, update, or run stored procedures |
| [Data masking](#mask-sensitive-data) | **Data Security** in Connect AI | Replaces Social Security and credit card numbers with `XXXX` in query results before the model receives them |
| [Per-user access](#scope-access-to-the-user) | The connection's **Permissions** tab in Connect AI | Limits the agent to what the signed-in user can query |

The app watches `.env` and picks up changes within about a second, so you can try each control while the agent is running.

## What you need

- **A CData Connect AI account.** A [free trial](https://www.cdata.com/ai/?utm_source=github&utm_medium=readme&utm_campaign=connect-ai&utm_content=connect-ai-gateway-demo) works.
- **A Connect AI personal access token (PAT)**, from **Settings** > **Access Tokens** ([how](https://docs.cloud.cdata.com/en/Settings/Personal-Access-Tokens)).
- **An Anthropic API key**, from the [Anthropic console](https://console.anthropic.com/settings/keys).
- **At least one connection in Connect AI.** To try data masking, use the [sample data](#try-it-with-the-sample-data).
- **[Docker](https://docs.docker.com/get-started/get-docker/)** ([no Docker on your Mac?](#no-docker-on-your-mac)).

## Quick start

```bash
git clone https://github.com/CDataSoftware/connect-ai-gateway-demo.git
cd connect-ai-gateway-demo
cp .env.example .env    # fill in CDATA_USERNAME, CDATA_PAT, and ANTHROPIC_API_KEY
docker compose up
```

Open <http://localhost:8000> and ask about your data, for example "What data sources can you reach?" The first start takes about 20 seconds to build. If startup fails, the log's `Startup failed:` line names the variable to fix.

Out of the box, the agent calls Anthropic directly with your provider key and has all 13 of Connect AI's MCP tools, including `execute_insert`, `execute_update`, and `executeProcedure`. Click the **Tools** pill in the header to see them.

## Try it with the sample data

[`sample-data/customers.sql`](sample-data/customers.sql) creates a `customers` table of 50 made-up people, each with a city, a lifetime value, a Social Security number, and a credit card number. The names and SSNs are random, and the card numbers are the card networks' published test numbers. A CSV copy is next to it.

Load it into any Postgres database Connect AI can reach, such as a free Neon or Supabase project:

```bash
psql "postgresql://<user>:<password>@<host>/<database>" -f sample-data/customers.sql
```

Then in Connect AI, open **Sources** and add a PostgreSQL connection to that database. The agent sees the connection name as the catalog; the questions below assume `DemoCustomers`.

> Which five customers in DemoCustomers have the highest lifetime value? Show their name, city, and lifetime value.

> Select the customer ID, full name, SSN, and credit card from the customers table in DemoCustomers for customer 1004, and show me exactly what the query returns.

## Govern the agent

Each control below is independent. Use any of them, in any order.

### Send model calls through the LLM Gateway

The LLM Gateway sits between the agent and the model provider. Your provider key stays in Connect AI, and the agent gets a virtual key instead.

1. In Connect AI, add your Anthropic key as a provider.
2. Under **Routing** > **Routing Rules**, create a rule, for example priority failover from `claude-sonnet-5-5` to `claude-haiku-5-5`.
3. Under **Projects**, create a project that uses the rule, and set a monthly budget.
4. On the project's **Virtual Keys** tab, create a key. It starts with `cgw_`.
5. In `.env`, comment out the first `ANTHROPIC_API_KEY`, uncomment `ANTHROPIC_BASE_URL` and the second `ANTHROPIC_API_KEY`, and paste the virtual key.

The header's LLM pill changes to **Connect AI LLM Gateway, virtual key**. Ask a question, then open **Logs** > **LLM Logs** in Connect AI to see the call with its tokens, cost, latency, and user, and the model the routing rule served.

The routing rule, not the request, decides which model answers, so `LLM_MODEL` becomes a label and `/status` reports the model actually served. Every response also includes budget headers (`x-project-budget-limit-usd`, `-used-usd`, `-remaining-usd`, and `-period`). The gateway accepts the OpenAI SDK at the same URL: set `OPENAI_BASE_URL`, `OPENAI_API_KEY`, and `LLM_MODEL=openai:<model>` instead.

### Limit the agent to read-only tools

Uncomment `CDATA_MCP_URL` in `.env`. Its `?ops=` parameter lists the six tools that read: `get_catalogs`, `get_schemas`, `get_tables`, `get_columns`, `get_instructions`, and `queryData`. The **Tools** pill drops from 13 to six, and the agent has no tool that can insert, update, or run a stored procedure.

### Mask sensitive data

In Connect AI, open **Data Security**, turn on the **US Social Security Number** and **Credit Card Number** rules, and save. With the sample data, ask the customer 1004 question again: the SSN and card come back as `XXXX`.

Connect AI masks query results on the way out. The model receives `XXXX`, and the database keeps the real values. The rules apply to every query in the workspace, from any agent or tool. They don't apply to text typed into a prompt.

### Scope access to the user

The agent signs in to Connect AI with your username and PAT, so it gets your access and nothing more. Each connection's **Permissions** tab sets Select, Insert, Update, Delete, and Execute per user. Uncheck **Select** on your own row and save, and the agent can no longer see that connection on its next question.

Check **Select** again afterward, especially on a shared connection. In production, give each user or service its own PAT so the agent inherits the right person's permissions.

## How it works

| Piece | What it does |
| --- | --- |
| `app/agent.py` | Builds the agent: Connect AI's MCP tools, the model from `LLM_MODEL`, and a cap on tool output so a large table listing can't overflow the context window |
| `app/live.py` | Watches `.env`, rebuilds the agent when it changes, and reports the live route, model, and tool scope to the header |
| `app/main.py` | The API (`/chat`, `/chat/stream`, `/tools`, `/status`, `/healthz`) and the chat page |
| `app/static/` | The chat page: live steps, the SQL behind each answer, and follow-up suggestions |
| Postgres | Conversation history, so chats survive restarts. The app deletes conversations idle for 30 days |

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
| The agent declines to query the SSN or card columns | The model is being careful, which hides what the platform does. Ask for the exact query and its raw result, as in the sample questions. |
| The SSN or card still shows after you turn on the rules | Check that you saved on **Data Security**, then ask again; rules apply from the next query. |
| `port is already allocated` | Set `AGENT_PORT` or `DB_PORT` in `.env`, for example `DB_PORT=5433`. |

## License

[MIT](LICENSE) © CData Software, Inc. The CData name and logos are trademarks of CData Software and aren't covered by the license; see [app/static/brand](app/static/brand/README.md).

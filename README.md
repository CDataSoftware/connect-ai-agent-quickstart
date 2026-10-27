# Connect AI Agent Quickstart

A sample AI agent that answers questions about your business data through CData Connect AI, with each layer of governance a configuration change away. Route its model calls through the Connect AI LLM Gateway, limit it to read-only tools, mask sensitive values, and scope its access to the signed-in user, without changing the agent's code.

![The chat page answering a question about a customer, with the SSN and card number masked as XXXX and the SQL query shown under the answer](docs/chat.png)

| Control | Where you set it | What it does |
| --- | --- | --- |
| LLM Gateway | A virtual key in `.env` | Logs every model call with tokens, cost, and user; routes and fails over between models; enforces a budget; keeps provider keys out of the app |
| Read-only tools | One line in `.env` | Removes the MCP tools that insert, update, or run stored procedures |
| Data masking | **Data Security** in Connect AI | Replaces Social Security and credit card numbers with `XXXX` before the model sees them |
| Per-user access | The connection's **Permissions** tab | Limits the agent to what the signed-in user can query |

## Before you start

- A CData Connect AI account. A [free trial](https://www.cdata.com/ai/?utm_source=github&utm_medium=readme&utm_campaign=connect-ai&utm_content=connect-ai-agent-quickstart) works.
- A Connect AI [personal access token](https://docs.cloud.cdata.com/en/Settings/Personal-Access-Tokens) (**Settings** > **Access Tokens**).
- [Docker](https://docs.docker.com/get-started/get-docker/). On a Mac without Docker Desktop, `brew install colima docker docker-compose && colima start` works.

You don't need a model provider key. The agent's model calls go through the Connect AI LLM Gateway with a virtual key.

## Quick start

### 1. Add the sample data

[`sample-data/customers.csv`](sample-data/customers.csv) holds 50 made-up customers with Social Security numbers and test credit card numbers. Connect AI reads it straight from GitHub, so there's no database to set up.

In Connect AI, open **Sources**, add a **CSV** connection named `DemoCustomers`, set **URI** to this URL, change **Connection Type** to **HTTPS** (it defaults to Amazon S3), and click **Save & Test**:

```text
https://raw.githubusercontent.com/CDataSoftware/connect-ai-agent-quickstart/main/sample-data/customers.csv
```

### 2. Get a virtual key

In Connect AI, open **Routing**, go to the **Virtual Keys** tab, and click **Issue Virtual Key** for a project. The key starts with `cgw_`. If there's no project yet, create one on the **Projects** tab; its routing rule decides which model answers.

### 3. Start the agent

```bash
git clone https://github.com/CDataSoftware/connect-ai-agent-quickstart.git
cd connect-ai-agent-quickstart
cp .env.example .env
```

In `.env`, set `CDATA_USERNAME` to your Connect AI login email, `CDATA_PAT` to your token, and `ANTHROPIC_API_KEY` to the virtual key. Then:

```bash
docker compose up
```

### 4. Ask a question

Open <http://localhost:8000> and ask:

> Select the customer ID, full name, SSN, and credit card for customer 1004 in DemoCustomers, and show me exactly what the query returns.

The agent finds the table, writes the SQL, and shows the query under its answer. The header shows the call going through the **Connect AI LLM Gateway**. In Connect AI, open **Logs** > **LLM Logs** to see the call with its tokens, cost, and model.

## Next steps

The agent picks up `.env` changes within a second, so you can add each control while it runs:

- **Read-only tools:** uncomment `CDATA_MCP_URL` in `.env`. **Tools** in the header drops from 13 to six, all of them reads.
- **Data masking:** in **Data Security**, turn on **US Social Security Number** and **Credit Card Number**. Ask again and both come back as `XXXX`.
- **Per-user access:** on the `DemoCustomers` connection's **Permissions** tab, uncheck **Select** on your row. The agent signs in as you, so it loses access too.

## Troubleshooting

| Problem | Fix |
| --- | --- |
| `Startup failed:` in the log | The rest of the line says which setting to fix. Fix it in `.env` and run `docker compose restart agent`. Edits only reload live once the agent has started. |
| `Connect AI rejected the credentials (HTTP 401)` | `CDATA_USERNAME` must be your login email and `CDATA_PAT` a current token. |
| `The LLM provider rejected the API key` | The virtual key is wrong or revoked. Issue a new one on **Routing** > **Virtual Keys**. |
| The header shows **Reload failed, see logs** | `docker compose logs agent` shows why the new `.env` didn't load. The previous settings stay active. |
| The agent won't query the SSN or card columns | Ask for the exact query and its raw result, as in step 4. |
| `port is already allocated` | Set `AGENT_PORT` or `DB_PORT` in `.env`. |

To change the code or run the tests, see [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE) © CData Software, Inc. The CData name and logos are trademarks of CData Software and aren't covered by the license.

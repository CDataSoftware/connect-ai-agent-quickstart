# Security policy

This demo gives an AI agent live access to enterprise data, so reports about it get a close look.

## Reporting a vulnerability

**Don't open a public issue.** Report it privately instead:

1. Go to this repository's **Security** tab.
2. Click **Report a vulnerability** ([how private reporting works](https://docs.github.com/en/code-security/how-tos/report-and-fix-vulnerabilities/report-privately)).
3. Describe the issue, how to reproduce it, and what an attacker could do.

Expect an acknowledgment within five business days. Fixes are merged to `main`.

## In scope

Problems in this repository's code and configuration, such as:

- Reaching `/chat`, `/tools`, or `/demo/stage` on a reachable service without `APP_API_KEY`
- The chat page rendering attacker-controlled HTML or script
- Credentials leaking into logs, error messages, API responses, the header, or `demo/stage.py` output
- A `compose.yaml` default that exposes a service or secret

## Out of scope

- **CData Connect AI itself**, including its MCP server, LLM Gateway, and API. Report those to CData through [Connect AI support](https://docs.cloud.cdata.com).
- **Your LLM provider** or other third-party services.
- **Prompt injection that stays within the agent's permissions.** The agent can do whatever its Connect AI user can; limit that with read-only tools and the connection's per-user permissions, as the demo shows.

## If you leaked a credential

Revoke it first, then clean up:

- **Connect AI PAT:** delete it under **Settings** > **Access Tokens** in Connect AI, create a new one, and update `CDATA_PAT` in `.env`.
- **LLM Gateway virtual key:** revoke it on the project's **Virtual Keys** tab and issue a new one. The provider key behind it stays private.
- **LLM provider key:** revoke it in your provider's console.

Treat a key that appeared in a screen recording or screenshot as leaked. Removing a secret from git history or blurring it in a video edit doesn't un-leak it. Revoke anything you published.

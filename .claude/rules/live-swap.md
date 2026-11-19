---
paths:
  - "app/live.py"
  - "app/config.py"
  - "compose.yaml"
---

# How the live swap works

compose mounts the project at `/workspace`. `app/live.py` polls `/workspace/.env` every 0.5 s by content hash (file events don't cross Colima's VM boundary, and editors that replace the file can leave the mtime unchanged through a mount), waits 0.3 s for the save to finish, applies the file to `os.environ`, and builds a new agent. Requests already running finish on the agent they started with. A bad edit keeps the old agent and sets `live_error`, which the header shows as **Reload failed, see logs**.

- Variables compose sets under `environment:` (`DATABASE_URL`, `WATCHFILES_FORCE_POLLING`, `LIVE_WORKSPACE`) are `PINNED` and always win over `.env`.
- A variable removed from `.env` is removed from `os.environ`, so commenting out `ANTHROPIC_BASE_URL` really sends the next call direct.
- The header calls the route "Connect AI LLM Gateway" when the base URL's host is `cloud.cdata.com` and its path starts with `/gateway`, and "virtual key" when the key starts with `cgw_`. It never shows a key, only its kind.
- `/status` reports `served_model`, the model named in the last response's metadata. Through a gateway routing rule it can differ from `LLM_MODEL`.

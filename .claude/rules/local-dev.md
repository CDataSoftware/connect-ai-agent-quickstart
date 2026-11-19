---
paths:
  - "compose.yaml"
  - "Dockerfile"
  - ".env.example"
---

# Local development

- **Docker engine.** Colima (`brew install colima docker docker-compose docker-buildx`), with `"cliPluginsExtraDirs": ["/opt/homebrew/lib/docker/cli-plugins"]` in `~/.docker/config.json`. Colima shares only `$HOME` with its VM: a bind mount from `/tmp` or a scratchpad is silently empty inside the container (`Could not import module "app.main"`).
- **Hot reload** of code relies on `WATCHFILES_FORCE_POLLING`; without it `--reload` never fires on Colima. `.env` changes are picked up by `app/live.py` instead, with no restart.
- **The agent healthcheck** exists because under `--reload` a failed startup leaves the container running. With it, `docker compose ps` says `unhealthy`.
- **Ports** are `AGENT_PORT` (8000) and `DB_PORT` (5432), overridable in `.env`.

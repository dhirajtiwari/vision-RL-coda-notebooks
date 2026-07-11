# 01 — Platform Docker / infra

**Load when:** P0 infra, compose, ports, health, secrets.
**Always-on also required:** `NEVER.md`, `MUST.md`, `OVERRIDES.md`.

## Target topology

| Service | Role | As-built ports (this repo) |
|---------|------|----------------------------|
| Graph **production** | Online diagnose + explorer **read** | Bolt 7687, Browser 7474 |
| Graph **staging** | Promote-first MERGE | Bolt 7688, Browser 7475 |
| Redis (optional) | Shared cache / rate / admission | 6379 |
| API | Control plane + diagnose | 8080 |
| Frontend | Chat + Admin + Explorer | 3000 |
| Mock SoR (optional) | Simulated enterprise APIs | 8090 |

## Must implement

- [ ] Compose starts **both** graphs independently
- [ ] Env separates `NEO4J_URI` (prod) vs `NEO4J_STAGING_URI` (staging)
- [ ] API `/health` green when graphs up
- [ ] Secrets not hardcoded for shared deploys (local demo passwords OK only if labeled)

## As-built map (this repo)

- `docker/docker-compose.infra.yaml`
- `docker/Dockerfile.api`, `Dockerfile.frontend`, `Dockerfile.etl`, `Dockerfile.mock`
- Optional: `docker-compose.redis.yaml`, `docker-compose.observability.yaml`
- Settings: `config/settings.py`

## Exit (P0)

Health green; both graphs respond; no chat path pointed at staging.

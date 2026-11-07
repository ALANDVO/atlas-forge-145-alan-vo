# Product development plan

Each round completes one feature or repair. Future items are planned, not implemented claims.

## Current round

project-skeleton

## Roadmap

### project-skeleton — Project skeleton: FastAPI backend + React/Vite frontend + Docker compose

Status: done

Acceptance:
- Backend runs with FastAPI and health endpoint
- Frontend builds with Vite + TypeScript + React
- Docker compose starts both services + Keycloak
- Basic pytest and vitest tests pass

Implementation: `backend/app/main.py`, `backend/app/api/health.py`, `backend/app/api/media.py`, `backend/app/core/config.py`, `frontend/src/App.tsx`, `frontend/src/main.tsx`, `frontend/vite.config.ts`, `docker-compose.yaml`, `backend/requirements.txt`, `frontend/package.json`

Tests: `backend/app/tests/test_main.py`, `frontend/src/App.test.tsx`

### oidc-auth — OIDC authentication with Keycloak (authorization code + PKCE)

Status: planned

Acceptance:
- Login redirects to Keycloak
- Callback exchanges code for tokens with PKCE
- Access token used for authenticated API calls
- Logout clears session
- Tests cover unauthenticated rejection and role denial

### media-range-server — Bounded media range responses (fixes connection starvation)

Status: done

Acceptance:
- Open-ended Range requests capped at 4 MB
- Content-Range header correct
- Video playback works with seeking
- Multiple video elements don't starve connections

Implementation: `backend/app/api/media.py`, `backend/app/core/config.py`

Tests: `backend/app/tests/test_main.py`

### llm-adapters — LLM provider adapters (OpenAI-compatible, Anthropic, Gemini, Ollama)

Status: planned

Acceptance:
- Each adapter implements common interface
- Configurable via env vars
- Errors are redacted
- CI mocks external calls

---

Alan Vo · [alanvo.net](https://alanvo.net) · [X: @alanvoasi](https://x.com/alanvoasi)

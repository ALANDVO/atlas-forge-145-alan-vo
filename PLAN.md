# Product development plan

Each round completes one feature or repair. Future items are planned, not implemented claims.

## Current round

project-skeleton

## Roadmap

### project-skeleton — Project skeleton: FastAPI backend + React/Vite frontend + Docker compose

Status: in_progress

Acceptance:
- Backend runs with FastAPI and health endpoint
- Frontend builds with Vite + TypeScript + React
- Docker compose starts both services + Keycloak
- Basic pytest and vitest tests pass

### oidc-auth — OIDC authentication with Keycloak (authorization code + PKCE)

Status: planned

Acceptance:
- Login redirects to Keycloak
- Callback exchanges code for tokens with PKCE
- Access token used for authenticated API calls
- Logout clears session
- Tests cover unauthenticated rejection and role denial

### media-range-server — Bounded media range responses (fixes connection starvation)

Status: planned

Acceptance:
- Open-ended Range requests capped at 4 MB
- Content-Range header correct
- Video playback works with seeking
- Multiple video elements don't starve connections

### llm-adapters — LLM provider adapters (OpenAI-compatible, Anthropic, Gemini, Ollama)

Status: planned

Acceptance:
- Each adapter implements common interface
- Configurable via env vars
- Errors are redacted
- CI mocks external calls


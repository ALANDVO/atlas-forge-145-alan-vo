# Changelog

## 1.0.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-10-24

### Added
- Project skeleton with FastAPI backend and React/Vite frontend
- Bounded media range server (fixes connection starvation from hyperframes#6029)
  - Open-ended `Range: bytes=N-` requests capped at 4 MB (configurable)
  - Suffix ranges `Range: bytes=-N` supported
  - Bounded ranges `Range: bytes=N-M` supported
  - Proper `206 Partial Content` with `Content-Range` headers
- Health check endpoint (`GET /api/health`)
- Docker Compose with backend, frontend (nginx), and Keycloak
- Keycloak realm export with admin/analyst/viewer roles and test users
- Backend tests with pytest (health, media range parsing, capped ranges)
- Frontend tests with vitest + React Testing Library
- Responsive UI with service health display and feature overview
- Configuration via environment variables with .env.example
- MIT License and comprehensive README

### Security
- Non-root Docker users
- Healthchecks on all services
- CORS restricted to configured origins
- Secrets via environment variables only

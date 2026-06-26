# Changelog

## [0.2.0] — 2026-06

### Added
- YAML-driven configuration (`start_from_config`)
- CLI (`edge_framework.cli`)
- InstrumentMapper (broker-agnostic symbols)
- Shadow connectors (EdgeFix, Demo2)
- FastAPI status API (`/health`, `/status`, `/metrics`)
- Docker + docker-compose
- 5 strategy examples
- Landing page, beta onboarding docs, billing/Stripe scaffolding

### Changed
- Paper connector: dynamic symbol pricing (no hardcoded symbols)

## [0.1.0] — 2026-06

### Added
- Initial ExecutionEngine, RiskManager, AuditLogger
- MT5, Topstep, Paper connectors
- Core trading loop
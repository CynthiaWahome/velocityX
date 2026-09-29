# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-09-29

### Added
- Externalized accounts pool to [`velocityx/accounts.json`](velocityx/accounts.json) for easy customization across multiple domains without touching code.
- Customizing for Your Niche guide in documentation covering target accounts, algorithmic multipliers, and reply tone.
- Comprehensive 61-test suite verifying database idempotency, error recovery, network retries, and prompt parsing.
- Support for modern `uv` workflow and Hatchling build backend.
- High-throughput Groq LPU reasoning layer generating context-aware reply suggestions via hardware-accelerated LLaMA 3.3 70B inference.

### Changed
- Rebranded engine and package identity to **VelocityX** (`velocityx`).
- Aligned scoring heuristics, recency multipliers, and architecture documentation with modern recommendation patterns (`xai-org/x-algorithm`).
- Switched default LLM inference model to `llama-3.3-70b-versatile`.
- Replaced legacy console logs and Telegram notification headers with VelocityX branding.

### Removed
- Deprecated legacy hardcoded target account arrays in source files.
- Removed throwaway diagnostic scripts and stale developer notes.

---

## [0.1.0] - 2026-04-12

### Added
- Initial proof-of-concept ingestion pipeline reading public Google News RSS feeds.
- SQLite deduplication ledger preventing redundant alert notifications.
- Rule-based opportunity scoring using recency multipliers and engagement weights.
- Telegram notification dispatcher with inline action links.

# ROADMAP.md — OrbitFlow Future Work

This file contains future ideas and is not a permanent instruction set.

Items here are not automatically approved implementation tasks. Move an item into an explicit task before Codex implements it.

## Potential Enhancements

- Store daily snapshots in MySQL or PostgreSQL.
- Build a web dashboard for interface changes.
- Add device grouping by region/site.
- Add email reporting for daily changes.
- Add Git-based snapshots of collected raw outputs.
- Add NMS inventory integration.
- Add topology mapping based on LLDP/CDP.
- Add controlled rollback execution only after provisioning has sufficient field testing.
- Add optional RAG/LLM summaries only after deterministic structured parsing is complete.
- Add database-backed history while preserving Excel workflows where still required.
- Add additional inventory sources only through an explicit approved architecture change.
- Expand transport/session abstraction so collectors and provisioners share one stable device-session API.
- Add credential-provider abstraction suitable for both Windows and Linux.
- Add additional vendor/platform skills as OrbitFlow scope grows.

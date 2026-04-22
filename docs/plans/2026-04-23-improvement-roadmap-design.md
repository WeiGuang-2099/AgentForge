# AgentForge Improvement Roadmap Design

**Date**: 2026-04-23
**Status**: Approved
**Strategy**: Feature-first, then hardening (functionality before infrastructure)
**Goal**: Production-ready multi-agent collaboration platform

---

## Overview

6-phase improvement plan for AgentForge. Each phase delivers a complete, demonstrable feature set. Phases 1-4 focus on functionality, Phases 5-6 on security, testing, and deployment.

## Current State Summary

- 50 Python files, 32 TS/TSX files
- Architecture is well-designed but implementation is incomplete
- Key gaps: memory system missing, data persistence broken, zero tests, security vulnerabilities
- README overstates completion status

---

## Phase 1: Data Persistence

**Goal**: All API endpoints return real data, no more empty lists or hardcoded values.

### Tasks

| # | Task | Description |
|---|------|-------------|
| 1.1 | Conversation persistence | Write `Conversation`/`Message` to DB, wire chat router CRUD to database |
| 1.2 | Usage statistics writes | After each LLM call, write `UsageRecord` (tokens, model, latency) |
| 1.3 | Audit log writes | Add middleware/decorator to auto-record sensitive operations to `AuditLog` |
| 1.4 | Auth persistence | User registration/login writes to `User` table, JWT signing/verification uses DB |
| 1.5 | Database migrations | Alembic scripts to create all tables and seed initial data |

### Acceptance Criteria
- All API endpoints return real data from the database
- No endpoint returns hardcoded empty lists
- Alembic migrations run cleanly on a fresh database

---

## Phase 2: Memory System

**Goal**: Agent possesses cross-session memory with short-term context and long-term semantic recall.

### Architecture

```
MemoryManager
  +-- ShortTermMemory     (DB-based conversation context window)
  |     +-- Last N messages per conversation_id
  |
  +-- LongTermMemory      (ChromaDB semantic memory)
        +-- Per-user/Agent isolated collections
        +-- Auto-archive conversation summaries (every N turns)
        +-- Semantic retrieval on new conversation start
```

### Tasks

| # | Task | Description |
|---|------|-------------|
| 2.1 | ShortTermMemory | Query last N messages as context, inject into prompt |
| 2.2 | LongTermMemory (ChromaDB) | Init collections, embedding storage, semantic search |
| 2.3 | Memory injection hook | Before Agent runs, auto-retrieve relevant memory and inject into system_prompt |
| 2.4 | Summary generation | Periodically summarize conversations and write to long-term memory |
| 2.5 | Memory management API | CRUD endpoints for clearing/exporting/viewing memories |

### Acceptance Criteria
- Agent "remembers" key information across sessions
- New conversations can recall relevant history semantically
- Memory management API fully functional

---

## Phase 3: Workflow Visual Editor

**Goal**: Drag-and-drop workflow orchestration using reactflow, replacing hardcoded role mappings.

### Architecture

```
Frontend (WorkflowEditor)
  +-- Node panel: Agent nodes, condition nodes, input/output nodes
  +-- Canvas: reactflow drag-and-drop
  +-- Properties panel: Selected node config (Agent, prompt, tools)
  +-- Serialization: Save/load workflow JSON

Backend (WorkflowEngine refactor)
  +-- Workflow model: WorkflowStep (nodes) + WorkflowEdge (edges)
  +-- Dynamic executor: Parse DAG from JSON, topological sort execution
  +-- Conditional branching: Support if/else node routing
```

### Tasks

| # | Task | Description |
|---|------|-------------|
| 3.1 | WorkflowEditor component | reactflow canvas + node panel + properties panel |
| 3.2 | Workflow CRUD API | Create/save/list/delete/execute workflows |
| 3.3 | Dynamic DAG executor | Replace hardcoded role mapping, parse JSON config |
| 3.4 | Conditional branch nodes | Support if/else routing in workflow |
| 3.5 | Preset workflow templates | Dev Team, content pipeline, etc. |
| 3.6 | Workflow list page | Select templates, manage custom workflows |

### Acceptance Criteria
- Users can drag-and-drop to create workflows in the UI
- Saved workflows can be executed end-to-end
- Conditional branching works correctly

---

## Phase 4: Custom Skill Upload + Plugin System

**Goal**: Users can upload custom Skills (tools), plugin system is fully functional.

### Skill Upload Flow

```
1. User uploads .py file + metadata (name, description, parameters)
2. Backend validates: AST check for security (ban os, subprocess, etc.)
3. Sandbox test: Execute once in isolated environment, verify return format
4. Register: Save to Skill table, dynamically load into ToolRegistry
5. Associate: User selects available Skills in Agent config
```

### Tasks

| # | Task | Description |
|---|------|-------------|
| 4.1 | Skill upload API | File upload + AST security validation + sandbox verification |
| 4.2 | Skill storage | Database storage + filesystem cache |
| 4.3 | Dynamic loading | Runtime load user Skills into ToolRegistry |
| 4.4 | AgentPlugin completion | Implement activate/deactivate lifecycle hooks |
| 4.5 | Plugin config UI | Frontend Skill management page (upload, list, toggle) |
| 4.6 | Marketplace integration | Display user-shared Skills in marketplace |

### Acceptance Criteria
- Users can upload .py tool files
- Files pass security validation before registration
- Uploaded Skills are usable in Agent conversations

---

## Phase 5: Security Hardening + Test Coverage

**Goal**: Fix all security vulnerabilities, establish comprehensive test suite.

### Security Tasks

| # | Task | Description |
|---|------|-------------|
| 5.1 | CORS fix | Restrict allowed origins from config, remove `*` wildcard |
| 5.2 | JWT secret enforcement | Reject default secret at startup, require configuration |
| 5.3 | Code sandbox hardening | Docker container/nsjail isolation, resource limits |
| 5.4 | Skill upload security | AST check + sandbox execution + module whitelist |
| 5.5 | API Key validation | Strengthen format checks beyond length > 10 |
| 5.6 | Path traversal fix | Fix file tool path validation for all platforms |
| 5.7 | Secret management | K8s secrets via SealedSecret or external vault |

### Test Coverage Targets

| Layer | Coverage | Scope |
|-------|----------|-------|
| Unit tests | Core modules 80%+ | Agent engine, tools, memory, workflow |
| Integration tests | API endpoints 70%+ | All route CRUD + auth flows |
| Security tests | Critical items 100% | Auth bypass, injection, path traversal, sandbox escape |
| E2E tests | Core flows | Chat -> tool call -> workflow execution |

### Acceptance Criteria
- CI pipeline includes test stage
- All PRs must pass test suite
- No critical/high security findings

---

## Phase 6: Deployment Optimization + Documentation

**Goal**: Production-grade deployment config, accurate documentation.

### Deployment Tasks

| # | Task | Description |
|---|------|-------------|
| 6.1 | Dockerfile optimization | Multi-stage build, non-root user, remove --reload |
| 6.2 | docker-compose hardening | Health checks, externalize env vars, no hardcoded passwords |
| 6.3 | Next.js API proxy | Configure rewrite rules for dev environment proxy to backend |
| 6.4 | Nginx config | Production reverse proxy + SSL |
| 6.5 | Redis integration | Cache LLM responses, session storage, rate limiting |
| 6.6 | Monitoring | Structured logging + Prometheus metrics |

### Documentation Tasks

| # | Task | Description |
|---|------|-------------|
| 6.7 | README status correction | Accurately mark feature completion status |
| 6.8 | API documentation | Auto-generated OpenAPI/Swagger docs |
| 6.9 | Contributing guide | Dev setup, code standards, PR process |
| 6.10 | Changelog | CHANGELOG.md for version tracking |

### Acceptance Criteria
- `docker-compose up` launches complete production environment
- Documentation accurately reflects feature status
- API docs auto-generated and accessible

---

## Roadmap Summary

```
Phase 1: Data Persistence          --> All APIs return real data
Phase 2: Memory System             --> Cross-session agent memory
Phase 3: Workflow Visual Editor    --> Drag-and-drop orchestration
Phase 4: Custom Skill Upload       --> User-extensible tool set
Phase 5: Security + Testing        --> Production security + CI coverage
Phase 6: Deployment + Docs         --> One-command production deploy
```

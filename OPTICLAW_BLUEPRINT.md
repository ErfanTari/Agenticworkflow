# OptiClaw — Ultra-Efficient, Memory-Rich, Meta-Aware AI Assistant

## 1) Product Goals and Non-Negotiable Constraints

OptiClaw is a **local-first, event-driven AI personal assistant runtime** that operates through chat platforms and secure action connectors.

### Hard constraints
- **No heartbeat scheduler** (no periodic wake loops).
- **Zero idle LLM calls**.
- **Idle resource budget target**: `<150MB RAM`, `<5% CPU` on modern laptops.
- **Tiered intelligence routing**: rules/small models first, large models only when needed.
- **Memory discipline**: compression, summarization, and hierarchical retrieval only.
- **Capability-based security** with trust tiers and isolated execution.

---

## 2) System Architecture (Text Diagram)

```text
                    ┌──────────────────────────────────────────────────────────┐
                    │                     Chat Surfaces                        │
                    │ WhatsApp | Telegram | Slack | Discord | Matrix | etc.   │
                    └───────────────┬──────────────────────────────────────────┘
                                    │ inbound webhook/event
                           ┌────────▼────────┐
                           │ Bridge Adapters │
                           │ (per platform)  │
                           └────────┬────────┘
                                    │ normalized event envelope
              ┌─────────────────────▼──────────────────────┐
              │ Event Router + Policy Gate                  │
              │ - auth/session map                          │
              │ - capability pre-check                      │
              │ - idempotency + dedupe                      │
              └─────────────────────┬──────────────────────┘
                                    │
                         ┌──────────▼──────────┐
                         │ Intent Triage Layer │  (cheap path)
                         │ - rule engine       │
                         │ - tiny local model  │
                         │ - toolability score │
                         └───────┬───────┬─────┘
                                 │       │
                          simple reply   needs planning/tooling
                                 │       │
                ┌────────────────▼──┐   ┌▼──────────────────────────────────┐
                │ Fast Response Path │   │ Planner + Meta-Cognitive Engine  │
                │ - cached templates │   │ - task decomposition               │
                │ - memory snippets  │   │ - self-model checks               │
                └──────────┬────────┘   │ - budget-aware model routing      │
                           │            └───────────────┬────────────────────┘
                           │                            │ execution graph
                           │                 ┌──────────▼─────────────────────┐
                           │                 │ Tool Orchestrator (Event-Driven)│
                           │                 │ - capability tokens             │
                           │                 │ - sandbox dispatch              │
                           │                 │ - compensating actions          │
                           │                 └───────┬───────────────┬────────┘
                           │                         │               │
             ┌─────────────▼────────────┐   ┌────────▼───────┐  ┌──▼──────────┐
             │ Memory System             │   │ Connectors      │  │ Code Runtime │
             │ episodic/semantic/proc    │   │ email/calendar  │  │ microVMs for │
             │ vector + graph + cache    │   │ files/APIs      │  │ shell/browser│
             └─────────────┬────────────┘   └────────────────┘  └──────────────┘
                           │
                 ┌─────────▼────────────────┐
                 │ Reflection + Learning     │
                 │ - outcome scoring         │
                 │ - self-model update       │
                 │ - memory compaction       │
                 └─────────┬────────────────┘
                           │
                    ┌──────▼────────┐
                    │ Response Synth │
                    │ + channel fmt  │
                    └──────┬────────┘
                           │ outbound message/event
                    ┌──────▼────────┐
                    │ Bridge Adapter │
                    └───────────────┘
```

---

## 3) Core Runtime Model: Event-Driven + Intelligent Micro-Scheduling

### Why no heartbeat
Instead of polling, OptiClaw uses:
1. **External event triggers** (message webhook, calendar webhook, file watcher, IMAP IDLE push).
2. **Internal completion events** (tool finished, sandbox output available, user approval arrived).
3. **One-shot deferred tasks** via durable timer wheel / delayed queue entries with exact wake timestamps.

### Micro-scheduling design
- Use a **priority event queue** with classes: `user_blocking`, `interactive`, `background`, `maintenance`.
- Deferred tasks are persisted as records `(task_id, wake_at, condition)` and loaded lazily by a low-overhead timer index.
- No periodic scan; storage provides an indexed `wake_at <= now` query on wake signal.
- Backpressure + cancellation tokens prevent zombie execution.

### Runtime states
- `SLEEPING`: no active events; only OS/webhook interrupts.
- `ACTIVE_FASTPATH`: handling cheap triage/reply.
- `ACTIVE_PLAN_EXEC`: multi-step execution graph.
- `WAIT_EXTERNAL`: blocked on OAuth approval/user confirmation/tool callback.

---

## 4) Module Blueprint

## 4.1 Gateway & Bridge Layer
**Responsibilities**
- Native adapters for WhatsApp/Telegram/Slack/Discord/Matrix/iMessage gateways.
- Normalize incoming events into `EventEnvelope`.
- Handle channel-specific constraints (markdown flavor, attachments, rate limits).

**Interfaces**
- `BridgeAdapter.on_event(raw_event) -> EventEnvelope`
- `BridgeAdapter.send(ResponsePacket)`

**Design notes**
- Keep adapters stateless; per-user auth/session in secure store.
- Use signature verification + replay protection.

## 4.2 Event Router + Policy Gate
**Responsibilities**
- Authenticate source/user mapping.
- Enforce tenant + capability policy prechecks.
- Deduplicate event IDs and ensure idempotence.

**Key data objects**
- `EventEnvelope`: channel, user_id, thread_id, content, attachments, metadata.
- `ExecutionContext`: request_id, trust_tier, cost_budget, locale, constraints.

## 4.3 Intent Triage Layer (Cheap Intelligence)
**Pipeline**
1. Deterministic rules (`/help`, `/status`, simple FAQs).
2. Tiny classifier model (intent, urgency, tool-needed probability).
3. Confidence gate.

**Outcome**
- `FAST_REPLY` or `PLAN_AND_EXECUTE`.
- Attach retrieval hints to reduce planner cost.

## 4.4 Planner + Meta-Cognitive Engine
**Subcomponents**
- `GoalDecomposer`: convert user goal into DAG of tasks.
- `SelfModelInspector`: checks capabilities, historical success rates, known failure modes.
- `BudgetRouter`: selects model provider/size based on complexity and budget.
- `RiskAssessor`: determines if approval required.

**Self-Model schema**
- Capabilities matrix (tool + scope + reliability score).
- Failure signatures and mitigation playbooks.
- User preference profile (tone, coding style, workflow habits).
- Current system health and resource profile.

## 4.5 Tool Orchestrator
**Responsibilities**
- Turn task DAG into executable steps.
- Issue short-lived capability tokens.
- Dispatch shell/browser/code tasks to microVMs.
- Handle retries, timeouts, and compensating rollbacks.

**Execution model**
- Event-sourced state machine per task:
  - `planned -> approved -> running -> blocked -> completed|failed|rolled_back`

## 4.6 Memory System (Hierarchical + Hybrid)
**Memory types**
- **Episodic**: time-ordered interaction/action logs.
- **Semantic**: facts/concepts/preferences with confidence.
- **Procedural**: reusable workflows/skills and code patterns.

**Storage tiers**
- L1: in-memory hot cache (recent thread context).
- L2: local KV + SQLite/Postgres for structured records.
- L3: vector index (HNSW/FAISS/Qdrant local) + graph store for entity relations.

**Compression strategy**
- Rolling summaries per thread.
- Multi-resolution context windows (micro/meso/macro summaries).
- Salience scoring and decay-based forgetting with pinning for critical items.

## 4.7 Reflection + Learning Loop
Triggered only on significant completion events.
- Compute outcome score (accuracy, user correction rate, tool success, latency, cost).
- Update self-model reliability metrics.
- Materialize new procedural memory entries when patterns repeat.
- Queue optional offline fine-tuning data package (local only).

## 4.8 Secure Connectors
- Email: IMAP IDLE + SMTP/Gmail API via OAuth scopes.
- Calendar: Google/Microsoft/CalDAV connectors with least-privilege scopes.
- Files: local FS + cloud drives via scoped tokens.
- Browser/API: sandbox-only execution, audited artifacts.

## 4.9 Code Intelligence Runtime
- Repo analyzer (symbol graph, dependency map, test map).
- Patch planner with deterministic diff validation.
- Test selection engine (smallest sufficient subset first).
- Failure-aware iterative debugger.

---

## 5) Data Flow Patterns

## 5.1 Message → Action Flow
1. Webhook event arrives.
2. Policy gate validates + enriches context.
3. Triage chooses fast reply or planner.
4. Planner builds DAG and risk labels.
5. Orchestrator executes tools in sandboxes.
6. Memory updated with compact artifacts.
7. Response synthesized and returned.
8. Reflection updates self-model.

## 5.2 Autonomous Tasks (No Polling)
- Triggered by explicit user instruction, external event stream, or one-shot timer.
- Each autonomous plan has:
  - objective
  - stop conditions
  - max budget/time
  - escalation path for uncertainty.

---

## 6) Code Organization (Monorepo)

```text
opticlaw/
  apps/
    gateway/                 # webhook receivers + bridge adapters
    orchestrator/            # event router, planner, tool orchestration
    desktop/                 # optional local control panel
  packages/
    core-types/              # EventEnvelope, TaskGraph, MemoryRecord
    triage-engine/           # cheap intent + policy checks
    planner-engine/          # decomposition + self-model usage
    memory-engine/           # storage, retrieval, compaction
    model-router/            # local/cloud model abstraction
    connector-email/
    connector-calendar/
    connector-files/
    connector-browser/
    connector-shell/
    skill-runtime/           # markdown + TS/Python skill execution
    security/                # policy, token minting, secret vault APIs
    observability/           # local traces, metrics, replay tools
  sandboxes/
    microvm-runner/          # Firecracker wrappers
    playwright-runner/
  schemas/
    events/
    memory/
    policy/
  infra/
    docker/
    nix/
  docs/
    architecture/
    runbooks/
    threat-model/
```

---

## 7) Canonical Interfaces (Language-Agnostic Contracts)

## 7.1 EventEnvelope
```json
{
  "event_id": "uuid",
  "source": "slack|telegram|...",
  "user_id": "string",
  "thread_id": "string",
  "timestamp": "iso8601",
  "content": {"text": "...", "attachments": []},
  "security": {"signature_valid": true},
  "hints": {"priority": "interactive"}
}
```

## 7.2 TaskGraph
```json
{
  "task_id": "uuid",
  "goal": "string",
  "nodes": [
    {
      "id": "n1",
      "kind": "reason|tool|message|approval",
      "deps": [],
      "policy": {"requires_approval": false},
      "budget": {"max_ms": 10000, "max_cost": 0.02}
    }
  ]
}
```

## 7.3 MemoryRecord
```json
{
  "memory_id": "uuid",
  "type": "episodic|semantic|procedural",
  "content": "...",
  "embedding_ref": "vec://...",
  "entities": ["repo:foo", "person:bar"],
  "salience": 0.84,
  "expires_at": null
}
```

---

## 8) Efficiency Tactics (Concrete)

- **Gate every LLM call** with estimated value function: `expected_gain > cost + latency_penalty`.
- **Speculative cheap answers**: respond quickly, continue deeper reasoning only if user asks follow-up.
- **Context budgeter** selects smallest memory slices that satisfy confidence target.
- **Adaptive model routing**:
  - tiny local model for triage/classification,
  - medium local model for coding and planning,
  - cloud frontier model only for hard cases.
- **Result caching** with semantic cache keys and invalidation on source changes.
- **Lazy connector init**: OAuth clients opened on first use only.

---

## 9) Security Architecture

- Capability tokens are **least privilege + short TTL + audience-bound**.
- Secrets in OS keychain/Vault; never in prompt context.
- Shell/browser execution isolated with network/file policies in microVM.
- All tool actions emit immutable audit events.
- Trust tiers:
  - Tier 0: read-only reasoning.
  - Tier 1: low-risk actions (draft email, local read).
  - Tier 2: side-effect actions requiring user approval.
  - Tier 3: high-risk/financial/admin actions with explicit MFA/approval.

---

## 10) Plugin/Skill System

### Skill package format
- `skill.md`: description, triggers, safety tags.
- `handler.ts` or `handler.py`: deterministic function entrypoint.
- `policy.yaml`: required capabilities/scopes.
- `tests/`: contract tests and malicious-input tests.

### Runtime behavior
- Static scan for dangerous operations.
- Sandboxed execution.
- Capability grant checked per invocation.
- Versioned with rollback support.

---

## 11) Model Routing Strategy

`ModelRouter.select(task)` considers:
- complexity score,
- latency SLO,
- privacy requirement,
- budget cap,
- historical model success by domain.

Output: `{provider, model, max_tokens, temperature, tool_mode}`.

Fallback order: `local-small -> local-medium -> cloud-primary -> cloud-secondary`.

---

## 12) Observability (Local-First)

- OpenTelemetry traces stored locally.
- Per-request timeline showing gates, model calls, tool runs, memory reads/writes.
- “Why this action?” explainer from planner decisions.
- Cost/latency dashboards with anomaly alerts.

No telemetry leaves machine unless user opts in.

---

## 13) Reliability & Failure Handling

- Exactly-once semantics for side-effect actions via idempotency keys.
- Circuit breakers around unstable connectors.
- Compensating transactions (e.g., unsend/label revert where possible).
- Dead-letter queue for failed events with replay UI.

---

## 14) Implementation Roadmap

## Phase 1 — Core Event Runtime
- Build bridge abstraction + one channel (Slack/Telegram).
- Event router + policy gate + triage engine.
- Basic planner + orchestrator with local shell connector.

## Phase 2 — Memory + Meta Layer
- Add hybrid memory stores and summarization pipeline.
- Introduce self-model and reflection updates.
- Add context budgeter and semantic cache.

## Phase 3 — Secure Action Connectors
- Email/calendar/files connectors with OAuth scopes.
- Approval workflows + trust tiers.
- Audit log + replay.

## Phase 4 — Coding Agent Excellence
- Repo symbol graph + patch planner.
- Automated test targeting and iterative debugging.
- Multi-file refactor workflows.

## Phase 5 — Ecosystem
- Plugin/skill SDK.
- Community skill registry (signed manifests).
- Cross-channel continuity.

---

## 15) Minimal Reference Tech Stack

- **Runtime**: TypeScript (Node.js) for orchestration, Rust or Go for high-performance agents.
- **Datastores**: SQLite/Postgres + local vector DB (Qdrant/FAISS) + graph layer.
- **Queue/Eventing**: NATS/Redis streams or embedded durable queue.
- **Sandboxing**: Firecracker/microVM wrapper + seccomp profiles.
- **Model providers**: Ollama/LM Studio local + optional cloud APIs.
- **UI**: Lightweight local dashboard (Svelte/React).

---

## 16) Acceptance Criteria (Definition of Done)

- Idle with no active sessions remains below target CPU/RAM.
- No periodic heartbeat threads present in runtime.
- 95th percentile simple-message latency under defined SLO.
- Memory retrieval precision above target in benchmark tasks.
- Zero unauthorized tool execution in security test suite.
- End-to-end coding task success rate exceeds baseline (OpenClaw/Claude Code benchmark set).

---

## 17) Practical Build Guidelines

1. Start with strict contracts (`EventEnvelope`, `TaskGraph`, `MemoryRecord`) before coding adapters.
2. Keep every module benchmarkable in isolation.
3. Add feature flags for every expensive capability.
4. Require golden traces for critical user journeys.
5. Enforce prompt/context linting to prevent memory bloat.
6. Treat meta-cognition as first-class state, not prompt prose.

This blueprint yields a system that is event-native, compute-frugal, memory-intelligent, and robust enough for real coding + real-world automation while remaining private and extensible.

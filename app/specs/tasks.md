# Implementation Roadmap

## Enterprise HR Policy Assistant — Traced Task Breakdown

| Field | Value |
|---|---|
| Document Type | Implementation Roadmap |
| Project Name | Enterprise HR Policy Assistant |
| Version | 1.0 |
| Status | Draft — Pending Review |
| Purpose | Break the approved specification chain into implementable tasks, each traced back to the specific requirement, contract, domain model, sequence flow, test case, and operational requirement that justifies it. No task exists here without a specification reference; no significant requirement exists without at least one task that implements it. |
| Scope | Every task required to build, test, and operationally ready the Phase 1–3 system already scoped in `rag_design.md` §10. Phase 4 (Agentic Extension) is explicitly out of scope — listed once, at the end, as a deliberate non-plan. |
| References | [requirements.md](./requirements.md) (SRS v1.0), [rag_design.md](./rag_design.md) (v1.1), [architecture.md](./architecture.md) (SAD v1.2), [interfaces.md](./interfaces.md) (v1.1), [domain_models.md](./domain_models.md) (v1.3), [sequence_diagrams.md](./sequence_diagrams.md) (v1.1), [testing.md](./testing.md) (v1.0), [evaluation/benchmark_spec.md](./evaluation/benchmark_spec.md) (v1.0), [deployment.md](./deployment.md) (v1.0) |
| Prepared By | Principal AI Solution Architect |
| Date | 2026-07-29 |

---

## 1. Document Control

`tasks.md` is the ninth and final document in the Specification-Driven Development (SDD) chain:

```
requirements.md → rag_design.md → architecture.md → interfaces.md → domain_models.md →
sequence_diagrams.md → testing.md → deployment.md → tasks.md → implementation
```

**This is a true implementation roadmap, not a generic task list.** A generic task list ("build the retriever," "add error handling") would let implementation drift silently away from nine documents of deliberate design decisions. Every task below carries the same discipline this whole SDD chain has maintained: a claim is only as good as its traceability. Specifically, every task cites, where applicable:

- the **Functional/Non-Functional Requirement** it satisfies (`requirements.md`),
- the **Interface Contract** it implements (`interfaces.md`),
- the **Domain Model(s)** it produces or consumes (`domain_models.md`),
- the **Sequence Diagram** its runtime behavior must match (`sequence_diagrams.md`),
- the **Test Reference** that validates it (`testing.md`), and
- any **Deployment Requirement** it must satisfy (`deployment.md`).

Where any of these is not applicable to a task (e.g., a purely internal refactor with no direct FR), that column is marked `—`, not silently omitted — an empty citation is still a stated fact about the task, not a gap in the table.

**No task introduces a new architectural decision.** Every task builds something already specified in an upstream document. Where a task is blocked on an unresolved upstream decision (an open ADR, an open decision from `testing.md`/`domain_models.md`/`deployment.md`), that is stated as a blocker, not silently worked around.

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-07-29 | Initial Implementation Roadmap |

---

## 2. Task Organization Principle

Tasks are grouped by the same four-phase Implementation Scope `rag_design.md` §10 already established, so that the roadmap's sequencing decisions were made once, at the architecture level, not re-litigated here:

| Phase | Scope | Section |
|---|---|---|
| **Phase 1 — Core RAG MVP** | Domain models, provider contracts, all fifteen pipeline stages + Not Found Path, both orchestrators — enough to answer a grounded question and decline an ungrounded one, end to end, via direct invocation (no Application Layer) | §4 |
| **Phase 2 — Engineering Hardening** | Concrete Provider Implementations, configuration and secret management, structured logging/error handling, the Evaluation Harness, regression test automation | §5 |
| **Phase 3 — Production Readiness** | The FastAPI Application Layer, Docker packaging, health checks, externalized session storage, metrics, backup/recovery automation | §6 |
| **Phase 4 — Agentic Extension** | Explicitly **not planned** in this roadmap — see §7 | §7 |

Within each phase, tasks are further grouped by the component they build, in the same order `interfaces.md` §4 already lists them, so a reader moving between this document and `interfaces.md` never has to re-map an ordering.

**A task's Phase assignment is fixed by which phase `rag_design.md` §10 already scoped it into — this document does not re-decide scope, only breaks it into tasks.**

---

## 3. Definition of Done (Applies to Every Task Below)

A task is not complete until all of the following hold — stated once here rather than repeated on every row:

1. The implementation satisfies every cited Interface Contract exactly (`interfaces.md`), including its documented failure scenarios — not only its happy path.
2. Every cited Domain Model is produced/consumed with the exact business meaning `domain_models.md` defines — no field, model, or shortcut is added that `domain_models.md` §16 ("Avoided Design Patterns") would flag.
3. Its behavior matches the cited Sequence Diagram exactly, including call order and short-circuit conditions where applicable.
4. Its cited Test Reference (`testing.md`) passes — Unit-level tasks require their stage's Unit Testing table (`testing.md` §5) to pass in full, including boundary and failure cases, not only normal behavior.
5. Where a Deployment Requirement is cited, the relevant `deployment.md` operational property (ownership, observability signal, failure classification) is demonstrably true of the implementation, not merely assumed.
6. No new vendor SDK type, framework-native object, or processing artifact crosses a boundary `domain_models.md` §16 or `architecture.md` §2.1 already forbids.

---

## 4. Phase 1 — Core RAG MVP

### 4.1 Domain Model Layer (foundational — blocks every task below)

| Task ID | Task | Requirements | Interface | Domain Model(s) | Sequence Diagram | Test Reference |
|---|---|---|---|---|---|---|
| T-DM-01 | Implement Core Document Models | FR-101–109, FR-305 | `interfaces.md` §6 | `Document`, `DocumentMetadata`, `ExtractedDocument` (`domain_models.md` §3) | §4.1 | — |
| T-DM-02 | Implement Chunking Models | FR-401–407, FR-501–505 | §6 | `TextChunk`, `ChunkMetadata` (§4) | §4.1 | — |
| T-DM-03 | Implement Embedding Model | FR-601–606 | §6 | `Embedding` (§5) | §3.1, §4.1 | — |
| T-DM-04 | Implement Query Processing Models | FR-1301–1306 | §6 | `Query`, `QueryContext` (§6) | §3.1 | — |
| T-DM-05 | Implement Retrieval Models | FR-801–806 | §6 | `SearchResult`, `RetrievedChunk` (§7) | §3.1, §3.2 | — |
| T-DM-06 | Implement Generation Model | FR-1101–1106 | §6 | `GeneratedResponse` (§8) | §3.1, §3.3 | — |
| T-DM-07 | Implement Citation Models | FR-1201–1205 | §6 | `Citation`, `CitationReference`, `Response` (§9) | §3.1, §3.2, §3.3 | — |
| T-DM-08 | Implement Conversation Models | FR-1301–1306 | §6 | `ConversationSession`, `ConversationMessage` (§10) | §6.1 | — |
| T-DM-09 | Implement Error/Observability Models | FR-1401–1405, FR-1501–1505 | §6, §7, §8 | `ExecutionMetadata`, `ErrorContext` (§11) | §4.2, §5.1 | — |

**Blocking note:** T-DM-01–09 have no external dependency and can proceed immediately — they are the one part of Phase 1 blocked on nothing.

### 4.2 Provider Interfaces (contracts only — Implementations are Phase 2)

| Task ID | Task | Requirements | Interface | Domain Model(s) | Sequence Diagram | Test Reference | Blocker |
|---|---|---|---|---|---|---|---|
| T-PROV-01 | Define Embedding Provider Interface (contract) | FR-601–606 | `interfaces.md` §5.1 | `Embedding` | §3.1 (`EPI` boundary) | `testing.md` §6.1 | — |
| T-PROV-02 | Define Vector Store Provider Interface (contract) | FR-701–705, FR-801–806 | §5.2 | `SearchResult` | §3.1 (`VSPI` boundary) | §6.2 | — |
| T-PROV-03 | Define LLM Provider Interface (contract) | FR-1101–1106 | §5.3 | `GeneratedResponse` | §3.1 (`LPI` boundary) | §6.3 | — |

**Depends on:** T-DM-01–09 (interfaces are expressed in terms of domain models).

### 4.3 Ingestion Pipeline

| Task ID | Task | Requirements | Interface | Domain Model(s) | Sequence Diagram | Test Reference |
|---|---|---|---|---|---|---|
| T-ING-01 | Implement Document Loader | FR-101, FR-103, FR-104, FR-107–109, FR-206 | `interfaces.md` §4.1 | `Document` | §4.1 | `testing.md` §5.1 |
| T-ING-02 | Implement PDF Parser | FR-201–205 | §4.2 | `ExtractedDocument` (raw facet) | §4.1 | §5.2 |
| T-ING-03 | Implement Text Preprocessor | FR-301–305 | §4.3 | `ExtractedDocument` (normalized facet) | §4.1 | §5.3 |
| T-ING-04 | Implement Semantic Chunker | FR-401–407 | §4.4 | `TextChunk[]` | §4.1 | §5.4 |
| T-ING-05 | Implement Metadata Extractor | FR-501–505 | §4.5 | `ChunkMetadata` | §4.1 | §5.5 |
| T-ING-06 | Implement Embedding Generator | FR-601–606 | §4.6 | `Embedding` | §4.1 | §5.6 |
| T-ING-07 | Implement Vector Indexer | FR-701–705, FR-105/FR-702 (re-ingestion) | §4.7 | `TextChunk`, `Embedding` | §4.1 (incl. re-ingestion note) | §5.7 |
| T-ING-08 | Implement Ingestion Orchestrator | FR-1401–1405 (batch isolation) | §3.1 | Composition of the above | §4.1, §4.2 | §7 (orchestrator ownership) |

**Depends on:** T-DM-01–02 (§4.1), T-PROV-01/02 (§4.6–4.7). Sequenced internally in the order listed — each stage's unit tests (`testing.md` §5.1–5.7) should pass before the Ingestion Orchestrator task (T-ING-08) integrates them, per §8.4/§8.5's integration-test expectations.

### 4.4 Query Pipeline

| Task ID | Task | Requirements | Interface | Domain Model(s) | Sequence Diagram | Test Reference | Notes |
|---|---|---|---|---|---|---|---|
| T-QRY-01 | Implement Session Manager | FR-1301–1306 | `interfaces.md` §4.8 | `ConversationSession` | §6.1 | `testing.md` §5.8 | MVP uses in-memory backing store (`deployment.md` §11) |
| T-QRY-02 | Implement Query Analyzer | — (architectural extension, no approved FR) | §4.9 | `Query` (provisional field) | §3.1 (marked provisional) | §5.9 | **Blocked/provisional** — `architecture.md` §16; do not treat as mandatory Phase 1 scope until formally accepted into `requirements.md`. If deferred, the Query Orchestrator routes every query directly to Query Reformulator. |
| T-QRY-03 | Implement Query Reformulator | FR-1304 | §4.10 | `Query` (resolved form) | §3.1, §6.1 | §5.10 | Mechanism open (`architecture.md` ADR-008) — contract shape is implementable now, mechanism choice is not |
| T-QRY-04 | Implement Retriever | FR-801–806 | §4.11 | `SearchResult[]` | §3.1, §3.2 | §5.11 | Must correctly produce the *empty* result as a valid, non-error outcome |
| T-QRY-05 | Implement Context Builder | FR-901–905 | §4.12 | `RetrievedChunk[]`, `QueryContext` | §3.1 | §5.12 | Must never construct `QueryContext` for empty evidence (Runtime Invariant 2) |
| T-QRY-06 | Implement Prompt Assembler | FR-1001–1005 | §4.13 | Consumes `QueryContext`; produces no domain model | §3.1 | §5.13 | Rendered prompt is confirmed non-domain (`domain_models.md` §16) |
| T-QRY-07 | Implement Response Generator | FR-1101–1106 | §4.14 | `GeneratedResponse` | §3.1, §3.3 | §5.14 | MVP reference path is blocking, not streaming (`domain_models.md` §8) |
| T-QRY-08 | Implement Citation Mapper | FR-1201–1205 | §4.15 | `CitationReference`, `Citation`, `Response` (grounded) | §3.1 | §5.15 | Must never call back to `VSPI`/`VDB` (Runtime Invariant 3) |
| T-QRY-09 | Implement Not Found Path | FR-805, FR-1106 | — (stage-equivalent, `rag_design.md` §5.10) | `Response` (declined) | §3.2, §3.3 | §5.16 | Must produce the identical output shape for all three trigger cases (`domain_models.md` §9) |
| T-QRY-10 | Implement Query Orchestrator | FR-1401–1405 | §3.2 | Composition of the above | §3.1–§3.3 | §7 (orchestrator ownership) | Must satisfy every "never" in `testing.md` §7's forbidden-actions table |

**Depends on:** T-DM-01–09, T-PROV-01–03. T-QRY-02 (Query Analyzer) does not block T-QRY-03–10 — the Query Orchestrator can route directly to Query Reformulator if the extension remains deferred.

---

## 5. Phase 2 — Engineering Hardening

| Task ID | Task | Requirements | Interface | Domain Model(s) | Sequence Diagram | Test Reference | Deployment Reference | Blocker |
|---|---|---|---|---|---|---|---|---|
| T-PROV-04 | Build Embedding Provider Implementation | FR-601–606, NFR-EXT-001 | `interfaces.md` §5.1 | `Embedding` | §3.1, §4.1 (`EImpl`/`ES`) | `testing.md` §6.1 | `deployment.md` §7 (credential scoping) | **Blocked** — ADR-004, embedding model selection (`architecture.md` §17) |
| T-PROV-05 | Build Vector Store Provider Implementation | FR-701–705, NFR-EXT-002 | §5.2 | `SearchResult` | §3.1, §4.1 (`VImpl`/`VDB`) | §6.2 | §7, §11, §13 (backup/DR) | **Blocked** — ADR-003, vector database selection |
| T-PROV-06 | Build LLM Provider Implementation | FR-1101–1106, NFR-EXT-003 | §5.3 | `GeneratedResponse` | §3.1, §3.3 (`LImpl`/`LLMSvc`) | §6.3 | §7 | **Blocked** — ADR-005, LLM provider selection |
| T-CFG-01 | Build Configuration Management component | FR-1601–1605 | — (cross-cutting, `architecture.md` §10.3) | — | All (`ExecutionMetadata`'s config-dependent behavior) | `testing.md` §12 (configuration validation failure) | `deployment.md` §6 | — |
| T-CFG-02 | Build Secret Resolution component | FR-1604, NFR-SEC-002 | — | — | §5.1 (credential-dependent calls) | §12, §17 (security logging) | §7 | — |
| T-LOG-01 | Build Structured Logging / `ExecutionMetadata` emission | FR-1501–1505 | §8 (Observability Contracts) | `ExecutionMetadata` | Every diagram, implicitly (§2.2) | §17 | §10 | Depends on T-DM-09 |
| T-ERR-01 | Build Error Taxonomy & Normalization | FR-1401–1405 | §7 (Error Contracts) | `ErrorContext` | §5.1, §4.2 | §9 (Runtime Invariant 4), §12 | §12 | Depends on T-DM-09 |
| T-EVAL-01 | Build Evaluation Harness | NFR-TEST-002/003 | — (drives Query/Ingestion Orchestrator entry points) | Full grounded/declined chain, observed not altered | §7.1 | §8.8 | §8, §10 | Depends on T-QRY-10, T-ING-08 |
| T-EVAL-02 | Populate initial golden question set | — (evaluation content, not a system requirement) | — | — | — | `benchmark_spec.md` §3–§6, §10–§12 | — | **Blocked** — requires a real HR policy corpus and HR Policy Owner engagement (`benchmark_spec.md` §13 item 1) |
| T-TEST-01 | Build regression test automation (pyramid execution + reporting) | NFR-TEST-003 | — | — | — | `testing.md` §14 | `deployment.md` §14 | Depends on T-EVAL-01 |

---

## 6. Phase 3 — Production Readiness

| Task ID | Task | Requirements | Interface | Domain Model(s) | Sequence Diagram | Test Reference | Deployment Reference | Blocker |
|---|---|---|---|---|---|---|---|---|
| T-APP-01 | Build the FastAPI Application Layer | SRS C-005 | `architecture.md` §3 ("Application Layer") | None produced — thin adapter only | — (transport-level, not a pipeline sequence) | `testing.md` §3 (no new test category — existing Integration tests re-run through the new transport) | `deployment.md` §4, §8, §15 (step 2) | — |
| T-APP-02 | Build health check endpoints (liveness/readiness) | NFR-OBS-001 | — | — | — | §9 (Operational Readiness cross-check) | §9 | Depends on T-APP-01 |
| T-APP-03 | Package as a Docker artifact | SRS C-006 | — | — | — | — | §3 (immutable artifacts), §14 (Packaging stage) | Depends on T-APP-01 |
| T-APP-04 | Build externalized Session Store implementation | FR-1301–1306 | `interfaces.md` §4.8 | `ConversationSession` | §6.1 | `testing.md` §5.8 | `deployment.md` §11 (Distributed Sessions), §15 (step 6) | **Blocked** — ADR-007, session storage technology |
| T-APP-05 | Integrate metrics/observability at the deployed-instance level | NFR-OBS-002 | §8 | `ExecutionMetadata` | — | §17 | §10 | Depends on T-LOG-01, T-APP-01 |
| T-APP-06 | Build backup/recovery automation for Document Store and Vector Index | NFR-REL-004/005 | — | `Document`, `ExtractedDocument`, `TextChunk`, `Embedding` (lineage relied on for re-indexing) | §4.1 | — (operational, not a pipeline test) | `deployment.md` §13 | **Blocked** — ADR-010, backup/DR strategy specifics |
| T-APP-07 | Split Ingestion and Query deployment topology | NFR-SCALE-003 | — | — | — | — | `deployment.md` §11, §15 (steps 3–5) | **Blocked** — ADR-011, deployment topology decision |

---

## 7. Phase 4 — Agentic Extension (Explicitly Not Planned)

No tasks are defined in this roadmap for Phase 4. `rag_design.md` §10 already scopes Phase 4 (employee context retrieval, policy reasoning workflows, HR system integrations, tool-based decision support) as future evolution, not current-scope work, and `architecture.md` §15 confirms none of it requires re-architecting anything Phases 1–3 build. This roadmap does not invent tasks for it — doing so would be inventing scope this SDD chain never approved. When Phase 4 is formally scoped, it will require its own requirements update and likely its own architecture revision before a task breakdown like this one would be meaningful.

---

## 8. Task Sequencing Summary

```
Phase 1:  T-DM-*  →  T-PROV-01/02/03 (contracts)  →  T-ING-*  and  T-QRY-*  (parallel, independent pipelines)
                                                              │
Phase 2:  T-PROV-04/05/06 (implementations, ADR-blocked)  ───┤
          T-CFG-*, T-LOG-01, T-ERR-01  ───────────────────────┤ (can proceed in parallel with Provider Implementations)
          T-EVAL-01  (depends on T-ING-08 + T-QRY-10 both complete)
          T-EVAL-02  (blocked on real corpus — independent of engineering sequencing)
          T-TEST-01  (depends on T-EVAL-01)
                                                              │
Phase 3:  T-APP-01  →  T-APP-02, T-APP-03, T-APP-05
          T-APP-04  (ADR-007-blocked, independent of T-APP-01)
          T-APP-06  (ADR-010-blocked, independent of T-APP-01)
          T-APP-07  (ADR-011-blocked, independent of T-APP-01)
```

**Reading this diagram:** Phase 1's ingestion and query pipelines can be built in parallel by different engineers, since neither depends on the other beyond the shared Domain Model Layer and Provider Interface contracts. Phase 2's three Provider Implementations are each blocked on their own independent ADR and do not block each other. Phase 3's Application Layer task is the only true bottleneck in that phase — everything else in Phase 3 can proceed once its own specific ADR resolves, without waiting on the others.

---

## 9. Remaining Blockers (Consolidated)

Every ADR-blocked or otherwise-blocked task above, gathered in one place so a reader does not have to scan every table to find them:

| Blocker | Blocks | Source |
|---|---|---|
| ADR-003 (Vector database selection) | T-PROV-05, T-APP-06 (indirectly, via Vector Index recovery), T-APP-07 (indirectly) | `architecture.md` §17 |
| ADR-004 (Embedding model selection) | T-PROV-04 | `architecture.md` §17 |
| ADR-005 (LLM provider selection) | T-PROV-06 | `architecture.md` §17 |
| ADR-007 (Session storage technology) | T-APP-04 | `architecture.md` §17 |
| ADR-010 (Document Store/Vector Index backup-DR strategy) | T-APP-06 | `deployment.md` §17 |
| ADR-011 (Ingestion/query deployment topology) | T-APP-07 | `deployment.md` §17 |
| Query Analyzer requirements alignment | T-QRY-02 (does not block the rest of Phase 1) | `architecture.md` §16 |
| Query Reformulator mechanism (ADR-008-adjacent) | Behavioral completeness of T-QRY-03 (contract shape is not blocked) | `architecture.md` ADR-008 |
| PDF parser selection (ADR-006) | T-ING-02's concrete implementation (its contract, T-ING-02 as scoped in §4.3, is implementable against a stubbed parser first) | `architecture.md` §17 |
| Real HR policy corpus + HR Policy Owner engagement | T-EVAL-02 | `benchmark_spec.md` §13 |
| Citation precision acceptance threshold | Acceptance sign-off criteria for T-QRY-08/T-EVAL-01, not the tasks' implementability | SRS AC-003, `testing.md` §21 |

**None of these blockers are resolved by this document.** Per this document's own Definition of Done (§3) and this session's established discipline throughout the SDD chain, an open decision is carried forward and cited, never guessed at to unblock a task artificially.

---

## 10. Related Documents

- [requirements.md](./requirements.md) — every FR/NFR cited above.
- [rag_design.md](./rag_design.md) — the four-phase scope this roadmap's structure inherits.
- [architecture.md](./architecture.md) — every ADR blocker cited above.
- [interfaces.md](./interfaces.md) — every contract cited above.
- [domain_models.md](./domain_models.md) — every domain model cited above.
- [sequence_diagrams.md](./sequence_diagrams.md) — every runtime flow cited above.
- [testing.md](./testing.md) — every test reference cited above.
- [evaluation/benchmark_spec.md](./evaluation/benchmark_spec.md) — the evaluation-content tasks (T-EVAL-02) trace to.
- [deployment.md](./deployment.md) — every operational requirement and ADR-010/011 cited above.

This is the final document in the SDD chain. Implementation begins from here — any task that cannot be traced to a row in this document, or any specification change discovered necessary during implementation, should be raised as an update to the relevant upstream document first, not implemented ahead of the specification it would otherwise contradict.

---

*End of Document.*

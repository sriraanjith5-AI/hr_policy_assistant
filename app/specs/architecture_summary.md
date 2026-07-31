# Architecture Summary

## Enterprise HR Policy Assistant — Condensed System Architecture Overview

| Field | Value |
|---|---|
| Source Document | [architecture.md](./architecture.md) (v1.2, Revised — Final Review Before interfaces.md) |
| Purpose | Quick-reference overview of the system-level architecture (context, layering, deployment, ownership boundaries) for reviewers who don't need the full SAD |
| Status | Draft — for review alongside source document |

---

## 1. What This Document Is

`architecture.md` is the **System Architecture Design Document (SAD)** — it sits above [rag_design.md](./rag_design.md), which owns the RAG pipeline's internal stage-by-stage design. The SAD answers system-level questions the pipeline design doesn't: who/what the system talks to (actors, external dependencies), how the codebase is layered, how it deploys (MVP vs. future), and which technology and architecture decisions are still open. It does not restate pipeline internals — it references them.

Core thesis, stated up front and used as the lens for the whole document: *"The system is designed as a modular stage-based RAG pipeline where orchestration logic controls execution flow while individual stages remain independently testable and replaceable."*

As of v1.2, this is the document's **final review pass before `interfaces.md`** — its purpose has shifted from "describe the architecture" to "close every ownership ambiguity that would otherwise leak into interface contracts."

---

## 2. System Context (Section 2)

**Actors:** Employee (asks questions), HR Policy Owner (supplies/maintains source PDFs, accountable for content correctness), System Administrator (operates config, ingestion, document lifecycle).

**External dependencies**, each treated as a narrow, swappable capability with zero business logic of its own:

| Dependency | Boundary |
|---|---|
| LLM Provider | Only ever sees the fully-assembled prompt; no awareness of retrieval or citations |
| Embedding Provider | Stateless text→vector function; no awareness of documents or chunks |
| Vector Database | Stores and searches; doesn't know what "citation" or "policy category" *mean* |
| Document Storage | System-owned raw-text audit store, distinct from the vector index |

The unifying rule: the core system owns all business meaning; every external dependency is a narrow, swappable I/O provider.

---

## 3. Logical Architecture & Dependency Inversion (Section 3)

The layer stack now makes Dependency Inversion explicit rather than implying a single, uniform downward chain:

```
Application Layer → Orchestration Layer → Pipeline Stage Layer → Domain Model Layer → Provider Interfaces
                                                                                              ▲
                                                                          Provider Implementations → External Infrastructure
```

**Provider Interfaces** and **Provider Implementations** are two separate boxes because they depend in *opposite* directions: Pipeline Stages depend downward on interfaces only; Implementations depend downward on the vendor SDK and separately *satisfy* the interface from outside the business-logic chain. Both sides depend on the same abstraction; the abstraction depends on neither.

**In practice:**
- Core application code depends on provider contracts, never a vendor client library.
- Pipeline stages must never directly import LLM SDKs, vector database SDKs, or embedding SDKs.
- Example: the core system depends on the `LLMProvider` interface, not an OpenAI SDK client.

### New in this layer: Domain Model Layer

Sits between Pipeline Stages and Provider Interfaces — the shared vocabulary (`Document`, `DocumentMetadata`, `TextChunk`, `Embedding`, `SearchResult`, `Citation`, `Query`, `Response`, `ConversationSession`) that every other layer produces, consumes, or passes through unchanged. **Ownership is explicit:** these concepts belong to the core system, not to any provider — providers are made to fit the domain model, not the reverse. Provider implementations translate external formats into domain models at the boundary (e.g., a vector DB's raw response → Vector Store Provider Implementation → `SearchResult`), which is what lets pipeline stages stay ignorant of vendor-specific response shapes. Detailed field-level shapes are deferred to `domain_models.md`.

### Orchestrator Responsibility Boundary (new)

**"Orchestrators coordinate workflow execution but do not contain business rules."** Allowed: stage sequencing, execution context management, error propagation, retry coordination, correlation tracking. Not allowed: retrieval scoring rules, chunking rules, citation validation rules, HR policy decisions — those live inside the relevant pipeline stage or a domain service, never inside the Ingestion or Query Orchestrator.

### Query Analyzer — reframed as a tracked extension (changed in this revision)

Query Analyzer is kept in the architecture, but its status changed: **"Query Analyzer is an architectural extension introduced to support intelligent routing. It is not a mandatory MVP requirement unless approved through requirements update."** MVP approach is lightweight deterministic routing/classification; future approach is LLM-assisted routing — same contract either way. Explicitly **not an autonomous agent in the MVP architecture**.

### Session Management — wording tightened (changed in this revision)

**"The architecture supports externalized session storage for production scalability. MVP may use an in-memory implementation behind the same interface boundary."** Future backing stores named as options, not mandates: Redis, database-backed storage, or a distributed cache — none of which changes query pipeline logic. The document is explicit that the MVP's in-memory choice does **not** support multi-instance scaling until an externalized implementation replaces it behind the same interface.

---

## 4. Provider Abstraction (Section 4)

Three interfaces, matching `rag_design.md` Section 3, now explicitly framed as the **Provider Interfaces** half of Section 3's inversion model:

- **Embedding Provider** — chunk + query embeddings, plus model/version as first-class output (prevents silent index/query model mismatch).
- **Vector Store Provider** — storage, similarity search, metadata filtering as an optional predicate (not a separate code path), ranked results.
- **LLM Provider** — blocking/streaming generation, configurable model/params, normalized failure taxonomy so orchestration error handling stays provider-agnostic.

Load-bearing sentence: *"Only provider implementations interact with third-party SDKs. Core pipeline stages depend only on provider contracts."*

---

## 5. Evaluation Architecture (Section 5)

First-class capability, drawn as its own layer sitting above both pipelines and calling down into Provider Interfaces. Responsibilities (expanded this revision): maintain evaluation datasets, measure retrieval effectiveness (Precision@K, Recall@K, Hit Rate@K, MRR), measure citation accuracy, measure answer quality (faithfulness, relevance, completeness, citation correctness), perform regression testing after pipeline changes, run pipeline comparison experiments.

**"The evaluation framework reuses production pipeline components and does not create a separate testing-only RAG implementation."** It drives both pipelines through the same Orchestration Layer entry points any caller would use; where isolation is needed, it swaps the implementation behind a Provider Interface, not the interface itself.

---

## 6. Data & Runtime Flow (Sections 6, 9)

**Ingestion:** PDF → Raw Document Storage → Extracted Text → Processed Chunks → Metadata + Embeddings → Vector Database. Metadata carried per chunk: document ID/version, page, section, chunk ID, extraction confidence, embedding model version — this is what makes citations traceable without runtime re-derivation.

**Query:** Question → Query Analysis → Query Embedding → Vector Retrieval → Relevant Context → LLM Generation → Citation-backed Response (with short-circuits at Query Analysis, empty retrieval, and LLM decline — full branching lives in `rag_design.md` Section 5).

---

## 7. Component Responsibilities (Section 7)

Now includes all nine query-pipeline components (Session Manager, Query Analyzer, and Query Reformulator were added alongside the previously-listed Retriever, Context Builder, Prompt Assembler, Response Generator, Citation Mapper) plus both orchestrators — closing a completeness gap from the prior revision.

---

## 8. Deployment — MVP vs. Future (Section 8)

| | MVP | Future Production |
|---|---|---|
| Entry point | Direct script/CLI/test-harness call into the Orchestration Layer | FastAPI Service (thin Application Layer) |
| Application Layer | **Absent by design** — not a stripped-down version, genuinely not present | Present, but contains no RAG business logic |
| Session storage | In-memory, behind the Session Manager interface | Externalized implementation behind the same interface |
| Core engine | Same layered architecture either way | Same layered architecture either way |

The MVP's lack of an API layer is a deliberate scope choice: validate correct RAG internals (retrieval quality, grounding, citations) before investing in a service interface.

---

## 9. Cross-Cutting & Principles (Sections 10–11)

Configuration management, logging/observability (correlation IDs, per-stage latency, error tracking), error handling (retryable vs. non-retryable, batch isolation, user-safe errors), and security (secret management, no sensitive data in logs, prompt-injection awareness) all apply uniformly across both workloads — detailed in `rag_design.md` Section 8, restated here at the principle level.

Five named principles: Single Responsibility, Dependency Inversion (now explicitly tied to the Provider Interface/Implementation split), Configuration-Driven Design, Provider Independence, Testability.

---

## 10. Technology Stack (Section 12)

Only Python and the custom-orchestration/provider-abstraction *approach* are treated as decided at the architecture level (each still gets a formal ADR for governance record-keeping). Vector database, LLM/embedding provider defaults, PDF parsing library, and session storage technology remain **"Initial MVP Candidates (ADR Required)"** at the category level — no vendor product is named or implied.

---

## 11. Trade-offs (Section 14)

Three decisions, each with an explicit reason, unchanged in substance from the prior revision:

1. **Custom orchestration over a framework** — understand RAG internals directly, keep execution control over the system's trust properties, stay explainable without framework-specific vocabulary.
2. **Abstraction only at the three external boundaries** — avoid indirection where no swap-out requirement exists.
3. **Architectural grounding, not prompt-only** — reduces risk and blast radius structurally; explicitly does not claim to eliminate incorrect answers (same framing as `rag_design.md` Section 6.3).

---

## 12. Scalability & Future Evolution (Sections 13, 15)

Scaling axes: independent ingestion/query workloads, stateless query serving, externalized session storage *(now explicitly conditional — see Section 3 above)*, provider replacement, parallelizable batch ingestion. Key line: *"MVP deployment may run as a single instance while maintaining boundaries required for future scaling."*

Future evolution (agentic assistant, employee profile integration, leave-eligibility reasoning, HR workflow automation, multi-language, enterprise auth) remains explicitly deferred; none of it requires re-architecting the layers in Section 3.

---

## 13. Architecture Extensions Requiring Requirements Alignment (Section 16 — new)

A new, formal tracking section replaces the previous informal "gaps flagged" note:

| Extension | Reason |
|---|---|
| Query Analyzer | Routing capability not explicitly present in the SRS's FR list |
| Relevance grading | Future retrieval improvement capability, not tied to any FR |

These must be formally accepted into `requirements.md` — or explicitly deferred and marked out of scope — before becoming mandatory implementation scope. Until resolved, `interfaces.md` should still define the Query Analyzer's contract, but treat it as *provisionally* in scope.

---

## 14. Architecture Decisions Requiring ADRs (Section 17 — recategorized)

Now grouped into three categories instead of one flat list, and Domain Model Ownership was added as a new candidate:

- **Architectural Decisions** — ADR-001 (custom orchestration), ADR-002 (provider abstraction boundary), ADR-009 (domain model ownership, *new*).
- **Technology Decisions** — ADR-003 (vector database), ADR-004 (embedding model), ADR-005 (LLM provider), ADR-006 (PDF parser), ADR-007 (session storage).
- **Future Capability Decisions** — ADR-008 (Query Analyzer classification mechanism), gated on Section 16's requirements-alignment outcome.

No ADR content (options/consequences) is written in the SAD itself — only candidates are identified, per this revision's explicit constraint.

---

## 15. Readiness for `interfaces.md`

This revision's stated goal was closing ownership ambiguity before contracts get written, and it resolves the three that mattered most:
- **Orchestrators vs. stages** — business rules are now explicitly disallowed inside orchestrators.
- **Domain models vs. providers** — ownership and the translation boundary are now explicit, with a worked example.
- **Query Analyzer's scope status** — no longer implied as accepted MVP requirement; tracked as pending requirements alignment instead.

`architecture.md` v1.2 is marked ready for `interfaces.md` creation on this basis.

---

*This is a condensed reading aid only. The authoritative architecture remains [architecture.md](./architecture.md); in case of any discrepancy, the source document governs.*

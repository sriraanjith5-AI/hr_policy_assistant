# Requirements Review Summary

## Enterprise HR Policy Assistant — SRS Review Notes

| Field | Value |
|---|---|
| Source Document | [requirements.md](./requirements.md) (v1.0, Draft — Pending Review) |
| Purpose of This Document | Condensed review aid for Solution Architects, Engineering Managers, QA, and AI Engineers ahead of formal SRS sign-off |
| Status | Draft — for review alongside source SRS |

---

## 1. Existing Requirements Summary

The source SRS defines a production-grade RAG system that lets employees ask natural-language questions about internal HR policy PDFs and receive citation-backed answers. It is scoped as a **backend/core-logic system** (no UI, no write-back actions, no auth implementation) intended for future exposure via FastAPI and deployment via Docker, built with **custom orchestration** (LangChain explicitly excluded).

The document is organized around 16 functional pipeline stages (ingestion → parsing → preprocessing → chunking → metadata extraction → embedding → vector storage → retrieval → context construction → prompt generation → LLM generation → citation generation → conversation support → error handling → logging → configuration) and 10 non-functional quality dimensions (performance, scalability, reliability, maintainability, observability, security, extensibility, testability, modularity, cost optimization). It totals roughly 90 functional requirements and 35 non-functional requirements, each individually numbered, plus 8 hard constraints, 9 tracked risks, 12 acceptance criteria, and 9 deferred future enhancements.

Overall the spec is grounding-first and anti-hallucination in intent: several requirements (FR-1002, FR-1106, FR-1203, FR-805) exist specifically to prevent the system from answering outside retrieved context or fabricating citations — this is the throughline that should anchor implementation and QA priorities.

---

## 2. Functional Requirements List

| Area | ID Range | Requirement Count | Key Behaviors |
|---|---|---|---|
| Document Ingestion | FR-101–109 | 9 | PDF-only input, batch ingestion, stable doc IDs, idempotent re-ingestion, deletion, size limits, provenance tracking |
| PDF Parsing | FR-201–206 | 6 | Text + page-boundary extraction, structure/table detection, scanned-page flagging, encrypted-PDF rejection |
| Text Preprocessing | FR-301–305 | 5 | Artifact removal, boilerplate dedup, UTF-8 normalization, preserved raw-text copy |
| Semantic Chunking | FR-401–407 | 7 | Semantic-boundary splitting, configurable size/overlap, sentence-safe splits, chunk provenance, config-driven strategy |
| Metadata Extraction | FR-501–505 | 5 | Structural + policy-domain metadata, explicit-null on low confidence, access classification tag, stored with embeddings |
| Embedding Generation | FR-601–606 | 6 | Chunk + query embeddings, model/version tracking, batch generation, retry handling, re-embedding on model change |
| Vector DB Storage | FR-701–705 | 5 | Persist text+metadata+vectors, upsert/delete semantics, metadata-filtered search, swappable vector DB abstraction |
| Semantic Retrieval | FR-801–806 | 6 | Top-K retrieval, similarity threshold, hybrid/metadata filtering, re-ranking hook, "no relevant info" fallback, dedup |
| Context Construction | FR-901–905 | 5 | Token-budgeted context assembly, deterministic ordering, citation-supporting metadata retained, truncation logging, conversation-aware |
| Prompt Generation | FR-1001–1005 | 5 | Versioned templates, context-only answering instruction, citation-format instruction, config-managed templates, few-shot support |
| LLM Response Generation | FR-1101–1106 | 6 | Configurable provider/model/params, timeout handling, categorized failure handling, streaming support, no-fabrication rule |
| Citation Generation | FR-1201–1205 | 5 | Mandatory citations (doc/section/page), claim-to-chunk traceability, unverified-statement flagging, structured citation output |
| Conversation Support | FR-1301–1306 | 6 | Multi-turn sessions, session isolation, bounded history, follow-up resolution, session reset, in-session persistence |
| Error Handling | FR-1401–1405 | 5 | Catalogued error categories, stable error codes, recoverable-vs-not distinction, batch failure isolation, no partial-answer leakage |
| Logging | FR-1501–1505 | 5 | Structured per-stage logs, correlation IDs, per-query log fields, configurable log levels, sensitive-content log avoidance |
| Configuration Management | FR-1601–1605 | 5 | Externalized parameters, environment profiles, fail-fast validation, secrets handling, redacted config diagnostic |

**Total: 91 functional requirements** across 16 pipeline areas.

---

## 3. Non-Functional Requirements List

| Dimension | ID Range | Count | Notable Measurable Targets |
|---|---|---|---|
| Performance | NFR-PERF-001–004 | 4 | p95 ≤ 8s end-to-end (non-streaming); p95 time-to-first-token ≤ 3s; retrieval p95 ≤ 500ms @ 100K chunks; 50-page PDF ingested ≤ 2 min |
| Scalability | NFR-SCALE-001–003 | 3 | ≥ 50 concurrent sessions; ≥ 10,000 pages / 100K+ chunks; independent scaling of ingestion vs. serving |
| Reliability | NFR-REL-001–005 | 5 | 99.5% monthly availability; graceful degradation; retry-with-backoff; idempotent ingestion; failure isolation |
| Maintainability | NFR-MAINT-001–003 | 3 | Independently modifiable stages; documented config defaults/ranges; independently versioned prompts |
| Observability | NFR-OBS-001–004 | 4 | Liveness/readiness health checks; rate/error/latency/relevance/token metrics; end-to-end correlation IDs; alerting-signal support |
| Security | NFR-SEC-001–007 | 7 | TLS everywhere; no secrets in logs; untrusted-input handling (prompt-injection awareness); ingestion-vs-query access separation; classification-tag hook; minimal third-party data exposure; ingestion audit trail |
| Extensibility | NFR-EXT-001–005 | 5 | Swappable embedding/vector-DB/LLM providers; transport-independent core logic; pluggable format parsers |
| Testability | NFR-TEST-001–004 | 4 | Isolated unit testing per stage; reproducible integration test set; retrieval precision/recall regression testing; simulated dependency-failure testing |
| Modularity | NFR-MOD-001–003 | 3 | Component decomposition matching pipeline stages; contract-based communication; separable orchestration layer |
| Cost Optimization | NFR-COST-001–005 | 5 | Token/call usage tracking; context/top-K as cost levers; no redundant re-embedding; query-level caching; configurable cost-per-query ceiling with alerting |

**Total: 43 non-functional requirements** across 10 quality dimensions.

---

## 4. Assumptions

As stated in Section 5 of the source SRS (AS-001–AS-009):

- Source documents are PDFs supplied by the HR Policy Owner (AS-001).
- Authentication/authorization is handled externally (identity provider/API gateway); the system trusts an already-authenticated caller (AS-002).
- Single-tenant operation only — no multi-tenant document isolation in v1.0 (AS-003).
- English-only source documents in v1.0 (AS-004).
- An LLM API and embeddings API/library are available and reachable (AS-005).
- A vector database is available and reachable (AS-006).
- Document updates happen periodically via re-ingestion, not real-time streaming (AS-007).
- HR Policy Owner is accountable for source content accuracy; the system is accountable for faithful retrieval/representation (AS-008).
- Expected load is enterprise-scale (hundreds–low thousands of employees), not internet-scale (AS-009).

**Review note:** these assumptions are load-bearing for several NFRs (e.g., NFR-SCALE-001's 50-concurrent-session target derives directly from AS-009) — if any assumption changes materially (e.g., multi-tenant becomes required, or expected user count grows 10x), the corresponding NFR targets should be revisited, not just the assumption text.

---

## 5. Missing Requirements

Gaps identified during review that are not covered — or only partially covered — by the current SRS:

1. **Answer quality/precision threshold left unfinalized.** AC-003 explicitly defers the target citation-precision percentage to "finalized during test plan derivation" — this is a placeholder, not a committed number, and should be closed before QA sign-off.
2. **No explicit data retention / deletion policy for conversation history.** FR-1306 says history persists "for the duration of a session" but does not define session timeout, max session lifetime, or whether/how conversation logs are retained post-session for audit vs. privacy purposes.
3. **No PII handling requirement for user queries.** Employees may type identifying details (e.g., "my manager X denied my request") into queries; there's no requirement governing whether/how such query content is logged, retained, or redacted (relevant to NFR-SEC-007 audit trail and general privacy compliance).
4. **No explicit rate-limiting / abuse-prevention requirement** for the query endpoint (distinct from LLM-provider-side rate limits in FR-1104) — nothing bounds a single user/session from issuing excessive requests.
5. **No accessibility requirement** — not applicable to the backend itself, but worth flagging as a gap for the future UI enhancement (FE-001) so it isn't overlooked later.
6. **No explicit versioning/compatibility requirement for the vector index schema** — FR-606 covers re-embedding on model change, but there's no requirement for how schema/dimension changes (e.g., switching to a differently-sized embedding model) are migrated without downtime.
7. **No requirement for evaluation dataset ownership/maintenance** — NFR-TEST-003 requires a labeled test set for regression evaluation, but nothing specifies who curates/maintains/expands it over time as policies change.
8. **No explicit disaster recovery / backup requirement** for the vector database or document store (distinct from NFR-REL availability targets, which cover uptime, not data durability/backup cadence).
9. **No internationalization-readiness requirement**, even as a forward-looking hook — AS-004 restricts to English, but unlike FR-504's access-classification hook, there's no equivalent lightweight metadata hook (e.g., a `language` field) to ease FE-003 later.
10. **No explicit requirement on handling contradictory or superseded policy content** (e.g., two ingested document versions both matching a query) beyond FR-105's "replace outdated chunks" — doesn't address the case where an old and new version briefly coexist or where two different policies conflict.

---

## 6. Architecture Decisions Implied

The SRS avoids prescribing implementation, but several requirements collectively imply architectural commitments that the design phase should treat as fixed constraints:

- **Layered, stage-based pipeline architecture** with well-defined data contracts between stages (NFR-MOD-001/002) — implies a pipeline/stage abstraction (not a monolithic function) is required, even though no class design is specified here.
- **Orchestration must be separable from stage logic** (NFR-MOD-003, C-002) — implies a dedicated orchestration/control-flow layer distinct from stage implementations, hand-built rather than framework-provided.
- **Provider abstraction layers are mandatory**, not optional, for embeddings, vector DB, and LLM (NFR-EXT-001–003, FR-705) — implies an interface/adapter pattern at each of those three integration points from day one, not retrofitted later.
- **Stateless request-serving path** (NFR-SCALE-001 implies statelessness to support horizontal scaling) — implies conversation state (Section 6.13) must live in an external/shared store reachable by any instance, not in-process memory, once scaled beyond one instance.
- **Separation of ingestion and query-serving workloads** (NFR-SCALE-003) — implies these should be independently deployable/scalable units (e.g., separate processes or services), not a single tightly coupled runtime.
- **Configuration externalization as a first-class concern** (FR-1601–1605) — implies a centralized configuration-loading mechanism used uniformly across all stages, validated at startup.
- **Transport-agnostic core** (NFR-EXT-004, C-004/C-005) — implies core pipeline logic must not import or depend on FastAPI/HTTP-specific types, confirming a clean boundary will be needed between "core" and "future API layer" code.
- **Structured, correlation-ID-driven logging as a cross-cutting concern** (FR-1502, NFR-OBS-003) — implies a shared logging/tracing utility threaded through every stage rather than ad hoc per-stage logging.
- **Dual storage of raw and processed text** (FR-305) — implies the ingestion pipeline needs somewhere to persist original extracted text separately from normalized text and from the vector DB (which only need hold the processed/chunked form), i.e., likely an additional document store beyond the vector database.

---

## 7. Open Questions

Items that should be resolved with stakeholders before or during implementation planning, beyond what's already flagged as "missing" in Section 5:

1. **Vector database and LLM/embedding provider selection.** The SRS deliberately avoids naming specific products (per constraint C-007 cloud portability). Which specific vector DB and LLM/embedding providers will be used for the initial deployment target, and has portability actually been validated for those specific choices?
2. **Conversation history storage mechanism.** FR-1306 explicitly leaves the persistence mechanism as "an implementation decision" — does the team have a preferred store (e.g., Redis, DB table) in mind, or is this fully open for the design phase?
3. **What counts as "nominal load" precisely?** NFR-PERF/SCALE targets reference "nominal load" without a numeric request-rate definition — should this be pinned to a specific requests/second or requests/minute figure for load testing?
4. **Re-ranking mechanism scope.** FR-804 makes re-ranking a "pluggable hook" with "no specific algorithm mandated" — is a re-ranker required for v1.0 acceptance, or is the hook sufficient (i.e., can v1.0 ship with re-ranking as a no-op)?
5. **Ownership of the labeled evaluation/test question set** (NFR-TEST-002/003, AC-003) — who from the HR Policy Owner side will supply and validate "known correct" answers, and on what cadence will it be refreshed as policies change?
6. **Definition of "Confidential" access classification behavior.** FR-504/NFR-SEC-005 introduce the tag as a forward-looking hook with enforcement explicitly out of scope — should v1.0 ingestion still refuse/warn on documents marked Confidential, or is the tag purely inert metadata for now?
7. **Cost ceiling value.** NFR-COST-005 requires a "configurable cost-per-query ceiling" but doesn't propose a starting number — what's the initial budget figure stakeholders want enforced/alerted on?
8. **Streaming vs. non-streaming as the default mode.** FR-1105 makes streaming configurable; is streaming the intended default for the eventual FastAPI layer, given the tighter p95 target in NFR-PERF-002 vs. NFR-PERF-001?
9. **Session identity source.** FR-1302 scopes conversation history to a "session identifier" — given AS-002 (auth handled externally), will the session ID be derived from the external identity provider's user/session token, or generated independently by this system?
10. **Acceptance criteria sign-off owner for AC-003's precision threshold** — Section 5's "Missing Requirements" item 1 flags this as unset; who has authority to finalize that number, QA Lead or HR Policy Owner (since it's as much a business-risk-tolerance call as a technical one)?

---

*This summary is a review aid only. The authoritative requirements remain those defined in [requirements.md](./requirements.md); in case of any discrepancy, the source SRS governs.*

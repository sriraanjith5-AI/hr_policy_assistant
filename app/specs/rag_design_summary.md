# RAG Design Summary

## Enterprise HR Policy Assistant — Condensed Architecture Overview

| Field | Value |
|---|---|
| Source Document | [rag_design.md](./rag_design.md) (v1.0, Draft — Pending Review) |
| Purpose | Quick-reference overview of the architecture for reviewers who need the shape of the system without the full detail |
| Status | Draft — for review alongside source design |

---

## 1. What This Architecture Is

A **custom-orchestrated, stage-pipeline RAG system** with no orchestration framework (no LangChain — C-001/C-002). Two independently scalable workloads — **Ingestion** and **Query-Serving** — are built from the same class of component ("Stages"), sequenced by thin custom "Orchestrators," and share three narrow **Provider Abstractions** (Embedding, Vector Store, LLM) that are the *only* points where third-party SDKs are touched (C-003). Everything else — chunking, retrieval logic, prompt assembly, citation mapping, conversation management — is hand-built.

Core design commitment: grounding is structurally enforced, not just prompted. An empty retrieval result or an LLM's own "I can't answer from this" is routed to a dedicated no-citation "Not Found" path before generation/citation logic ever runs — it's architecturally impossible for the system to emit a factual answer with zero supporting context.

---

## 2. Provider Abstraction Layer (Section 3)

Three interfaces sit between all stages and the outside world, enabling swap-out without touching pipeline logic (NFR-EXT-001–003):

| Interface | Responsibility | Key Design Point |
|---|---|---|
| Embedding Provider | Text → vector, for both chunks and queries | Exposes model/version as first-class output to prevent silent mismatch between index and query embeddings |
| Vector Store | Persist/query chunk text + metadata + vectors | Filters expressed in provider-neutral predicate form, not vendor query syntax |
| LLM Provider | Submit prompt → generated text (blocking or streaming) | Normalizes failures into categories (rate-limited/timeout/refused/transient) so error handling is provider-agnostic |

---

## 3. Ingestion Pipeline (Section 4)

Linear, per-document sequence (batch items processed independently so one failure doesn't block others — FR-1404):

**Document Loader → PDF Parser → Text Preprocessor → Semantic Chunker → Metadata Extractor → Embedding Generator → Vector Indexer**, sequenced by the **Ingestion Orchestrator**.

Plus one supporting (non-pipeline) component: the **Document Store**, which persists original raw extracted text separately from the vector index, for audit purposes distinct from retrieval.

Notable propagated signal: a page-level `extraction_fidelity_flag` (set when a page is scanned/unparseable) flows from the PDF Parser through Metadata Extraction so downstream consumers know provenance confidence rather than silently trusting degraded text.

---

## 4. Query-Serving Pipeline (Section 5)

Per-question sequence, sequenced by the **Query Orchestrator**:

**Session Manager → Query Reformulator → Retriever → Context Builder → Prompt Assembler → Response Generator → Citation Mapper**

Two structural short-circuits bypass the LLM/citation stages entirely and route to a shared **"Not Found" path** (empty citations, by construction):
- Retriever returns zero chunks above threshold → skip straight to Not Found (no LLM call — saves cost, guarantees no ungrounded answer).
- LLM itself declines (context insufficient) → route to the same Not Found path.

Conversation state (Session Manager) lives in an externalized store, not in-process memory — required for the stateless-serving-path principle that underpins horizontal scaling (NFR-SCALE-001).

---

## 5. Retrieval Strategy (Section 6)

Six-step process inside the Retriever component:

1. Embed query (same model/version as the index)
2. Over-fetch candidates via similarity search (optionally metadata-filtered)
3. Drop candidates below similarity threshold
4. Deduplicate near-identical chunks (byproduct of chunk overlap)
5. Optional pluggable re-rank step (pass-through identity function if no re-ranker configured — v1.0 status still open, see Section 8)
6. Return final top-K to Context Builder

Metadata filtering is an *optional predicate* on the same search call, not a separate code path — avoids two retrieval paths drifting out of sync. All thresholds/K-values are externally configurable (cost + regression-testing lever).

---

## 6. Citation Generation (Section 7)

Core invariant: **citation metadata has one source of truth — ingestion-time Metadata Extraction — and is never re-derived at query time.** It's carried unmodified from chunk creation through to the final response.

Flow: Prompt Assembler labels context segments with stable reference tokens → LLM instructed to echo them inline → Citation Mapper parses the tokens out of the generated answer and resolves each back to full citation metadata (document/section/page) via the Context Builder's carried-through map, never by re-querying the vector store.

Any generated claim that doesn't resolve to a reference token sets `unverified_statement_flag: true` rather than being silently trusted or silently dropped. The "Not Found" path is architecturally forbidden from calling the Citation Mapper at all, so it can never carry stale/fabricated citations.

---

## 7. Cross-Cutting Concerns (Section 8)

Three shared utilities invoked uniformly by every stage/orchestrator (not separate pipeline stages):

- **Error Handling** — catalogued error taxonomy; Orchestrators classify recoverable (retry+backoff) vs. non-recoverable (fail the unit without crashing the batch/session); no partial output ever presented as complete.
- **Logging & Observability** — single logging spine tagged with a correlation ID per run/request; metrics (NFR-OBS-002) are *derived from* these structured log events rather than a separately instrumented path, to prevent drift.
- **Configuration Management** — single config-loading component consulted by everything; fail-fast validation at startup; secrets never touch stage logic or logs directly.

---

## 8. Evaluation Approach (Section 9)

Architected as an **offline harness reusing production pipeline components** (not a bespoke test-only path), in five layers:

1. Stage-level unit evaluation (stubbed providers, no live calls)
2. Full pipeline integration evaluation against a labeled fixture corpus + question set
3. Retrieval precision/recall tracked as a regression gate for chunking/retrieval config changes
4. Citation accuracy + `unverified_statement_flag` rate tracked as a hallucination-risk indicator
5. Resilience evaluation via failure-simulation mode on each Provider Abstraction

Explicitly out of scope for the architecture itself: *who* curates the labeled question set and *what* the exact acceptance precision threshold is — those are governance decisions the SRS (AC-003) already flags as unresolved, not something this design document settles.

---

## 9. Carried-Forward Open Questions (Section 10)

Five stakeholder decisions from the requirements review are noted as directly affecting specific component designs, not re-decided here:

| Question | Affects |
|---|---|
| Session identity source | Session Manager's input contract |
| Conversation history storage tech | What backs the Session Manager's externalized store |
| Is a real re-ranker required for v1.0? | Whether Retriever step 5 is live logic or a pass-through |
| Numeric definition of "nominal load" | Sizing of Retriever over-fetch count and Vector Store throughput expectations |
| Streaming default for future FastAPI layer | Response Generator's default mode |

---

## 10. One-Paragraph Takeaway

Everything funnels through two orchestrators built from swappable, independently testable stages, talking to the outside world through exactly three abstraction points. Grounding and citation integrity are enforced structurally — via short-circuit paths and a single source of truth for citation metadata — rather than relying solely on prompt instructions, which is the architecture's answer to the SRS's core anti-hallucination requirements (FR-1002, FR-1106, FR-1203) and the top-ranked risk in the requirements review (R-002).

---

*This is a condensed reading aid only. The authoritative architecture remains [rag_design.md](./rag_design.md); in case of any discrepancy, the source design document governs.*

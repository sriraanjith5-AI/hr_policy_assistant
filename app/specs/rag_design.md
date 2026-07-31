# RAG Architecture Design Specification

## Enterprise HR Policy Assistant — Custom Retrieval-Augmented Generation Orchestration

| Field | Value |
|---|---|
| Document Type | Architecture Specification |
| Project Name | Enterprise HR Policy Assistant |
| Version | 1.1 |
| Status | Revised — Pending Review |
| Upstream Documents | [requirements.md](./requirements.md) (SRS v1.0), [requirements_review_summary.md](./requirements_review_summary.md) |
| Prepared By | Principal AI Solution Architect |
| Date | 2026-07-29 |

---

## Document Control

This document translates the approved-in-principle functional and non-functional requirements in `requirements.md` into an **architecture** — component responsibilities, data flow, and inter-stage interfaces — without prescribing code, class hierarchies, or folder layout. It exists to let Solution Architects, Engineering Managers, QA Engineers, and AI Engineers agree on system shape before implementation begins, per the Specification-Driven Development (SDD) methodology mandated in the SRS (Constraint C-008).

This document does **not** supersede `requirements.md`. Every architectural decision below is traceable to one or more requirement IDs (FR-xxx, NFR-xxx, C-xxx) from the SRS; where a decision resolves an open question raised in `requirements_review_summary.md`, that is noted explicitly. Where a decision is an architectural refinement not separately enumerated as an FR (e.g., the Query Analyzer in Section 5.2), that is called out explicitly rather than implied.

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-07-29 | Initial architecture draft for review |
| 1.1 | 2026-07-29 | Incorporated architecture review feedback: softened hallucination-prevention language to avoid absolute claims; added Query Analyzer component and renumbered Section 5 accordingly; added a future relevance-grading enhancement to the retrieval strategy; added a phased Implementation Scope section (MVP → hardening → production readiness → agentic extension); expanded the evaluation section with retrieval and generation quality metrics; corrected internal cross-section reference errors carried over from v1.0 |

---

## 1. Architectural Principles

These principles govern every design decision in this document and are derived directly from the SRS constraints (Section 8 of `requirements.md`):

1. **No orchestration framework.** LangChain or any equivalent high-level RAG orchestration library is prohibited (C-001). Control flow that sequences pipeline stages is custom logic owned by this project (C-002).
2. **Library use is bounded to four integration points only**: PDF parsing, embedding generation, vector database access, and LLM API access (C-003). Every other capability — chunking strategy, retrieval logic, prompt assembly, citation mapping, conversation management, orchestration — is custom-built.
3. **Core logic is transport-agnostic.** Nothing in the pipeline may depend on FastAPI, HTTP semantics, or any specific serving framework (C-004, C-005, NFR-EXT-004). A future FastAPI layer is a thin adapter that calls into core logic, never the other way around.
4. **Core logic is provider-agnostic.** Every external dependency (embedding provider, vector database, LLM provider) sits behind an abstraction boundary so it is swappable via configuration (NFR-EXT-001–003, FR-705).
5. **The pipeline is stage-based, not monolithic.** Each of the 16 functional areas in the SRS corresponds to an addressable architectural component with an explicit input/output contract (NFR-MOD-001/002).
6. **Grounding is the primary design goal, not an absolute guarantee.** Every architectural decision touching prompt construction, generation, and citation is oriented toward the SRS's context-only-answering intent (FR-1002, FR-1106, FR-1203) — this is the system's central trust property and the primary driver of the retrieval and citation design in Sections 6–7. The architecture reduces the *likelihood and blast radius* of ungrounded answers through structural controls (routing, validation, traceability); it does not claim to make incorrect or unsupported output impossible. See Section 6.3 for the precise framing.
7. **Statelessness on the serving path.** To meet NFR-SCALE-001 (horizontal scaling), request-handling components hold no in-process state that survives a single request; conversation state is externalized (Section 5.1).

---

## 2. Architectural Style

The system is a **custom-orchestrated, stage-pipeline RAG architecture** composed of two independently scalable workloads sharing a common set of stage components and abstraction interfaces:

- **Ingestion Workload** — batch/on-demand pipeline that turns source PDFs into indexed, embedded, metadata-tagged chunks in the vector database.
- **Query-Serving Workload** — request/response (or streaming) pipeline that turns an employee question into a grounded, cited answer.

Both workloads are built from the same class of components — **Stages** — connected by an **Orchestrator**, and both depend on the same three **Provider Abstractions** (Embedding, Vector Store, LLM). This shared-component design directly satisfies NFR-SCALE-003 (independent scalability of ingestion vs. serving) while avoiding duplicated logic, and satisfies NFR-MOD-001–003 (component decomposition, contract-based communication, separable orchestration).

```
                          ┌─────────────────────────────────────┐
                          │           ORCHESTRATOR               │
                          │  (custom control flow — no framework)│
                          └───────────────┬───────────────────────┘
                                          │ sequences
              ┌───────────────────────────┼───────────────────────────┐
              │                                                       │
   ┌──────────▼──────────┐                                 ┌─────────▼─────────┐
   │  INGESTION PIPELINE   │                                 │  QUERY PIPELINE     │
   │  (Section 4)          │                                 │  (Section 5)        │
   └──────────┬──────────┘                                 └─────────┬─────────┘
              │                                                       │
              └──────────────────┬────────────────────────────────────┘
                                 │  shared via Provider Abstractions
                    ┌────────────▼─────────────┐
                    │   PROVIDER ABSTRACTIONS    │
                    │  Embedding · VectorStore ·  │
                    │  LLM  (Section 3)           │
                    └────────────────────────────┘
```

---

## 3. Provider Abstraction Layer

Per NFR-EXT-001–003, the three external dependencies permitted by C-003 are each accessed exclusively through a narrow abstraction interface. No stage component may call an embedding SDK, vector DB SDK, or LLM SDK directly — only through these interfaces. This is the architectural mechanism that satisfies cloud portability (C-007) and provider swap-out without core changes.

### 3.1 Embedding Provider Interface

**Responsibility:** Convert text (chunk or query) into a vector representation, and report which model/version produced it.

| Operation | Input Contract | Output Contract | Related Requirements |
|---|---|---|---|
| Embed batch | List of text strings | List of vectors + model identifier/version | FR-601, FR-604 |
| Embed single (query-time) | One text string | One vector + model identifier/version | FR-602 |
| Report model identity | — | Model name + version string | FR-603, FR-606 |

**Design notes:** The interface must expose model/version identity as first-class output (not buried in logs) so the Vector Store abstraction can reject or flag a query embedding generated by a different model than the one used to index the target chunks (prevents silent relevance degradation — addresses Risk R-003).

### 3.2 Vector Store Interface

**Responsibility:** Persist and query chunk text + metadata + embeddings; support upsert, delete, and filtered similarity search.

| Operation | Input Contract | Output Contract | Related Requirements |
|---|---|---|---|
| Upsert chunks | List of (chunk ID, text, metadata, vector) | Success/failure per chunk | FR-701, FR-702 |
| Delete by document ID | Document ID | Count of vectors removed | FR-703, FR-106 |
| Similarity search | Query vector, top-K, optional metadata filter, optional similarity threshold | Ranked list of (chunk ID, text, metadata, score) | FR-704, FR-801–804 |
| Delete-then-replace by document ID | Document ID, new chunk set | Old chunks removed, new chunks inserted atomically from the caller's perspective | FR-105, FR-702, NFR-REL-004 |

**Design notes:** This is the single most important abstraction for NFR-EXT-002. It must not leak vector-DB-specific query syntax to calling stages — filters are expressed in a provider-neutral metadata-predicate form (e.g., "policy_category = X") that the adapter translates internally.

### 3.3 LLM Provider Interface

**Responsibility:** Submit a fully constructed prompt and return a generated response (streamed or complete), with usage accounting.

| Operation | Input Contract | Output Contract | Related Requirements |
|---|---|---|---|
| Generate (blocking) | Prompt payload, generation parameters (temperature, max tokens, timeout) | Generated text + token usage + finish reason | FR-1101, FR-1102, FR-1103 |
| Generate (streaming) | Same as above | Stream of text deltas + final usage/finish-reason event | FR-1105 |
| Classify failure | Raw provider error | Normalized failure category (rate-limited / timeout / refused / transient / unknown) | FR-1104, FR-1401 |

**Design notes:** Failure normalization is architecturally significant — it is what allows the Error Handling cross-cutting concern (Section 8) to apply a single recoverable-vs-non-recoverable policy regardless of which LLM provider is configured.

---

## 4. Ingestion Pipeline — Component Responsibilities

The ingestion pipeline is a linear sequence of stages, each consuming the previous stage's output. It is triggered per-document (or per-batch, iterating documents independently to satisfy FR-1404 failure isolation).

### 4.1 Document Loader

- **Responsibility:** Accept a source PDF (or batch), validate it is well-formed, non-corrupted, within size limits, and not unreadably encrypted; assign a stable document ID.
- **Requirements:** FR-101, FR-103, FR-104, FR-107, FR-108, FR-206.
- **Input:** Raw file (+ optional prior document ID for re-ingestion).
- **Output:** Validated file handle + document ID + provenance record (filename, timestamp, ingesting actor, version number) → FR-109.
- **Failure mode:** Malformed/oversized/encrypted files are rejected here with a categorized error (FR-1401) before any downstream stage runs; this failure does not abort a concurrent batch (FR-1404).

### 4.2 PDF Parser

- **Responsibility:** Extract page-ordered text, structural markers (headings, lists), and table content from the validated PDF, using the sole permitted PDF-parsing library dependency (C-003).
- **Requirements:** FR-201–205.
- **Input:** Validated file handle.
- **Output:** Per-page structured extraction result: `{page_number, raw_text, structural_elements[], tables[], extraction_fidelity_flag}`.
- **Failure mode:** Pages that cannot be extracted (e.g., scanned images) are flagged `unparseable`/`reduced-fidelity` rather than silently dropped (FR-205) — this flag propagates through Metadata Extraction (4.5) so downstream consumers know provenance confidence.

### 4.3 Text Preprocessor

- **Responsibility:** Normalize extracted text — strip PDF artifacts, deduplicate repeated boilerplate, standardize encoding — while preserving structural cues and the original raw text.
- **Requirements:** FR-301–305.
- **Input:** Per-page structured extraction result (4.2 output).
- **Output:** `{page_number, normalized_text, raw_text_reference, structural_elements[]}`.
- **Design note:** Raw text is preserved by reference (not duplicated in every downstream artifact) but must remain retrievable for audit — see Section 4.9 (Document Store).

### 4.4 Semantic Chunker

- **Responsibility:** Split normalized, structure-aware text into chunks along semantic boundaries, applying configured target/max size and overlap, never splitting mid-sentence.
- **Requirements:** FR-401–407.
- **Input:** Normalized per-page text + structural elements (4.3 output), chunking configuration (size, overlap, strategy).
- **Output:** List of chunk records: `{chunk_id, document_id, text, source_page_range, section_path}`.
- **Design note:** This is a pure function of its inputs and configuration — no external API calls — which makes it independently unit-testable per NFR-TEST-001.

### 4.5 Metadata Extractor

- **Responsibility:** Attach structural metadata (page, section) and attempt extraction of policy-domain metadata (category, effective date, owner), marking low-confidence fields explicitly null rather than guessing.
- **Requirements:** FR-501–505.
- **Input:** Chunk records (4.4 output) + document-level provenance (4.1 output) + extraction fidelity flags (4.2 output).
- **Output:** Enriched chunk records: `{..., metadata: {document_title, section_path, page_range, policy_category, effective_date, policy_owner, access_classification, extraction_fidelity, ingestion_timestamp, document_version}}`.

### 4.6 Embedding Generator

- **Responsibility:** Call the Embedding Provider Interface (Section 3.1) in batch to produce a vector per chunk; record model/version.
- **Requirements:** FR-601, FR604–606.
- **Input:** Enriched chunk records (4.5 output).
- **Output:** `{..., embedding_vector, embedding_model_id}` per chunk.
- **Failure mode:** Per-chunk embedding failures are retried per NFR-REL-003; unrecoverable per-chunk failures are reported without aborting the batch (FR-605).

### 4.7 Vector Indexer

- **Responsibility:** Call the Vector Store Interface (Section 3.2) to upsert embedded chunk records; on re-ingestion, atomically replace the prior document's chunks.
- **Requirements:** FR-702, FR-703, NFR-REL-004/005.
- **Input:** Embedded chunk records (4.6 output), document ID.
- **Output:** Ingestion result summary: `{document_id, chunks_indexed, chunks_failed, pages_flagged_reduced_fidelity, status}`.

### 4.8 Ingestion Orchestrator (sub-orchestrator)

- **Responsibility:** Sequence 4.1 → 4.2 → 4.3 → 4.4 → 4.5 → 4.6 → 4.7 for a single document; iterate documents in a batch independently so one document's failure does not block others (FR-1404); emit structured logs at each stage transition (FR-1501) with a correlation ID per document (FR-1502).
- **Requirements:** FR-1404, FR-1501, FR-1502, NFR-MOD-003.
- **Design note:** This is a distinct orchestrator instance from the Query Orchestrator (Section 5.9) — both are thin, custom control-flow components that call stages in sequence and handle stage-level errors; they share no runtime state, satisfying NFR-SCALE-003.

### 4.9 Document Store (supporting component, not a pipeline stage)

- **Responsibility:** Persist original raw extracted text (4.3) separately from the vector database, addressing FR-305's requirement to retain unmodified text for audit without bloating the vector index with duplicate content.
- **Requirements:** FR-305, implied by architecture review (`requirements_review_summary.md` Section 6, "Dual storage of raw and processed text").
- **Design note:** This is intentionally a separate concern from the Vector Store abstraction (Section 3.2) — the vector store holds retrieval-optimized content; the document store holds audit-optimized content. The two are linked by `document_id`/`chunk_id` reference, not duplicated data.

### Ingestion Data Flow Diagram

```
 PDF file
    │
    ▼
[4.1 Document Loader] ──(reject: malformed/oversized/encrypted)──► Error (FR-1401)
    │  validated file + document_id + provenance
    ▼
[4.2 PDF Parser] ──(flag: unparseable page)──► fidelity flag propagates forward
    │  per-page {raw_text, structure, tables, fidelity}
    ▼
[4.3 Text Preprocessor] ───────────────────────► raw text persisted to [4.9 Document Store]
    │  per-page {normalized_text, structure}
    ▼
[4.4 Semantic Chunker]
    │  chunk records {text, page_range, section_path}
    ▼
[4.5 Metadata Extractor]
    │  enriched chunk records {+ metadata}
    ▼
[4.6 Embedding Generator] ──► [3.1 Embedding Provider Interface]
    │  embedded chunk records {+ vector, model_id}
    ▼
[4.7 Vector Indexer] ──► [3.2 Vector Store Interface]
    │  ingestion result summary
    ▼
 Logged (FR-1501/1502) + returned to caller
```

---

## 5. Query-Serving Pipeline — Component Responsibilities

The query pipeline is triggered per employee question and produces a grounded, cited answer (or an explicit "not found" / declined result). It is the primary vehicle for the grounding-oriented design intent described in Section 1, Principle 6.

### 5.1 Session Manager

- **Responsibility:** Resolve the incoming request's session identifier, load bounded conversation history, and expose a reset operation.
- **Requirements:** FR-1301–1306.
- **Input:** Session ID (source resolved per Section 4.6 open question in `requirements_review_summary.md` — see Section 11 of this document), incoming query text.
- **Output:** `{session_id, conversation_history[bounded], current_query}`.
- **Design note:** Backed by an externalized store (not in-process memory) to satisfy the stateless-serving-path principle (Section 1, Principle 7) — the specific store technology is an implementation decision, not fixed here.

### 5.2 Query Analyzer

- **Responsibility:** Classify the incoming query *before* any retrieval or generation work is performed, so the expensive/grounded path of the pipeline (retrieval, context construction, LLM generation, citation mapping) is only invoked for queries that actually require HR policy content.
- **Status:** This is an architectural refinement introduced in this revision, not a separately enumerated FR in the SRS. It operationalizes the cost-control intent of NFR-COST-002 (avoid unnecessary retrieval/generation work) and supports the grounding principle (Section 1, Principle 6) by keeping full RAG generation scoped to in-domain queries.
- **Input:** `{session_id, current_query, conversation_history[bounded]}` (5.1 output).
- **Output:** `{query_category: "policy_query" | "conversational" | "unsupported", direct_response_text?: string}`.
- **Routing:**
  - `policy_query` → proceeds to the Query Reformulator (5.3) and the full RAG pipeline.
  - `conversational` → routed to a lightweight **Direct Response** — a short reply (e.g., a greeting acknowledgment) produced without invoking retrieval or the grounded-generation path. No citations are attached, and none are expected.
  - `unsupported` → routed to the "Not Found" / Declined-Answer Path (5.10) with a category-appropriate message (e.g., "This assistant only answers HR policy questions"); no citations are attached.
- **Design note:** This is a lightweight classification/routing component, not an agentic planner. It makes a single categorization decision per query and does not perform multi-step reasoning, tool selection, or task decomposition — those capabilities are explicitly deferred to Phase 4 (Section 10). The specific classification mechanism (rule-based heuristics, a small classifier, or a lightweight LLM call) is not mandated here — see Section 11, Open Question 6.

**Example routing:**

| User Input | `query_category` | Flow |
|---|---|---|
| "Hello" | `conversational` | Direct Response — no retrieval, no citations |
| "What is maternity leave eligibility?" | `policy_query` | Full RAG pipeline (5.3 → 5.10) |
| "What's the weather today?" | `unsupported` | Not Found / Declined-Answer Path (5.10), no citations |

### 5.3 Query Reformulator

- **Responsibility:** Resolve ambiguous follow-up queries (e.g., pronoun references) into a self-contained retrieval query using conversation history. Invoked only for queries the Query Analyzer (5.2) classifies as `policy_query`.
- **Requirements:** FR-1304.
- **Input:** Current query + bounded conversation history (5.1 output).
- **Output:** `{reformulated_query, original_query}` — both retained; original is shown to the user/logs, reformulated drives retrieval.
- **Design note:** This stage may itself call the LLM Provider Interface (a lightweight reformulation call) or use a deterministic heuristic — this document does not mandate the mechanism, only the input/output contract, consistent with "no implementation detail" scoping.

### 5.4 Retriever

- **Responsibility:** Embed the reformulated query, execute similarity search (with optional metadata filtering) against the Vector Store Interface, apply the relevance threshold, deduplicate near-identical chunks, and optionally re-rank.
- **Requirements:** FR-801–806, FR-602.
- **Input:** Reformulated query (5.3 output), retrieval configuration (top-K, threshold, filters).
- **Output:** Ranked, deduplicated candidate chunk list: `[{chunk_id, text, metadata, score}]`, possibly empty.
- **Detailed strategy:** See Section 6.

### 5.5 Context Builder

- **Responsibility:** Assemble the retrieved candidate chunks (and, where relevant, prior-turn context) into a token-budgeted, deterministically ordered context payload, applying truncation when the budget is exceeded and recording that truncation occurred.
- **Requirements:** FR-901–905.
- **Input:** Ranked chunk list (5.4 output), conversation history (5.1 output), context token budget (config).
- **Output:** `{context_chunks[ordered, budget-fitted], truncated: bool, citation_metadata[per chunk]}`.
- **Failure mode:** If the Retriever (5.4) returns an empty candidate list, the Context Builder short-circuits and the pipeline proceeds directly to the "not found" response path (Section 5.10) — no LLM call is made, satisfying FR-805 and avoiding wasted cost (NFR-COST-002).

### 5.6 Prompt Assembler

- **Responsibility:** Render the versioned prompt template, injecting system instructions, the fitted context (5.5), conversation history, few-shot examples (if configured), and the current query — with explicit instructions to answer only from context and to decline otherwise.
- **Requirements:** FR-1001–1005.
- **Input:** Context payload (5.5 output), reformulated + original query, prompt template identifier/version (config).
- **Output:** Fully rendered prompt payload ready for the LLM Provider Interface.

### 5.7 Response Generator

- **Responsibility:** Call the LLM Provider Interface (Section 3.3) with the assembled prompt and configured generation parameters; handle streaming vs. blocking per configuration; classify and surface failures.
- **Requirements:** FR-1101–1106.
- **Input:** Prompt payload (5.6 output), generation config.
- **Output:** `{generated_text | stream, token_usage, finish_reason}` or a normalized failure.

### 5.8 Citation Mapper

- **Responsibility:** Map the generated answer's referenced content back to the specific source chunk(s) it draws from, using the citation metadata carried through the Context Builder (5.5); flag any generated statement that cannot be traced to a retrieved chunk.
- **Requirements:** FR-1201–1205.
- **Input:** Generated text (5.7 output), citation metadata (5.5 output).
- **Output:** `{answer_text, citations: [{document_title, section, page_range}], unverified_statement_flag: bool}`.
- **Detailed strategy:** See Section 7.

### 5.9 Query Orchestrator (sub-orchestrator)

- **Responsibility:** Sequence 5.1 → 5.2 → (5.3 → 5.4 → 5.5 → 5.6 → 5.7 → 5.8, when the Query Analyzer classifies the query as `policy_query`) for a single query; apply the Query Analyzer's `conversational`/`unsupported` short-circuits (5.2), the empty-retrieval short-circuit (5.5 failure mode), and the LLM-declines-to-answer short-circuit (5.10); apply timeouts and retry policy at each external-call boundary; emit structured, correlated logs (FR-1501/1502); persist the turn to conversation history (5.1) on completion regardless of which path was taken.
- **Requirements:** FR-1103, FR-1401–1405, FR-1501–1503, NFR-REL-002/003.
- **Design note:** Like the Ingestion Orchestrator (4.8), this is custom control flow — a sequence of stage calls with explicit branching and error handling — not a framework-managed chain (C-001/C-002).

### 5.10 "Not Found" / Declined-Answer Path

- **Responsibility:** Produce a well-formed, clearly-labeled response when any of: (a) the Query Analyzer (5.2) classifies the query as `unsupported`, (b) the Retriever (5.4) returns no chunks above threshold, or (c) the LLM itself indicates the context is insufficient to answer. No citations are attached in this path.
- **Requirements:** FR-805, FR-1106, FR-1205.
- **Design note:** This is not an error condition — it is a first-class successful outcome of the pipeline, architecturally distinct from the Error Handling concern in Section 8.

### Query Data Flow Diagram

```
 Employee question + session_id
    │
    ▼
[5.1 Session Manager] ──► load bounded conversation_history
    │
    ▼
[5.2 Query Analyzer] ──► classify query_category
    │
    ├── conversational ───────────────────────────────────► Direct Response (no retrieval, no citations)
    │
    ├── unsupported ──────────────────────────────────────► [5.10 Not Found Path] ──► response (no citations)
    │
    ▼ policy_query
[5.3 Query Reformulator]
    │  reformulated_query
    ▼
[5.4 Retriever] ──► [3.2 Vector Store Interface] (via [3.1 Embedding Provider Interface] for query embedding)
    │  ranked candidate chunks (may be EMPTY)
    │
    ├── EMPTY ──────────────────────────────────────────► [5.10 Not Found Path] ──► response (no citations)
    │
    ▼ non-empty
[5.5 Context Builder]
    │  budget-fitted context + citation metadata
    ▼
[5.6 Prompt Assembler]
    │  rendered prompt
    ▼
[5.7 Response Generator] ──► [3.3 LLM Provider Interface]
    │  generated text
    │
    ├── LLM declines (insufficient context) ─────────────► [5.10 Not Found Path] ──► response (no citations)
    │
    ▼ answer produced
[5.8 Citation Mapper]
    │  {answer_text, citations[], unverified_statement_flag}
    ▼
[5.1 Session Manager] ◄── persist turn to conversation_history (all paths, including Direct Response and Not Found)
    │
    ▼
 Response returned to caller (streamed or blocking, per FR-1105)
 Logged end-to-end under one correlation ID (FR-1502, NFR-OBS-003)
```

---

## 6. Retrieval Strategy

This section elaborates the Retriever component (5.4) architecture, since retrieval quality is the primary lever on answer accuracy (Risk R-002, R-007) and on cost (NFR-COST-002).

### 6.1 Retrieval Stages (within the Retriever component)

1. **Query embedding** — the reformulated query is embedded via the Embedding Provider Interface (3.1), using the same model/version validated against the target index (FR-603).
2. **Candidate search** — an over-fetch of `top_K_candidates` (configurable, typically larger than the final top-K passed to context construction) is retrieved via similarity search, optionally pre-filtered by metadata predicate (e.g., policy category) when such a filter is inferable from the query or supplied explicitly (FR-803).
3. **Threshold filtering** — candidates below the configured minimum similarity score are discarded (FR-802).
4. **Deduplication** — near-identical chunks (an expected byproduct of chunk overlap, FR-403) are collapsed, retaining the highest-scoring instance (FR-806).
5. **Re-ranking (pluggable hook)** — an optional re-ranking step may reorder the deduplicated candidate set using a secondary relevance signal. This is architected as a swappable strategy component with a defined input/output contract (`candidates[] → reordered candidates[]`), not a mandated algorithm (FR-804). In the absence of a configured re-ranker, this stage is a pass-through identity function — the architecture must support this as a valid v1.0 configuration (see Open Question 3 in Section 11).
6. **Final top-K selection** — the top-K (post-re-ranking) results are returned to the Context Builder (5.5).

### 6.2 Hybrid Filtering

Metadata-filtered retrieval (FR-803, FR-704) is architected as an **optional predicate** attached to the similarity search call, not a separate retrieval path. This keeps the Retriever's interface to the Vector Store (3.2) single and consistent, whether or not a filter is present, and avoids a second code path that could drift out of sync with the primary semantic path.

### 6.3 Empty-Result Handling and the Limits of Structural Grounding

An empty or below-threshold result set is a **valid, expected output** of the Retriever, not an error. It is the architectural trigger for the Section 5.10 "Not Found" path. This is a deliberate design choice to satisfy FR-805 and the grounding principle (Section 1, Principle 6).

More broadly: **the architecture minimizes unsupported answers by enforcing retrieval-grounded generation, context validation, and citation traceability. It reduces hallucination risk structurally through controlled retrieval and citation validation paths rather than relying only on prompt instructions.** Routing zero-context queries and Query-Analyzer-flagged out-of-domain queries away from the LLM entirely (Section 5.2, 5.10) is one concrete instance of this structural control, and the Citation Mapper's unverified-statement flag (Section 7.3) is another. Neither of these, individually or together, eliminates hallucination risk in the general case — an LLM can still misstate or misattribute content drawn from retrieved chunks that were themselves relevant. This document does not claim absolute elimination of hallucinated or unsupported output; Section 9 describes how residual risk is measured and tracked, not assumed away.

### 6.4 Retrieval Configuration Surface

All of the following are externally configurable per FR-1601, with no code change required to adjust: `top_K_candidates`, `top_K_final`, `similarity_threshold`, `metadata_filter_defaults`, `reranker_enabled` (bool). This directly supports NFR-COST-002 (top-K and context budget as cost-control levers) and NFR-TEST-003 (regression evaluation of retrieval changes without redeploying code).

### 6.5 Future Retrieval Enhancement — Relevance Grading

Retrieved chunks can optionally pass through a **relevance grading** stage before context construction, positioned between deduplication (6.1 step 4) and final top-K selection (6.1 step 6).

**Purpose:**
- Remove chunks that are semantically similar to the query (and therefore pass embedding-based similarity search) but are not actually relevant to answering it.
- Improve overall context quality passed to the Prompt Assembler (5.6).
- Reduce unnecessary token consumption in the context payload (supports NFR-COST-001/002).
- Improve answer faithfulness (Section 9.3) by narrowing the context to genuinely supportive content.

**Scope for this revision (v1.0):** the system uses similarity thresholding (6.1 step 3) and the optional re-ranking hook (6.1 step 5) as its relevance controls. A dedicated relevance-grading stage is **not** part of v1.0 and is **not required** for the Phase 1–3 scope defined in Section 10.

**Future versions:** a relevance grader — e.g., a lightweight classifier or LLM-judged relevance check applied per candidate chunk — can be introduced as an additional pluggable stage using the same swappable-strategy pattern already established for re-ranking (6.1 step 5), without changing the Retriever's external input/output contract (5.4).

---

## 7. Citation Generation Strategy

This section elaborates the Citation Mapper component (5.8), the architectural mechanism that satisfies the SRS's citation-backed-answer mandate (FR-1201–1205) and directly supports BO-003 (trust through verifiable citations).

### 7.1 Citation Traceability Model

Every chunk that enters the Context Builder (5.5) carries its full citation metadata (`document_title`, `section_path`, `page_range`, `document_id`, `chunk_id`) from ingestion-time Metadata Extraction (4.5) through to generation. This metadata is never regenerated or inferred at query time — it is carried, unmodified, end-to-end. This is an architectural invariant: **citation data has a single source of truth (ingestion-time metadata extraction), never a runtime re-derivation.**

### 7.2 Answer-to-Source Mapping

The Prompt Assembler (5.6) instructs the LLM to reference which supplied context segment(s) support each part of its answer (FR-1003) — for example, by labeling context segments with stable reference tokens (e.g., `[source: chunk_id]`) inside the prompt, which the model is instructed to echo back inline. The Citation Mapper (5.8) then:

1. Parses the generated answer for these reference tokens.
2. Resolves each referenced token back to its full citation metadata (7.1) via the Context Builder's citation metadata map (5.5 output) — never by re-querying the vector store.
3. Produces a structured citation list distinct from the prose answer (FR-1204), so a downstream client can render citations separately from answer text.

### 7.3 Unverified Statement Detection

If the generated answer contains claims that do not resolve to any reference token from the supplied context — i.e., the model asserted something without tying it to retrieved content — the Citation Mapper flags `unverified_statement_flag: true` on the response (FR-1203) rather than silently dropping or silently trusting the unattributed claim. This flag is surfaced in the response contract, logged (FR-1503), and available to the evaluation harness (Section 9) to track the unverified-statement rate over time as a hallucination-risk *indicator* — not a certification that no hallucination occurred, consistent with the framing in Section 6.3.

### 7.4 No-Citation Guarantee on Declined Answers

The Section 5.10 "Not Found" path is architecturally forbidden from invoking the Citation Mapper — it produces a response with an empty citation list by construction, not by the Citation Mapper choosing to emit nothing (FR-1205). This removes an entire class of potential bugs where a "not found" response could accidentally carry stale or fabricated citations.

### 7.5 Citation Output Contract

```
{
  answer_text: string,
  citations: [
    { document_title: string, section_path: string | null, page_range: [int, int], document_id: string, chunk_id: string }
  ],
  unverified_statement_flag: boolean,
  truncated_context: boolean   // carried from 5.5, informs the consumer answer may be based on partial context
}
```

---

## 8. Cross-Cutting Concerns

These concerns apply uniformly across every stage in both pipelines and are architected as shared utilities invoked by stages and orchestrators, not as separate pipeline stages themselves.

### 8.1 Error Handling

- Every stage raises errors using a shared, catalogued error taxonomy (ingestion / parsing / embedding / retrieval / generation / configuration — FR-1401), each carrying a stable error code and contextual identifiers (document ID, chunk ID, session ID, correlation ID — FR-1402).
- The Orchestrators (4.8, 5.9) are the architectural layer responsible for classifying each error as recoverable (→ retry with backoff, NFR-REL-003) or non-recoverable (→ fail the unit of work, without crashing the surrounding batch/session — FR-1403, FR-1404).
- No partial pipeline output is ever surfaced to the end user as if complete (FR-1405) — a mid-pipeline failure always routes to an explicit error/degraded response, never a truncated success response.

### 8.2 Logging & Observability

- A shared logging utility is invoked by every stage and both orchestrators, emitting structured entries tagged with a correlation ID assigned at the start of each ingestion run or query request (FR-1502).
- Stage-level log entries capture, at minimum, stage name, duration, input identifiers (document/chunk/session ID), and outcome (FR-1501).
- Query-level aggregate logging captures the Query Analyzer's routing decision (5.2), retrieved chunk IDs + scores (when the `policy_query` path is taken), LLM model/version, generation latency, and citation outcome (FR-1503) — this is emitted by the Query Orchestrator (5.9) after the pipeline reaches any terminal path (5.8 Citation Mapper, Direct Response, or 5.10 Not Found).
- This same logging spine is the substrate for the metrics required by NFR-OBS-002 (request rate, error rate, per-stage latency percentiles, relevance score distribution, token usage) — metrics are derived from structured log events, not a separately instrumented code path, to avoid drift between what's logged and what's measured.

### 8.3 Configuration Management

- A single configuration-loading component is consulted by every stage and both orchestrators at startup; no stage reads raw environment variables or config files directly (FR-1601).
- Configuration is validated (types, ranges, required presence) at process startup, before any ingestion or query traffic is accepted — fail-fast (FR-1603).
- Secrets (API keys, DB credentials) are resolved through this same component from a secure source, never embedded in stage logic or logged (FR-1604, NFR-SEC-002).
- The configuration component exposes a redacted diagnostic view (secrets masked) for operational troubleshooting (FR-1605).

---

## 9. Evaluation Approach

Evaluation is architected as a **separate, offline harness** that exercises the same Query Pipeline (Section 5) components used in production, rather than a bespoke test-only code path — this is what makes NFR-TEST-001–004 achievable without divergence between "what we test" and "what we ship."

### 9.1 Evaluation Layers

1. **Stage-level unit evaluation.** Each pipeline stage (Sections 4, 5) is exercised in isolation with fixed inputs and asserted outputs, using stubbed Provider Abstractions (Section 3) so no live LLM/embedding/vector-DB call is required (NFR-TEST-001). This covers deterministic stages exhaustively (Chunker, Metadata Extractor, Context Builder's budget/truncation logic, Citation Mapper's reference-resolution logic).
2. **Pipeline integration evaluation.** The full ingestion-to-answer flow is run against a reproducible, version-controlled fixture set: a small corpus of representative HR policy PDFs plus a labeled question set with known correct source locations (NFR-TEST-002, ties to AC-003 in the SRS). This exercises real (or sandboxed) Provider Abstractions end-to-end.
3. **Retrieval quality evaluation.** Precision/recall of the Retriever (Section 6) against the labeled question set is computed and tracked as a regression gate — a retrieval or chunking configuration change is evaluated against this metric before being promoted, directly supporting NFR-TEST-003 and mitigating Risk R-007 (chunking misconfiguration silently degrading retrieval). See Section 9.2 for the specific metrics.
4. **Grounding/citation quality evaluation.** For each labeled question, the evaluation harness checks (a) whether the returned citations match the expected source location, and (b) whether `unverified_statement_flag` (Section 7.3) is set — the aggregate unverified-statement rate across the labeled set is tracked as a hallucination-risk indicator, supporting BO-003 and mitigating Risk R-002. See Section 9.3 for the specific metrics.
5. **Resilience evaluation.** Each Provider Abstraction (Section 3) can be run in a failure-simulation mode (forced timeout, forced error) to exercise the Error Handling concern (Section 8.1) end-to-end without depending on an actual provider outage (NFR-TEST-004).

### 9.2 Retrieval Evaluation Metrics

Retrieval quality (9.1, item 3) is measured with standard information-retrieval metrics computed against the labeled question set:

| Metric | Definition | What It Catches |
|---|---|---|
| Precision@K | Fraction of the top-K retrieved chunks that are actually relevant to the question | Irrelevant/noisy chunks diluting context |
| Recall@K | Fraction of all known-relevant chunks that appear within the top-K retrieved results | Relevant policy content missed entirely |
| Hit Rate@K | Whether at least one relevant chunk appears within the top-K results, per question | Binary retrieval success/failure at the question level |
| Mean Reciprocal Rank (MRR) | Average, across all evaluated questions, of 1 ÷ (rank of the first relevant chunk) | How high the correct chunk ranks, not just whether it's present |

**Example:**

> Question: *"What is maternity leave duration?"*
> Expected: the Leave Policy section containing maternity leave rules.
> Evaluation: check whether the expected chunk (identified by `chunk_id`, or by `document_id` + `section_path`) appears within the top-K results the Retriever (5.4) returns for this question, and at what rank.

### 9.3 Generation Evaluation Metrics

Generation quality (9.1, item 4) is measured on the final answer produced by the Response Generator (5.7) and Citation Mapper (5.8):

| Metric | Definition |
|---|---|
| Faithfulness | Whether every factual claim in the answer is supported by the retrieved context; correlates inversely with the `unverified_statement_flag` rate (Section 7.3) |
| Answer Relevance | Whether the answer actually addresses the question asked, independent of factual correctness |
| Completeness | Whether the answer covers all relevant aspects present in the retrieved context (e.g., all eligibility conditions, not just one) |
| Citation Correctness | Whether the citations attached to the answer (Section 7) point to the actual source of each claim, not merely a plausible-looking source |

**Clarification:** these metrics quantify observed system quality against a fixed labeled test set and drive the regression gate described in 9.1; they narrow and make hallucination *risk* measurable, but evaluation against a fixed test set does not guarantee zero hallucination on novel, unseen questions in production. This is consistent with the framing in Section 6.3 — the architecture reduces risk structurally and evaluation quantifies the residual risk; neither claims to eliminate it.

### 9.4 Evaluation Data Flow

```
 Fixture corpus (PDFs) ──► [Ingestion Pipeline, Section 4] ──► indexed knowledge base (test instance)
                                                                      │
 Labeled question set ──────────────────────────────────────────────┤
        │                                                            ▼
        │                                              [Query Pipeline, Section 5]
        │                                                            │
        ▼                                                            ▼
 expected {source_doc, section, page}          actual {citations[], unverified_statement_flag, answer_text}
        │                                                            │
        └──────────────────────► [Evaluation Harness: compare] ◄─────┘
                                          │
                Precision@K, Recall@K, Hit Rate@K, MRR,
        faithfulness, answer relevance, completeness,
              citation correctness, latency percentiles
                                          │
                                          ▼
                          Regression report (gates config/prompt changes)
```

### 9.5 What This Architecture Deliberately Does Not Fix

Consistent with `requirements_review_summary.md` (Missing Requirements #7), this architecture defines *how* evaluation is run but does not resolve *who* curates and maintains the labeled question set, nor the exact precision threshold gating release (SRS AC-003 leaves this as a placeholder). Those remain open governance questions, not architecture questions — see Section 11.

---

## 10. Implementation Scope

This architecture (Sections 1–9) describes the target system shape. Implementation proceeds incrementally across four phases; later phases build on earlier ones without requiring re-architecture of components delivered earlier, per the provider-abstraction and modularity principles in Section 1. This section exists to make the MVP boundary explicit and to separate "designed for" from "built now."

### Phase 1 — Core RAG MVP

The end-to-end grounded question-answering path, minimally viable:

- PDF ingestion (4.1)
- Parsing (4.2)
- Text preprocessing (4.3)
- Semantic chunking (4.4)
- Metadata extraction (4.5)
- Embedding generation (4.6)
- Vector storage (4.7)
- Similarity retrieval (5.4, Section 6.1 steps 1–4 and 6 — re-ranking as pass-through)
- Context construction (5.5)
- Prompt generation (5.6)
- LLM response generation (5.7)
- Citation mapping (5.8)

### Phase 2 — Engineering Hardening

Makes Phase 1 production-viable as software, not just functionally correct:

- Provider abstraction implementations (Section 3) as concrete, swappable adapters
- Configuration management (Section 8.3)
- Structured logging (Section 8.2)
- Error handling framework (Section 8.1)
- Evaluation harness (Section 9.1–9.4)
- Regression testing gated on retrieval and generation metrics (Section 9.2–9.3)

### Phase 3 — Production Readiness

Makes the system deployable and operable at enterprise scale:

- FastAPI service layer (thin adapter per Principle 3, Section 1)
- Docker deployment (C-006)
- Health checks (NFR-OBS-001)
- Metrics (NFR-OBS-002)
- External session storage (resolves Section 5.1's externalized-store design note)
- Scaling considerations (NFR-SCALE-001–003)

### Phase 4 — Agentic Extension

Explicitly out of scope for the architecture described in Sections 1–9, and not required for v1.0 acceptance (SRS Section 3.2). Noted here so the boundary is deliberate, not accidental:

- Employee context retrieval (e.g., role- or tenure-specific policy applicability)
- Policy reasoning workflows (multi-step reasoning across multiple policies)
- HR system integrations (e.g., leave-balance lookups)
- Tool-based decision support

The Query Analyzer (5.2) is intentionally scoped as a single-decision router, not a Phase 4 planner, so that Phase 4 — if pursued — extends the pipeline rather than replacing it.

---

## 11. Open Architectural Questions Carried Forward

The following items from `requirements_review_summary.md` Section 7 (Open Questions), plus one introduced by this revision, directly affect component design choices above and should be resolved before implementation begins:

| # | Question | Where It Affects This Architecture |
|---|---|---|
| 1 | Session identity source | Determines the Session Manager's (5.1) input contract — whether `session_id` is passed in from an external identity provider token or generated by this system |
| 2 | Conversation history storage mechanism | Determines what sits behind the Session Manager's (5.1) externalized store — this document specifies the contract, not the technology |
| 3 | Re-ranking requirement for v1.0 | Determines whether Section 6.1 step 5 ships as a real re-ranker or a pass-through identity function for v1.0 acceptance |
| 4 | "Nominal load" numeric definition | Needed to size the Retriever's (5.4) over-fetch candidate count and the Vector Store's expected concurrent-query throughput |
| 5 | Streaming default | Determines whether the Response Generator (5.7) defaults to streaming or blocking mode when the future FastAPI layer is added |
| 6 | Query Analyzer classification mechanism | Determines whether Section 5.2 uses rule-based heuristics, a lightweight classifier, or a small LLM call to categorize queries — affects latency (NFR-PERF-002) and cost (NFR-COST) budgets |

These are flagged here for traceability, not re-litigated — resolution is a stakeholder decision, not an architectural one.

---

*End of Document. This architecture specification is derived from and subordinate to [requirements.md](./requirements.md). Where any conflict exists, the SRS governs and this document should be revised to match.*

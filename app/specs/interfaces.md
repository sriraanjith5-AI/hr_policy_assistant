# Interface Contracts Specification

## Enterprise HR Policy Assistant — Internal Component Interfaces

| Field | Value |
|---|---|
| Document Type | Interface Contracts Specification |
| Project Name | Enterprise HR Policy Assistant |
| Version | 1.1 |
| Status | Revised — Final Review Before domain_models.md |
| Upstream Documents | [requirements.md](./requirements.md) (SRS v1.0), [rag_design.md](./rag_design.md) (RAG Architecture Design v1.1), [architecture.md](./architecture.md) (SAD v1.2) |
| Downstream Documents (not yet created) | `domain_models.md`, `sequence_diagrams.md`, `testing.md`, `deployment.md`, `tasks.md` |
| Prepared By | Principal AI Solution Architect |
| Date | 2026-07-29 |

---

## Document Control

`interfaces.md` is the fourth document in the Specification-Driven Development (SDD) chain for this project:

```
requirements.md → rag_design.md → architecture.md → interfaces.md → domain_models.md →
sequence_diagrams.md → testing.md → deployment.md → tasks.md → implementation
```

This document defines the **contracts** between the components `architecture.md` identified — orchestrators, pipeline stages, domain models, and provider interfaces/implementations. It answers **what each component exposes and consumes**, not how it is built internally. It contains no implementation code, no class definitions, no method signatures in any specific programming language, and no framework-specific types (no LangChain constructs, no FastAPI request/response types, no vendor SDK types). Every interface below is expressed in terms of Domain Model concepts (Section 6) and plain input/output/failure descriptions, so it stays valid regardless of which language or framework eventually implements it.

Per `architecture.md` Section 16, the **Query Analyzer** interface (Section 4.9 below) is defined here for architectural coherence, but its inclusion in mandatory implementation scope remains contingent on requirements alignment — this is called out again at that interface's definition, not assumed away.

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-07-29 | Initial Interface Contracts Specification |
| 1.1 | 2026-07-29 | Final review pass before `domain_models.md`: added an explicit dependency-direction diagram naming forbidden vendor SDKs (OpenAI, Chroma/Pinecone, HuggingFace, PDF libraries); added a `Dependencies` field to every pipeline stage interface; restructured the Orchestrator Interfaces intro into explicit Allowed/Not-allowed lists; added explicit "must not expose vendor objects" statements to all three Provider Interfaces; restructured Query Analyzer and Query Reformulator into Status/mechanism/possible-approaches fields; strengthened the Session Manager contract with the MVP-vs-distributed-storage statement and an explicit "no schema defined here" note; itemized the four not-found/business-outcome cases in Error Contracts so they cannot be misread as technical failures; added a new Interface Evolution section; renumbered the closing Related Documents section |

---

## 1. Purpose

`interfaces.md` defines the contracts between:

- **Orchestrators** — the Ingestion Orchestrator and Query Orchestrator (`architecture.md` Section 3, "Orchestration Layer").
- **Pipeline stages** — the ingestion and query stage sequences (`architecture.md` Section 3, "Pipeline Stage Layer").
- **Domain models** — the shared business vocabulary (`architecture.md` Section 3, "Domain Model Layer"; detailed shapes deferred to `domain_models.md`).
- **Provider implementations** — via the Provider Interfaces they satisfy (`architecture.md` Section 4).

**Purpose of defining these contracts explicitly, ahead of implementation:**

- **Enable independent development** — a stage's contract is enough for one engineer to build it while another builds an adjacent stage, without either needing to read the other's internals.
- **Support testing** — every contract below is a seam a test double can be substituted at (Section 9).
- **Allow component replacement** — a Provider Implementation, or even a Pipeline Stage's internal algorithm, can be swapped as long as the contract is honored (`architecture.md` Section 11, "Provider Independence").
- **Enforce separation of concerns** — a contract makes a component's *boundary* explicit, which is what makes `architecture.md`'s ownership rules (e.g., "orchestrators do not contain business rules," Section 3) checkable rather than aspirational.

---

## 2. Interface Design Principles

These four principles govern every contract defined in this document. They are not new — they are `architecture.md` Section 11's principles, restated here specifically as *interface* design rules.

### Dependency Inversion

Components depend on contracts, not implementations. A Pipeline Stage's declared dependency is always a Provider Interface (Section 5) or another stage's output contract (Section 4) — never a concrete Provider Implementation, and never another stage's internal logic. (`architecture.md` Section 3.0.)

### Provider Independence

External services are hidden behind interfaces. No contract in Section 4 or Section 5 references a vendor name, SDK type, or wire format — a contract is satisfied by any implementation that honors the input/output/failure shape, regardless of which vendor sits behind it. (`architecture.md` Section 4, 11.)

### Testability

Interfaces allow mock implementations. Every Provider Interface (Section 5) and every stage's dependency on one is defined precisely enough that a stubbed/mock implementation can satisfy it in a test without touching a live external system. (`architecture.md` Section 11; SRS NFR-TEST-001.)

### Single Responsibility

Each interface represents one capability. No interface in this document bundles two unrelated responsibilities (e.g., the Retriever's interface does not also expose citation-resolution behavior) — this mirrors `rag_design.md`'s one-stage-one-responsibility decomposition (Sections 4–5) and `architecture.md` Section 11.

### 2.1 Dependency Direction (Validated Against `architecture.md` v1.2)

Every contract in Sections 3–5 was checked against this direction. It must hold for every interface in this document, with no exceptions:

```
Orchestrators
    ↓
Pipeline Stage Interfaces
    ↓
Domain Models
    ↓
Provider Interfaces
    ↓
Provider Implementations
    ↓
External Systems
```

**Pipeline stages depend on:**
- Domain models (Section 6)
- Other stage contracts (their declared upstream input, Section 4)
- Provider Interfaces (Section 5) — never a Provider Implementation

**Pipeline stages must NOT depend on:**
- The OpenAI SDK, or any specific LLM vendor's client library
- The Chroma SDK, the Pinecone SDK, or any specific vector database's client library
- The HuggingFace SDK, or any specific embedding vendor's client library
- A PDF library's own implementation types (a Pipeline Stage may call a PDF parsing library at the point named in `architecture.md` Section 4, but its *interface* — Section 4.2 below — exposes only domain-shaped output, never a library-specific object)

No interface definition in this document names any of the above. Where a future reviewer or implementer is tempted to add a vendor type to a contract's input/output, that is a violation of this principle and should be rejected at review, not accepted as a convenience.

---

## 3. Orchestrator Interfaces

An orchestrator's contract is limited to workflow coordination. This boundary is enforced identically for both orchestrators below:

**Allowed:**
- Workflow sequencing
- Error propagation
- Execution context management (correlation ID, provenance, timing)
- Retry coordination

**Must NOT contain:**
- Retrieval rules (scoring, thresholding, re-ranking logic)
- Chunking rules (size, overlap, boundary decisions)
- Citation rules (what counts as a valid citation, resolution logic)
- HR policy logic (any decision about policy content itself)

Every rule above belongs to the relevant Pipeline Stage Interface in Section 4 — never to the orchestrator that sequences it. (`architecture.md` Section 3, "Orchestrator Responsibility Boundary".)

### 3.1 Ingestion Orchestrator Interface

**Responsibilities:**
- Coordinate ingestion stages (Document Loader → ... → Vector Indexer, Section 4) in sequence for a single document.
- Process documents individually within a batch, isolating one document's failure from the rest (SRS FR-1404).
- Handle batch execution: accept a document source (single or batch) and drive each through the full stage sequence.

**Inputs:**
- Document source (one or more source documents, each identified by a `Document` domain object or a reference resolvable to one — Section 6).
- Ingestion configuration (chunking, embedding model selection, etc. — sourced via the configuration mechanism, not passed ad hoc).

**Outputs:**
- Ingestion result: one result per input document, each reporting success, partial success (e.g., pages flagged reduced-fidelity), or failure, plus provenance and correlation identifiers (Section 8).

**Depends on (contracts, not implementations):** Document Loader, PDF Parser, Text Preprocessor, Semantic Chunker, Metadata Extractor, Embedding Generator, Vector Indexer interfaces (Section 4). Never a Provider Implementation or vendor SDK directly (Section 2.1).

**Explicitly does not:** decide chunking boundaries, decide what counts as "relevant" metadata, or retry an individual provider call directly (that retry policy is implemented by the relevant Provider Implementation, per `architecture.md` Section 10) — it only decides whether a stage's *reported* failure is recoverable or fails the current document (SRS FR-1401–1403).

### 3.2 Query Orchestrator Interface

**Responsibilities:**
- Coordinate the question-answering workflow: sequence Session Manager → Query Analyzer → (conditionally) Query Reformulator → Retriever → Context Builder → Prompt Assembler → Response Generator → Citation Mapper (Section 4).
- Manage the retrieval and generation flow's short-circuits: the Query Analyzer's `conversational`/`unsupported` routing, the empty-retrieval short-circuit, and the LLM-declines short-circuit (`rag_design.md` Section 5, Query Data Flow Diagram).
- Propagate errors from any stage as a classified (recoverable/non-recoverable) outcome (SRS FR-1401–1405).

**Inputs:**
- User query (raw text).
- Session context (a session identifier, resolved to a `ConversationSession` domain object via the Session Manager interface — Section 4.8).

**Outputs:**
- Response object: either a cited answer (`Response` + `Citation[]` domain objects, Section 6), a declined/"not found" response (no citations, by contract — `rag_design.md` Section 7.4), or a normalized error.

**Depends on (contracts, not implementations):** Session Manager, Query Analyzer, Query Reformulator, Retriever, Context Builder, Prompt Assembler, Response Generator, Citation Mapper interfaces (Section 4). Never a Provider Implementation or vendor SDK directly (Section 2.1).

**Explicitly does not:** score retrieval relevance, decide what constitutes a valid citation, or classify a query's topic itself — it only routes based on what the Query Analyzer and Retriever *report*.

---

## 4. Pipeline Stage Interfaces

Each interface below states its responsibility, input model, output model, dependencies, and failure scenarios, using Domain Model names from Section 6 rather than language-specific types. Where a stage's expected behavior on an edge case is a **valid, non-error outcome** (e.g., an empty retrieval result), it is listed separately from true failure scenarios — conflating the two would misrepresent `rag_design.md`'s explicit design intent (Section 5.9, 6.3; see also Section 7 below).

This section includes four stages beyond the reviewer-specified list — **Vector Indexer** (ingestion), and **Session Manager**, **Query Analyzer**, **Query Reformulator** (query) — because omitting them would leave `architecture.md`'s full Component Responsibilities table (Section 7) without contracts, reintroducing the same completeness gap that revision closed. Query Analyzer's contract (4.9) carries its provisional-scope note forward from `architecture.md` Section 16.

### Ingestion Stage Interfaces

#### 4.1 Document Loader Interface

- **Responsibility:** Validate and register a source document; assign a stable document identifier and provenance record.
- **Input:** Document location/source (raw file or reference).
- **Output:** `Document` (validated, with assigned ID and provenance).
- **Dependencies:** None — no upstream stage, no Provider Interface.
- **Failure scenarios:** malformed file; file exceeds configured size limit; file is encrypted in a way that blocks text extraction (SRS FR-107, FR-108, FR-206) — each is a non-recoverable failure for this document, reported without aborting a batch (SRS FR-1404).

#### 4.2 PDF Parser Interface

- **Responsibility:** Extract page-ordered text, structural markers, and table content from a validated document.
- **Input:** `Document` (validated, from 4.1).
- **Output:** Extracted document content — per-page text, structural elements, and an extraction-fidelity indicator per page.
- **Dependencies:** Document Loader (4.1) output. Calls a PDF parsing library at the External Infrastructure boundary (`architecture.md` Section 4), but this interface's own input/output is domain-shaped only — it never exposes a library-specific object (Section 2.1).
- **Failure scenarios:** a page is unparseable (e.g., scanned image) — **not treated as a hard failure**; the page is flagged reduced-fidelity/unparseable and processing continues (`rag_design.md` Section 4.2, FR-205). A true failure occurs only if the document as a whole cannot be opened/parsed at all.

#### 4.3 Text Preprocessor Interface

- **Responsibility:** Normalize extracted text (strip artifacts, deduplicate boilerplate, standardize encoding) while preserving the original raw text and structural cues.
- **Input:** Extracted document content (from 4.2).
- **Output:** Cleaned text (normalized) + a reference to the preserved raw text (SRS FR-305).
- **Dependencies:** PDF Parser (4.2) output. No Provider Interface.
- **Failure scenarios:** none expected to be non-recoverable at this stage under normal operation; an encoding that cannot be normalized should be reported as a data-quality warning attached to the affected page, not a hard failure, consistent with this stage's "preserve, don't discard" design intent (`rag_design.md` Section 4.3).

#### 4.4 Semantic Chunker Interface

- **Responsibility:** Split cleaned text into semantically bounded chunks per the configured target/max size and overlap.
- **Input:** Clean text (from 4.3) + chunking configuration.
- **Output:** Text chunks (`TextChunk[]`, unenriched — page range and section path attached, metadata not yet extracted).
- **Dependencies:** Text Preprocessor (4.3) output. No Provider Interface.
- **Failure scenarios:** a semantic unit exceeds the configured maximum size and must fall back to a hard split (`rag_design.md` Section 4.4) — this is expected, deterministic behavior, not a failure; a true failure would be malformed/empty input from the prior stage.

#### 4.5 Metadata Extractor Interface

- **Responsibility:** Attach structural and policy-domain metadata to each chunk; mark low-confidence fields explicitly null rather than guessing.
- **Input:** `TextChunk` (from 4.4) + document-level provenance (from 4.1) + extraction fidelity flags (from 4.2).
- **Output:** Chunk metadata (`DocumentMetadata` attached to the `TextChunk`).
- **Dependencies:** Semantic Chunker (4.4), Document Loader (4.1), PDF Parser (4.2) outputs. No Provider Interface.
- **Failure scenarios:** none that block the pipeline — an unextractable metadata field is represented as an explicit null (SRS FR-503), never a stage failure.

#### 4.6 Embedding Generator Interface

- **Responsibility:** Produce a vector embedding for each chunk via the Embedding Provider Interface (Section 5.1), recording the model/version used.
- **Input:** Text chunk (`TextChunk` + `DocumentMetadata`, from 4.5).
- **Output:** `Embedding` (vector + model/version), attached to the chunk.
- **Dependencies:** Metadata Extractor (4.5) output; Embedding Provider Interface (5.1).
- **Failure scenarios:** Embedding Provider failure (rate-limited, timeout, transient) — retried per configured policy; an unrecoverable per-chunk failure is reported without aborting the rest of the batch (SRS FR-605, NFR-REL-003).

#### 4.7 Vector Indexer Interface

- **Responsibility:** Persist embedded chunks (text + metadata + vector) to the vector index via the Vector Store Provider Interface (Section 5.2); on re-ingestion, atomically replace the prior document's chunks.
- **Input:** Embedded `TextChunk[]` (from 4.6), document ID.
- **Output:** Ingestion result summary (chunks indexed, chunks failed, pages flagged reduced-fidelity, status).
- **Dependencies:** Embedding Generator (4.6) output; Vector Store Provider Interface (5.2).
- **Failure scenarios:** Vector Store Provider unavailable or rejects an upsert — retried per configured policy; an unrecoverable failure is reported as this document's ingestion outcome without corrupting previously indexed documents (SRS NFR-REL-005).

### Query Stage Interfaces

#### 4.8 Session Manager Interface

- **Responsibility:** Resolve the incoming session identifier, load bounded conversation history, and expose a reset operation.
- **Status:** **The interface supports both MVP in-memory session management and future distributed session storage.** The contract below does not change between the two — only the concrete backing implementation does (`architecture.md` Section 3, "Session Management").
- **Possible future implementations:**
  - Redis
  - Database-backed storage
  - Distributed cache

  This document does not define a storage schema here — that is an implementation detail of whichever backing store is eventually chosen (ADR-007, `architecture.md` Section 17), out of scope for a contract-only specification.
- **Input:** Session identifier + current query text.
- **Output:** `ConversationSession` (bounded history + current query).
- **Dependencies:** A session store, behind this same interface boundary (in-memory for MVP, externalized for production). No other stage.
- **Failure scenarios:** session store unreachable (externalized deployments only) — treated as a recoverable failure subject to retry; on exhaustion, the Query Orchestrator proceeds with an empty history rather than blocking the request, and this degradation is logged (Section 8).

#### 4.9 Query Analyzer Interface — *provisional, pending requirements alignment*

> Per `architecture.md` Section 16: this interface is an architectural extension, not a confirmed SRS requirement. It is defined here so `interfaces.md` is internally coherent with `architecture.md`'s Pipeline Stage Layer, but implementers should treat it as provisional scope until `requirements.md` is updated or the extension is formally deferred.

- **Responsibility:** Classify the incoming query before any retrieval or generation work occurs, routing it to the full pipeline, a direct response, or a decline.
- **Status:** Architecture extension (not an approved FR).
- **MVP implementation:** Optional — the Query Orchestrator (3.2) can operate without this stage, routing every query directly to the Query Reformulator (4.10), if the extension is deferred per Section 16.
- **Classification mechanism:** Not decided. This contract fixes only the input/output shape below, not how the category is derived.
- **Possible future approaches:**
  - Deterministic rules
  - A classifier model
  - LLM-assisted routing
- **Input:** `ConversationSession` (from 4.8).
- **Output:** Query category (`policy_query` / `conversational` / `unsupported`) + an optional direct-response text.
- **Dependencies:** Session Manager (4.8) output; optionally the LLM Provider Interface (5.3) if an LLM-assisted approach is selected.
- **Failure scenarios:** classification mechanism failure — falls back to a configured default category (implementer's choice, not fixed by this contract) rather than blocking the request; the classification mechanism itself is an open ADR (`architecture.md` ADR-008), not fixed by this interface.

#### 4.10 Query Reformulator Interface

- **Responsibility:** Resolve ambiguous follow-up queries (e.g., pronoun references) into a self-contained retrieval query using conversation history.
- **Status:** Supported extension (distinct from Query Analyzer — this stage has an established basis in `rag_design.md` FR-1304 and is not tracked in Section 16 as pending alignment).
- **Mechanism:** Not fixed.
- **Possible implementations:**
  - Deterministic transformation
  - LLM-assisted rewriting
- **Input:** Current query + `ConversationSession` (from 4.8), for queries classified `policy_query` (from 4.9, when present) or all queries (when Query Analyzer is deferred, per 4.9's MVP note).
- **Output:** Reformulated query (text) + original query (retained).
- **Dependencies:** Session Manager (4.8) output, Query Analyzer (4.9) routing decision when present; optionally the LLM Provider Interface (5.3) if an LLM-assisted approach is selected.
- **Failure scenarios:** reformulation mechanism failure — falls back to using the original query unmodified rather than blocking the request (a deliberate degrade-gracefully behavior, not a hard failure).

#### 4.11 Retriever Interface

- **Responsibility:** Embed the reformulated query, execute similarity search (optionally metadata-filtered) against the Vector Store Provider Interface, apply the relevance threshold, deduplicate, and optionally re-rank.
- **Input:** Query embedding (derived from the reformulated query via the Embedding Provider Interface, Section 5.1) + retrieval configuration (top-K, threshold, filters).
- **Output:** Ranked search results (`SearchResult[]`), **possibly empty** — an empty result is a valid, expected output, not a failure (`rag_design.md` Section 6.3), and is the trigger for the Query Orchestrator's "Not Found" short-circuit.
- **Dependencies:** Query Reformulator (4.10) output; Embedding Provider Interface (5.1); Vector Store Provider Interface (5.2).
- **Failure scenarios:** Vector Store Provider or Embedding Provider unavailable/erroring — a true failure, retried per configured policy, distinct from the empty-result case above.

#### 4.12 Context Builder Interface

- **Responsibility:** Assemble retrieved chunks (and relevant conversation history) into a token-budgeted, deterministically ordered context package, truncating and recording truncation when the budget is exceeded.
- **Input:** Retrieved chunks (`SearchResult[]`, from 4.11) + `ConversationSession` (from 4.8) + context token budget (config).
- **Output:** Context package (ordered context chunks + citation metadata map + a truncation flag).
- **Dependencies:** Retriever (4.11) output; Session Manager (4.8) conversation history. No Provider Interface.
- **Failure scenarios:** none that block the pipeline under normal operation; exceeding the token budget is expected, handled behavior (truncation + flag), not a failure.

#### 4.13 Prompt Assembler Interface

- **Responsibility:** Render the versioned prompt template with system instructions, the context package, conversation history, and the current query.
- **Input:** Query + context (context package from 4.12, original/reformulated query).
- **Output:** Prompt (a fully rendered prompt payload ready for the LLM Provider Interface).
- **Dependencies:** Context Builder (4.12) output; prompt template configuration. No Provider Interface.
- **Failure scenarios:** configured prompt template missing or malformed — a configuration error (Section 7), surfaced at startup validation where possible (SRS FR-1603) rather than per-request.

#### 4.14 Response Generator Interface

- **Responsibility:** Submit the assembled prompt to the LLM Provider Interface (Section 5.3) and return the generated response, in blocking or streaming mode per configuration.
- **Input:** Prompt (from 4.13) + generation configuration.
- **Output:** Generated response (text or stream) + token usage + finish reason.
- **Dependencies:** Prompt Assembler (4.13) output; LLM Provider Interface (5.3).
- **Failure scenarios:** LLM Provider failure, normalized to one of: rate-limited, timeout, refused, transient, unknown (`architecture.md` Section 4, "LLM Provider"). A `refused` or context-insufficient finish reason is not itself an error — it routes to the Query Orchestrator's "Not Found" short-circuit, same as an empty retrieval.

#### 4.15 Citation Mapper Interface

- **Responsibility:** Resolve the generated response's references back to source citations using the citation metadata carried from the Context Builder; flag any claim that cannot be traced to retrieved content.
- **Input:** Generated response (from 4.14) + citation metadata (from 4.12).
- **Output:** Citation-backed response (`Response` + `Citation[]` + an `unverified_statement_flag`).
- **Dependencies:** Response Generator (4.14) output; Context Builder (4.12) citation metadata. No Provider Interface.
- **Failure scenarios:** none that block the pipeline — an unresolvable reference sets the unverified-statement flag (`rag_design.md` Section 7.3) rather than failing the request; a true failure would only occur if the citation metadata map itself is missing/corrupted, which is a defect in the Context Builder's contract, not a normal Citation Mapper failure mode.

---

## 5. Provider Interfaces

These are the three interfaces `architecture.md` Section 4 defines as the *only* points where a Provider Implementation may import a third-party SDK. Every contract below is intentionally silent on vendor identity, wire protocol, and authentication mechanism — those are Provider Implementation concerns, not interface concerns.

### 5.1 Embedding Provider Interface

**Responsibilities:**
- Generate document embeddings (batch, for chunks at ingestion time).
- Generate query embeddings (single, for a query at retrieval time).
- Expose model metadata (model name/version) as first-class output alongside every embedding produced.

**Must not expose:**
- OpenAI-specific objects
- HuggingFace-specific objects
- Any other vendor SDK's native embedding-response type

**Inputs:** Text (a chunk's text, or a query's text).

**Outputs:** Vector representation (`Embedding`) + model version.

**Failure scenarios:** rate-limited, timeout, or transient provider error — classified for retry per `architecture.md` Section 10; a persistent failure is reported to the calling stage (4.6, 4.11) as an unrecoverable failure for that unit of work.

### 5.2 Vector Store Provider Interface

**Responsibilities:**
- Store vectors (upsert chunk text + metadata + embedding; delete by document ID; atomic replace on re-ingestion).
- Search vectors (similarity search given a query embedding and top-K).
- Apply metadata filters as an optional predicate on the same search call, not a separate code path (`rag_design.md` Section 6.2).
- Return domain-level search results (`SearchResult[]`) — never a vendor-native response object.

**Must not expose:**
- Chroma-specific objects
- Pinecone-specific objects
- Any other vector database's native response or query-builder type

**Inputs:** Embeddings (for storage) or a query embedding + search criteria (top-K, optional metadata filter, optional similarity threshold) (for search).

**Outputs:** Search results (`SearchResult[]`, ranked) for search calls; success/failure per chunk for storage calls.

**Failure scenarios:** unavailable/erroring provider — classified for retry; a model/version mismatch between a query embedding and the indexed chunks should be detectable (`rag_design.md` Section 3.1, Risk R-003) and reported rather than silently degrading relevance.

### 5.3 LLM Provider Interface

**Responsibilities:**
- Generate responses (blocking or streaming) from a fully assembled prompt.
- Support configurable model parameters (model selection, temperature, max tokens, timeout) without requiring code changes to the calling stage.
- Normalize provider failures into the shared taxonomy (rate-limited / timeout / refused / transient / unknown), so no calling stage branches on a vendor-specific error type.

**Must not expose:**
- Any vendor SDK's response object (e.g., a provider-specific completion/message object) — only the domain-shaped output below.

**Inputs:** Prompt (a fully rendered prompt payload).

**Outputs:** Generated response (text or a stream of text deltas) + token usage + finish reason.

**Failure scenarios:** normalized into rate-limited / timeout / refused / transient / unknown (`architecture.md` Section 4), so the Response Generator (4.14) and Query Orchestrator (3.2) never branch on a vendor-specific error type.

---

## 6. Domain Model Contracts

The objects below are the vocabulary every interface in Sections 3–5 is expressed in terms of. **This section names them; it does not define their attributes** — field-level shapes, types, and validation rules belong to the forthcoming `domain_models.md`, per `architecture.md` Section 3 ("Domain Model Layer").

- `Document` — a source policy document and its provenance.
- `Chunk` (`TextChunk`) — a semantically bounded segment of a document, pre- and post-enrichment.
- `Metadata` (`DocumentMetadata`) — structural and policy-domain metadata attached to a chunk or document.
- `Embedding` — a vector representation plus the model/version that produced it.
- `Query` — an employee's question, in original and (where applicable) reformulated form.
- `SearchResult` — a ranked retrieval candidate (chunk text + metadata + relevance score).
- `Citation` — a resolved reference from an answer back to its source document/section/page.
- `Response` — a generated answer, with or without attached citations, including the unverified-statement flag.
- `Session` (`ConversationSession`) — a session's identity and bounded conversation history.

Every interface in Sections 3–5 above consumes and/or produces one or more of these objects — no interface in this document introduces a data shape outside this list without it being one of these nine names or a direct composition of them (e.g., "Ingestion result summary" in Section 4.7 is a composition of `Document` + per-`Chunk` outcomes, not a tenth undocumented type).

---

## 7. Error Contracts

Per SRS FR-1401, every component in this document raises errors from a **shared, catalogued taxonomy**, not ad hoc per-component error types:

| Category | Applies to |
|---|---|
| Validation errors | Document Loader (4.1) — malformed/oversized/encrypted input |
| Parsing errors | PDF Parser (4.2) — document-level parse failure (not per-page fidelity flags, which are not errors) |
| Embedding failures | Embedding Generator (4.6), Embedding Provider Interface (5.1) |
| Retrieval failures | Retriever (4.11), Vector Store Provider Interface (5.2) — distinct from an empty-but-successful retrieval |
| LLM failures | Response Generator (4.14), LLM Provider Interface (5.3) |
| Citation validation failures | reserved for a defect in the citation metadata map itself (Context Builder, 4.12); an unresolved *reference* is a flag, not this category (Section 4.15) |
| Configuration errors | any component reading invalid/missing configuration at startup (SRS FR-1603) |

**Errors should be normalized so orchestrators can handle them consistently.** Concretely: every error, regardless of category, carries (a) a stable error code, (b) a category from the table above, (c) a recoverable/non-recoverable classification (SRS FR-1403), and (d) the observability metadata in Section 8. This uniform shape is what lets the Ingestion Orchestrator (3.1) and Query Orchestrator (3.2) apply one retry/fail policy across every stage and provider, instead of a per-component special case — consistent with `architecture.md`'s Orchestrator Responsibility Boundary (Section 3).

### Not Error Conditions — Valid Application Outcomes

The following four cases must **never** be classified into the error taxonomy above, regardless of how "failure-like" they may look at the calling layer. Each is a first-class, successful outcome of the pipeline (`rag_design.md` Section 5.9–5.10, 6.3, 7.3–7.4):

1. **No retrieval result** — the Retriever (4.11) returning an empty `SearchResult[]` because nothing met the relevance threshold. This triggers the "Not Found" short-circuit, not an error.
2. **Insufficient context** — the LLM Provider (5.3) reporting that the supplied context is insufficient to answer. Reported as a normal finish-reason outcome from the Response Generator (4.14), not a provider failure.
3. **LLM refusal due to grounding** — the LLM declining to answer *because* the prompt instructs it to answer only from supplied context (`rag_design.md` Section 6.3). This is the grounding design working as intended, not a `refused`-category technical failure (which is reserved for the LLM Provider genuinely rejecting the request on policy/content grounds unrelated to grounding intent).
4. **Unverified citation flag** — the Citation Mapper (4.15) setting `unverified_statement_flag` on a response. This is a quality signal attached to a successful response, not a Citation Validation failure (Section 7 table).

A component or orchestrator that maps any of these four into the error taxonomy above should be treated as a contract violation, not a defensible implementation choice — it would misrepresent a designed business outcome as a system fault, undermining the observability data in Section 8 and the evaluation metrics in `rag_design.md` Section 9.

---

## 8. Observability Contracts

Every interface call in Sections 3–5 — orchestrator, stage, or provider — carries the following metadata, per SRS FR-1501–1503 and NFR-OBS-002/003:

| Field | Description |
|---|---|
| Correlation ID | Identifies all activity belonging to one ingestion run or one query request, across every stage and provider call it triggers. |
| Request ID | Identifies this specific call/invocation within the correlation ID's scope (distinguishes retries and sub-calls). |
| Execution timestamp | When this call started (and, on completion, ended). |
| Component name | Which orchestrator, stage, or provider interface produced this record. |
| Processing duration | Elapsed time for this call, used for the per-stage latency percentiles in NFR-OBS-002. |
| Error information | Present only on failure: error code, category (Section 7), recoverable/non-recoverable classification. |

This is the metadata shape referenced, but not re-derived, by `architecture.md` Section 10 ("Logging and Observability") — every contract in this document implicitly includes emitting this record as part of its behavior, without treating it as a separate interface to be called out per component.

---

## 9. Testing Support

**Interfaces enable:**
- Mock providers
- Isolated stage testing
- Failure simulation
- Integration testing

This is possible because every contract in Sections 3–5 is a seam (SRS NFR-TEST-001–004):

- **Mock providers.** Any Provider Interface (Section 5) can be satisfied by a test double instead of a real Provider Implementation — a stage under test never needs a live LLM, embedding API, or vector database connection.
- **Isolated stage testing.** Deterministic stages (Semantic Chunker 4.4, Context Builder 4.12, Citation Mapper 4.15) can be tested with fixed `TextChunk`/`SearchResult`/`Response` inputs and asserted outputs, with no provider involved at all.
- **Failure simulation.** Any Provider Interface's mock can be configured to return a specific failure category (Section 7) — timeout, rate-limited, refused — to verify an orchestrator's retry/non-retry classification without depending on an actual provider outage.
- **Integration testing.** The full Ingestion Orchestrator (3.1) or Query Orchestrator (3.2) can be exercised end-to-end against stubbed Provider Interfaces, verifying the orchestrator's sequencing and short-circuit behavior without live external calls (`rag_design.md` Section 9.1).

**Example:** the Retriever (4.11) can be tested using a mock `VectorStoreProvider` that returns a fixed `SearchResult[]` (including the empty-list case) — this verifies the Retriever's threshold filtering, deduplication, and empty-result short-circuit trigger, entirely independent of which real vector database is eventually selected (`architecture.md` ADR-003).

---

## 10. Interface Evolution

Interfaces may evolve as the system grows. This section states the guidelines this document's contracts are expected to follow once implementation begins — it does not implement version numbers now, and no contract in Sections 3–5 above carries an individual version tag at this stage.

**Guidelines:**
- **Maintain backward compatibility where possible.** A contract change that only adds an optional field, or narrows a failure scenario into more specific sub-categories, should not require every caller to change simultaneously.
- **Avoid breaking changes without migration.** A contract change that removes or repurposes an existing input/output field is a breaking change and requires a migration path (e.g., a transition period where both shapes are accepted) — it should not be introduced silently.
- **Provider replacement should not impact pipeline contracts.** Swapping a Provider Implementation (e.g., changing which vector database backs the Vector Store Provider Interface, ADR-003) must never require a change to any Pipeline Stage Interface in Section 4 — if it does, the boundary was drawn incorrectly and Section 2.1's dependency direction has been violated somewhere.

Formal versioning scheme (e.g., how a contract change is numbered, communicated, and deprecated) is deferred to `testing.md` and `tasks.md`, later in the SDD chain — this section establishes intent only.

---

## 11. Related and Forthcoming Documents

- [requirements.md](./requirements.md) — the source of truth for *what* the system must do.
- [rag_design.md](./rag_design.md) — the source of truth for pipeline-internal design, retrieval strategy, and citation mechanics that these contracts implement.
- [architecture.md](./architecture.md) — the source of truth for system-level layering, ownership boundaries, and the Dependency Inversion model these contracts are expressed under.
- `domain_models.md` (not yet created) — will define the field-level shapes of every object named in Section 6.
- `sequence_diagrams.md` (not yet created) — will show these contracts invoked in sequence for the primary flows (`rag_design.md` Section 5, 9.2 data flow diagrams, expressed as sequence diagrams).
- `testing.md` (not yet created) — will formalize the testing approach outlined in Section 9 into a concrete test plan, and the versioning scheme referenced in Section 10.
- `deployment.md`, `tasks.md` (not yet created) — later in the SDD chain; out of scope here.

Where this document and an upstream document disagree, the upstream document governs, per the SDD chain order above.

---

*End of Document.*

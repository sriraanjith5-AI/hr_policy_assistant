# System Architecture Design Document (SAD)

## Enterprise HR Policy Assistant — RAG System Architecture

| Field | Value |
|---|---|
| Document Type | System Architecture Design Document (SAD) |
| Project Name | Enterprise HR Policy Assistant |
| Version | 1.2 |
| Status | Revised — Final Review Before interfaces.md |
| Upstream Documents | [requirements.md](./requirements.md) (SRS v1.0), [rag_design.md](./rag_design.md) (RAG Architecture Design v1.1) |
| Downstream Documents (not yet created) | `interfaces.md` (provider and stage contracts), `domain_models.md` (data/entity shapes) |
| Prepared By | Principal AI Solution Architect |
| Date | 2026-07-29 |

---

## Document Control

This SAD sits **above** `rag_design.md`. Where `rag_design.md` defines the RAG pipeline's internal stage-by-stage design (component responsibilities, retrieval strategy, citation mechanics, evaluation approach), this document defines the **system-level view**: who and what the system talks to, how the codebase is layered, how it deploys, and which technology decisions remain open. It intentionally does not restate pipeline internals in full detail — see `rag_design.md` Sections 4–9 for that level of depth, referenced throughout below rather than duplicated.

This document does not define code structures, classes, or method signatures. Those belong in the forthcoming `interfaces.md` (contracts between orchestration, stages, and provider abstractions) and `domain_models.md` (chunk, citation, session, and configuration data shapes) — both out of scope here and explicitly deferred (see Section 18).

Per the SRS's Specification-Driven Development mandate (Constraint C-008), this document is reviewed and approved before implementation begins, alongside `requirements.md` and `rag_design.md`.

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-07-29 | Initial System Architecture Design Document |
| 1.1 | 2026-07-29 | Incorporated architecture review feedback: corrected the layered diagram to express Dependency Inversion explicitly (Provider Interfaces vs. Provider Implementations, rather than one undifferentiated downward layer); added a Domain Model Layer; added a first-class Evaluation Architecture section; clarified Query Analyzer MVP-vs-future scope; refined session-storage wording to avoid mandating a specific backing store for the MVP; restructured the technology section into Decided vs. Open (ADR-required); added an Architecture Decisions Requiring ADRs section; renumbered subsequent sections and corrected several stale internal cross-references carried over from v1.0 |
| 1.2 | 2026-07-29 | Final review pass before `interfaces.md`: clarified Domain Model Layer ownership and the provider-implementation translation boundary (with a worked example); made the Orchestration Layer's non-business-rule boundary explicit (allowed vs. not-allowed responsibilities); expanded the dependency-direction explanation to name the three SDK families pipeline stages must never import; reframed the Query Analyzer as a tracked architectural extension pending requirements alignment, not accepted MVP scope by default; refined session-storage wording to name concrete future backing-store options without mandating any; strengthened the Evaluation Architecture responsibilities list; added a new Architecture Extensions Requiring Requirements Alignment section; recategorized the ADR candidate list into Architectural / Technology / Future Capability groups and added a Domain Model Ownership candidate; corrected a stale cross-reference (Query Analyzer non-goal note pointed at the wrong section for Future Evolution) |

---

## 1. Architecture Overview

### System Purpose

The Enterprise HR Policy Assistant is a Retrieval-Augmented Generation (RAG) system that lets employees ask natural-language questions about internal HR policy and receive answers grounded in, and cited against, the organization's actual policy documents.

### Business Problem Addressed

Employees currently resolve HR policy questions by searching static documents or filing tickets with HR — both slow, and both a source of repeated load on HR staff for questions that are already answered in existing policy text (SRS BO-001, BO-002). The system addresses this by making policy content queryable in natural language while preserving traceability back to the source document, so answers remain auditable rather than being treated as an opaque black box (BO-003).

### Architectural Goals

1. Ground every substantive answer in retrieved, citable source content — not the LLM's parametric knowledge (SRS FR-1002, FR-1106).
2. Keep the system fully explainable and inspectable at the architecture level: every stage has a defined input/output contract and can be reasoned about, tested, and replaced independently (SRS NFR-MOD-001–003).
3. Avoid vendor and framework lock-in at every external boundary — embeddings, vector storage, and LLM generation are each swappable (SRS NFR-EXT-001–003, C-007).
4. Keep transport (how a request reaches the system) fully decoupled from the RAG logic itself, so the same core can be driven by a script, a test harness, or a future HTTP API without modification (SRS C-004, C-005).
5. Make the system's own hallucination-risk posture honest and measurable rather than asserted — structural controls reduce risk, evaluation quantifies what remains (`rag_design.md` Section 6.3, 9.3).

### Key Design Principles

This SAD inherits, and does not restate in full, the architectural principles established in `rag_design.md` Section 1. In summary:

- **Custom RAG orchestration** — no LangChain or equivalent orchestration framework; a purpose-built Orchestrator sequences pipeline stages (SRS C-001/C-002, `rag_design.md` Section 1 Principle 1).
- **Stage-based pipeline architecture** — every pipeline responsibility (parsing, chunking, retrieval, prompt assembly, generation, citation mapping, etc.) is an independently addressable component with an explicit contract, not steps folded into one large function (`rag_design.md` Section 1 Principle 5, Sections 4–5).
- **Provider abstraction** — the only three points where third-party SDKs are touched (embeddings, vector store, LLM) sit behind narrow interfaces; nothing else in the system calls a vendor SDK directly (SRS C-003, `rag_design.md` Section 3).
- **Retrieval-grounded generation** — the LLM is only invoked with retrieved context attached, and is instructed to answer only from that context (SRS FR-1002, `rag_design.md` Section 5, 6.3).
- **Citation traceability** — citation metadata has a single source of truth (ingestion-time extraction) and is carried unmodified through to the final answer, never re-derived at query time (`rag_design.md` Section 7.1).
- **Testability** — deterministic stages (chunking, context budgeting, citation resolution) require no live external call to unit test; the full pipeline is testable against stubbed providers (SRS NFR-TEST-001–004).
- **Extensibility** — new document formats, providers, or a re-ranking/relevance-grading stage can be introduced without altering unrelated components (SRS NFR-EXT-001–005, `rag_design.md` Section 6.5).
- **Separation between core RAG logic and the transport/API layer** — core logic has no dependency on FastAPI or any serving framework; a future API layer is a thin adapter that calls into the core, never the reverse (SRS C-004/C-005, Section 3 below).

**The system is designed as a modular stage-based RAG pipeline where orchestration logic controls execution flow while individual stages remain independently testable and replaceable.** This sentence is the architectural thesis of the entire system and is the lens through which every section below should be read: orchestration owns *sequencing and error/short-circuit handling*; stages own *transformation logic*; provider abstractions own *external I/O*. No layer does another layer's job.

---

## 2. System Context Architecture

### Actors

| Actor | Role |
|---|---|
| **Employee** | Submits natural-language HR policy questions and receives cited answers. The system's primary end user. Authenticated identity is assumed to arrive from an external identity provider (SRS AS-002) — this system does not implement authentication itself. |
| **HR Policy Owner** | Supplies and maintains the authoritative source HR policy PDFs; triggers (or authorizes) ingestion of new/updated documents; is accountable for the correctness of source content (SRS AS-008). |
| **System Administrator** | Operates the system: manages configuration (Section 10), monitors observability signals, manages ingestion runs and re-ingestion of updated policies, and is the actor with authority to delete/replace documents in the knowledge base (SRS FR-106, FR-1601–1605). |

### External Dependencies

| Dependency | Responsibility Boundary |
|---|---|
| **LLM Provider** | Accepts a fully-assembled, grounded prompt and returns generated text (or a stream of tokens) plus usage/finish-reason metadata. It has **no** knowledge of the retrieval process, the vector store, or citation logic — it only ever sees what the Prompt Assembler hands it. Accessed exclusively through the LLM Provider Interface (`rag_design.md` Section 3.3). |
| **Embedding Provider** | Converts text (a chunk at ingestion time, or a query at request time) into a vector. It has no awareness of documents, chunks, or retrieval — it is a stateless text-to-vector function from the system's perspective. Accessed exclusively through the Embedding Provider Interface (`rag_design.md` Section 3.1). |
| **Vector Database** | Persists chunk text, metadata, and embeddings, and answers similarity-search queries (optionally metadata-filtered). It owns storage and search execution only — it does not know what a "citation" or a "policy category" *means*, it only stores and filters on the metadata fields the system gives it. Accessed exclusively through the Vector Store Interface (`rag_design.md` Section 3.2). |
| **Document Storage** | Persists the original, raw extracted document text (distinct from the vector database's retrieval-optimized chunk storage), for audit purposes (SRS FR-305, `rag_design.md` Section 4.9 — the "Document Store"). This is a system-owned supporting store, not a third-party SaaS dependency in the same sense as the three above, but it is drawn as an external dependency here because its storage technology is not fixed by this architecture (see Section 12). |

The common thread across all four: **the core system owns all business meaning (what a citation is, what "relevant" means, what a grounded answer is); every external dependency is treated as a narrow, swappable capability provider, never as a source of business logic.** This is the architectural expression of SRS C-003 and C-007.

### Core System

**Enterprise HR Policy Assistant** — the custom-orchestrated RAG pipeline described in full in `rag_design.md`, comprising the Ingestion Workload and the Query-Serving Workload (`rag_design.md` Section 2).

### Context Diagram

```
                    ┌───────────────────┐
                    │      Employee       │
                    └──────────┬──────────┘
                               │ asks a question
                               ▼
                 ┌───────────────────────────────┐
                 │   Enterprise HR Policy          │
                 │   Assistant (core system)       │
                 └───────────────┬─────────────────┘
                                 │
              ┌──────────────────┼───────────────────┐
              ▼                  ▼                    ▼
   ┌─────────────────┐ ┌──────────────────┐ ┌──────────────────┐
   │  Vector Database   │ │   LLM Provider     │ │ Embedding Provider │
   │  (chunk search)    │ │  (answer gen.)     │ │ (text → vector)    │
   └─────────────────┘ └──────────────────┘ └──────────────────┘
              ▲
              │ indexed by
              │
   ┌────────────────────────────┐
   │  Document Ingestion Pipeline │◄──────────── triggers/supplies documents
   │  (part of the core system)   │
   └────────────────────────────┘
              ▲
              │ supplies source PDFs
              │
   ┌───────────────────┐
   │  HR Policy Owner     │
   └───────────────────┘

   ┌───────────────────┐
   │ System Administrator │──► configures, operates, monitors, and manages
   └───────────────────┘      documents/config across both workloads
```

Note on the Embedding Provider's position in the diagram: it is drawn beneath the Vector Database because, architecturally, the Vector Store Interface's similarity search depends on a query embedding that the Embedding Provider produces first (`rag_design.md` Section 6.1, step 1) — this is a sequencing relationship at query time, not a structural dependency (the core system calls both interfaces directly; the Vector Database does not call the Embedding Provider itself).

---

## 3. Logical Architecture

The codebase is organized into layers. Section 3.0 below corrects a simplification carried over from the previous revision of this document, where "Provider Abstraction" was drawn as a single, ordinary downward layer — that framing obscured the Dependency Inversion Principle that the provider boundary actually depends on. The corrected model is what makes Section 1's thesis ("orchestration controls flow, stages remain independently testable and replaceable") architecturally enforceable rather than aspirational.

### 3.0 Dependency Direction (Corrected Conceptual Model)

```
Application Layer
        ↓
Orchestration Layer
        ↓
Pipeline Stage Layer
        ↓
Domain Model Layer
        ↓
Provider Interfaces

Provider Implementations
        ↓
External Infrastructure
```

**Provider Interfaces** and **Provider Implementations** are drawn as two separate boxes, not one, because they depend in opposite directions:

- Pipeline Stages depend **downward** on Provider Interfaces — contracts only, never a concrete SDK.
- Provider Implementations depend **downward** on External Infrastructure (the actual vendor SDK) and separately **implement** (satisfy) the Provider Interfaces from outside the business-logic chain.

This is Dependency Inversion applied at the system's one real external boundary: both the high-level pipeline logic and the low-level SDK integration depend on the same abstraction — the interface — but the interface itself depends on neither. The previous single-box "Provider Abstraction Layer" was correct about *what* sits at that boundary but did not make this inversion visible.

**In practice:**
- Core application code depends on provider contracts (the interfaces), not on any specific vendor's client library.
- Provider implementations depend on external SDKs — that dependency is isolated to the implementation, and does not leak upward.
- Pipeline stages must never directly import:
  - LLM SDKs (e.g., an LLM vendor's client library)
  - Vector database SDKs (e.g., a vector store's client library)
  - Embedding SDKs (e.g., an embedding provider's client library)

**Example:** the core system depends on the `LLMProvider` interface — it does not depend on, say, an OpenAI SDK client. Only the concrete Provider Implementation that satisfies `LLMProvider` imports that SDK; no Pipeline Stage, Orchestrator, or Domain Model ever does.

### Application Layer

**Responsibilities:**
- Future API exposure (e.g., HTTP endpoints for asking a question or triggering ingestion).
- Request validation at the transport boundary (distinct from business-rule validation, which lives in Pipeline Stages).
- Response formatting for the calling client (e.g., HTTP status codes, JSON envelope).
- The integration point where an external authentication mechanism (SRS AS-002) attaches caller identity before a request reaches the Orchestration Layer.

**Constraint:** Core RAG logic must not depend on FastAPI, or any other transport framework. This layer is optional for the MVP (Section 8, MVP Deployment) — the Orchestration Layer's entry points can be called directly (e.g., from a script or test harness) without this layer existing yet.

### Orchestration Layer

Custom control flow — explicitly not a framework-managed chain (SRS C-001/C-002). Two orchestrators, sharing no runtime state (`rag_design.md` Section 4.8, 5.9):

**Ingestion Orchestrator** — responsibilities:
- Control the document processing workflow, sequencing Pipeline Stage Layer components for ingestion (`rag_design.md` Section 4.1–4.7).
- Execute ingestion stages in order, per document.
- Handle batch processing failures: isolate a single document's failure so it does not abort the rest of a batch (SRS FR-1404).
- Maintain execution context per document (correlation ID, provenance) across the stage sequence for logging (SRS FR-1502).

**Query Orchestrator** — responsibilities:
- Control the question-answering workflow, sequencing Pipeline Stage Layer components for a single query (`rag_design.md` Section 5.1–5.10).
- Execute the retrieval pipeline, including the Query Analyzer's routing decision and the empty-retrieval and LLM-declines short-circuits (`rag_design.md` Section 5.9).
- Manage error handling: classify each stage failure as recoverable (retry) or non-recoverable (fail this request without crashing the process), per SRS FR-1401–1405.
- Coordinate citation generation as the final step before returning a response, ensuring the Citation Mapper only runs on the path that reached actual generation (`rag_design.md` Section 5.8, 5.10).

#### Orchestrator Responsibility Boundary

**Orchestrators coordinate workflow execution but do not contain business rules.** This boundary applies identically to both orchestrators above and is what keeps the Orchestration Layer thin and swappable-in-shape (e.g., testable as pure sequencing logic) independent of what any given stage actually decides.

**Allowed** (orchestration concerns):
- Stage sequencing
- Execution context management (correlation ID, provenance, timing)
- Error propagation
- Retry coordination
- Correlation tracking

**Not allowed** (business-logic concerns — must not live in an orchestrator):
- Retrieval scoring rules
- Chunking rules
- Citation validation rules
- HR policy decisions

Business behavior belongs inside the appropriate pipeline stage (e.g., retrieval scoring inside the Retriever, citation validation inside the Citation Mapper) or, where a rule spans multiple stages, inside a domain service expressed in terms of the Domain Model Layer below — never inside the Ingestion Orchestrator or Query Orchestrator themselves. An orchestrator that starts making a retrieval-scoring or citation-validation decision has, by definition, taken on a pipeline stage's responsibility and should be treated as a design defect to correct before implementation, not a convenient shortcut.

### Pipeline Stage Layer

Each stage is a self-contained transformation with a defined input/output contract (full detail: `rag_design.md` Sections 4–5). Restated here at the system-architecture level of detail only.

**Ingestion stages:**

```
Document Loader
    │
    ▼
PDF Parser
    │
    ▼
Text Preprocessor
    │
    ▼
Semantic Chunker
    │
    ▼
Metadata Extractor
    │
    ▼
Embedding Generator
    │
    ▼
Vector Indexer
```

| Stage | Responsibility | Input | Output | Dependencies |
|---|---|---|---|---|
| Document Loader | Validate and register a source PDF | Raw file | Validated file + document ID + provenance | None (no provider) |
| PDF Parser | Extract page-ordered text and structure | Validated file | Per-page text + structure + fidelity flags | PDF parsing library (External Infrastructure) |
| Text Preprocessor | Normalize extracted text | Per-page extraction result | Normalized text + raw text reference | None |
| Semantic Chunker | Split text into retrieval-sized chunks | Normalized text | Chunk records | None |
| Metadata Extractor | Attach structural + policy metadata | Chunk records | Enriched chunk records | None |
| Embedding Generator | Produce a vector per chunk | Enriched chunk records | Embedded chunk records | Embedding Provider Interface |
| Vector Indexer | Persist chunks to the index | Embedded chunk records | Ingestion result summary | Vector Store Interface |

**Query stages:**

```
Session Manager
    │
    ▼
Query Analyzer
    │
    ▼
Query Reformulator
    │
    ▼
Retriever
    │
    ▼
Context Builder
    │
    ▼
Prompt Assembler
    │
    ▼
Response Generator
    │
    ▼
Citation Mapper
```

| Stage | Responsibility | Input | Output | Dependencies |
|---|---|---|---|---|
| Session Manager | Resolve session, load bounded history | Session ID + query | Session context | Session store, behind an interface boundary (see "Session Management" below) |
| Query Analyzer | Classify query before retrieval | Session context | Query category + optional direct response | None (mechanism scoped by phase — see "Query Analyzer" below) |
| Query Reformulator | Resolve follow-up ambiguity | Query + history | Reformulated query | None, or LLM Provider Interface (mechanism unspecified) |
| Retriever | Semantic search + filtering + dedup | Reformulated query | Ranked chunk candidates | Embedding Provider Interface, Vector Store Interface |
| Context Builder | Assemble budgeted context | Ranked chunks | Context payload + citation metadata | None |
| Prompt Assembler | Render the grounded prompt | Context payload | Prompt payload | None |
| Response Generator | Generate the answer | Prompt payload | Generated text | LLM Provider Interface |
| Citation Mapper | Resolve citations, flag unverified claims | Generated text + citation metadata | Final answer + citations | None |

This layer does not define code structures — the exact shape of a "chunk record" or "context payload" is `domain_models.md`'s concern; see the Domain Model Layer below for the vocabulary those shapes will be built from.

#### Query Analyzer — Architecture Extension Status, and MVP vs. Future Scope

**Query Analyzer is an architectural extension introduced to support intelligent routing. It is not a mandatory MVP requirement unless approved through requirements update.** It is retained in this architecture because it is a coherent, low-risk design addition (Section 16, Architecture Extensions Requiring Requirements Alignment), not because it is presumed pre-approved SRS scope — no FR currently mandates it. This document keeps it because removing a described component silently would be worse for implementation readiness than tracking it honestly as pending alignment.

**Purpose** (unchanged from `rag_design.md` Section 5.2):
- Avoid unnecessary retrieval calls for queries that don't need HR policy content.
- Route unsupported (out-of-domain) queries away from generation entirely.
- Identify HR policy-related questions and route them into the full retrieval-grounded pipeline.

**MVP approach:** lightweight deterministic routing/classification — a single categorization decision per query (`policy_query` / `conversational` / `unsupported`), implemented as rule-based heuristics or a small deterministic classifier. No multi-step reasoning, no tool selection, no task decomposition.

**Future approach:** LLM-assisted routing — a more capable classification mechanism (e.g., an LLM call tuned for routing) may replace the MVP heuristic behind the same input/output contract, without changing the Retriever, Context Builder, or any downstream stage.

**Query Analyzer is not an autonomous agent in the MVP architecture.** It must not exhibit agent behavior (planning, multi-step tool use, or autonomous decision-making beyond the single category label). That capability class is scoped to Phase 4 (Section 15, Future Evolution) and is a different component, not an evolution of this one's responsibility.

#### Session Management

**The architecture supports externalized session storage for production scalability. MVP may use an in-memory implementation behind the same interface boundary.** No statement in this document should be read as mandating a specific backing store for the MVP — externalization is a capability the interface boundary provides, not a requirement the MVP must satisfy immediately.

This means: the Session Manager stage's contract (Section 3, Pipeline Stage Layer table) does not change between MVP and future production — only the concrete backing store does. Future implementations may use, among other options:
- Redis
- Database-backed storage
- A distributed cache

...without changing query pipeline logic — the Session Manager, Query Orchestrator, and every downstream stage remain unaware of which of these (if any) is in use. An in-memory MVP implementation does **not** support multi-instance horizontal scaling of the Query Orchestrator (Section 13); that property is only realized once an externalized implementation is deployed behind the same interface. This is a deliberate, honest scope boundary, not an architectural gap — see Section 12 (Technology Stack) and ADR-007 (Section 17).

### Domain Model Layer

Sits between the Pipeline Stage Layer and the Provider Interfaces (and is also the shared vocabulary Pipeline Stages use to talk to each other). It represents the business concepts exchanged between components — independent of any specific provider, transport, or storage technology. It has no dependencies of its own: no provider imports, no framework imports, no external SDK references. It is the layer every other layer either produces, consumes, or passes through unchanged.

**Ownership:** Domain models represent business concepts owned by the core HR Policy Assistant system. They are independent of external providers and are used as the common language between pipeline stages and provider interfaces. No external dependency (vector database, embedding API, LLM API) defines or constrains the shape of a domain model — the system defines them on its own terms, and providers are made to fit, not the reverse.

**Representative domain concepts** (illustrative, not exhaustive):

- `Document`
- `DocumentMetadata`
- `TextChunk`
- `Embedding`
- `SearchResult`
- `Citation`
- `Query`
- `Response`
- `ConversationSession`

These names correspond to concepts already used informally throughout `rag_design.md` (e.g., "chunk record," "citation output contract," "context payload") — the Domain Model Layer is where those informal shapes become a single, explicit, shared vocabulary rather than being redefined ad hoc by each stage.

**Provider implementations translate external formats into domain models.** A Provider Implementation's job is not only to call the vendor SDK, but to convert whatever shape that SDK returns into the domain model the rest of the system expects — the translation happens once, at the boundary, not repeatedly wherever the data is used.

```
Vector database response:

External format (vendor-specific)
        │
        ▼
Vector Store Provider Implementation   (translates)
        │
        ▼
SearchResult Domain Model
```

This guarantees two things architecturally:
- **Pipeline stages do not understand vendor-specific response formats.** The Retriever consumes `SearchResult` domain objects, never a raw vector-database SDK response object.
- **Provider implementations isolate SDK-specific structures.** If the vector database is swapped (Section 17, ADR-003), only its Provider Implementation's translation logic changes — the `SearchResult` domain model, and everything downstream of it, is unaffected.

**Detailed class definitions, field-level shapes, and validation rules belong to the forthcoming `domain_models.md`.** This section establishes only that the layer exists, who owns it, which business concepts it names, and where translation into it happens.

### Provider Interfaces & Provider Implementations

Covered in full in Section 4 below. As established in Section 3.0: Provider Interfaces are the contracts Pipeline Stages depend on; Provider Implementations are the concrete adapters that satisfy those contracts and are the only place third-party SDKs are imported.

### External Infrastructure

The actual third-party SDKs and services: the PDF parsing library, the embedding API/SDK, the vector database's client library, and the LLM API/SDK. These are only ever imported by Provider Implementations — see Section 4.

---

## 4. Provider Abstraction Architecture

Per SRS C-003, the only third-party libraries permitted anywhere in this system are for PDF parsing, embedding generation, vector database access, and LLM API access. This section defines the **Provider Interfaces** referenced in Section 3.0's dependency model — the contracts that Pipeline Stages depend on. Concrete **Provider Implementations** (also introduced in Section 3.0) are what actually import third-party SDKs; pipeline stages depend only on the interfaces defined here, never on an implementation directly (PDF parsing is consumed directly by the PDF Parser stage as a library call, not as a swappable "provider" in the same sense, since the SRS does not require PDF-parser interchangeability the way it requires embedding/vector-store/LLM interchangeability — see `rag_design.md` Section 3).

### Embedding Provider

**Responsibilities:**
- Generate document (chunk) embeddings at ingestion time, in batch.
- Generate query embeddings at retrieval time, singly.
- Maintain model/version information as first-class output, so a query embedded with a different model than the index can be detected rather than silently degrading relevance (`rag_design.md` Section 3.1, Risk R-003).

### Vector Store Provider

**Responsibilities:**
- Store embeddings alongside chunk text and metadata.
- Execute similarity search given a query vector and a top-K.
- Apply metadata filters as an optional predicate on the same search call (`rag_design.md` Section 6.2) — not a separate filtered-search code path.
- Return ranked chunks (text + metadata + score) to the Retriever.

### LLM Provider

**Responsibilities:**
- Send a fully assembled prompt for generation.
- Handle response generation in both blocking and streaming modes.
- Support configurable models and generation parameters (temperature, max tokens, timeout) without code changes.
- Normalize provider-specific failures into a shared failure taxonomy (rate-limited / timeout / refused / transient / unknown) so the Orchestration Layer's error handling does not need provider-specific branches (`rag_design.md` Section 3.3).

**Only provider implementations interact with third-party SDKs. Core pipeline stages depend only on provider contracts.** This is the single most load-bearing sentence in this section: it is what makes NFR-EXT-001–003 (swap embedding/vector-store/LLM providers without touching pipeline logic) actually true rather than aspirational, and it is what makes cloud portability (C-007) achievable without a rewrite.

---

## 5. Evaluation Architecture

Evaluation is a first-class architecture capability, not an afterthought bolted onto testing. It is drawn here as its own layer because it has its own responsibilities and its own relationship to the rest of the system — one that is easy to get wrong if left implicit.

```
                     Evaluation Layer
                            │
              ┌─────────────┴─────────────┐
              ▼                             ▼
     Ingestion Pipeline               Query Pipeline
              │                             │
              └─────────────┬───────────────┘
                             ▼
                    Provider Interfaces
```

**Evaluation Layer responsibilities:**
- Maintain evaluation datasets (the labeled fixture corpus and question set — `rag_design.md` Section 9.1, item 2).
- Measure retrieval effectiveness (Precision@K, Recall@K, Hit Rate@K, MRR — `rag_design.md` Section 9.2).
- Measure citation accuracy (whether returned citations match the expected source location — `rag_design.md` Section 9.1, item 4).
- Measure answer quality (faithfulness, answer relevance, completeness, citation correctness — `rag_design.md` Section 9.3).
- Perform regression testing after pipeline changes (gating retrieval/chunking/prompt configuration changes before promotion — `rag_design.md` Section 9.1, item 3).
- Run pipeline comparison experiments (e.g., comparing two chunking or retrieval configurations against the same labeled set before promoting one).

**The evaluation framework reuses production pipeline components and does not create a separate testing-only RAG implementation.** The Evaluation Layer drives the Ingestion Pipeline and Query Pipeline through the same Orchestration Layer entry points any other caller would use (Section 3) — it is architecturally a caller, not a fork. Where it needs isolation (e.g., stage-level unit evaluation with no live external call — `rag_design.md` Section 9.1, item 1), it calls Provider Interfaces directly with stubbed/test-double implementations substituted underneath, exactly as Section 3.0's Dependency Inversion model allows for any caller: the interface is the same; only the implementation behind it changes.

Full metric definitions, evaluation-layer detail, and the evaluation data flow are specified in `rag_design.md` Section 9 — this section exists only to place Evaluation in the system's architecture, not to re-derive its internal design.

---

## 6. Data Architecture

This section describes data **lifecycle and flow** at the conceptual level. Concrete field-level schemas belong to `domain_models.md` (not yet created) — nothing here should be read as a schema definition. The concepts named below correspond to Domain Model Layer entities introduced in Section 3 (e.g., "Processed Chunks" below is the `TextChunk` domain concept in flow form).

### Document Ingestion Flow

```
HR Policy PDF
    │
    ▼
Raw Document Storage        (Document Store — see Section 2, "Document Storage")
    │
    ▼
Extracted Text               (PDF Parser output, pre-normalization)
    │
    ▼
Processed Chunks             (Semantic Chunker output)
    │
    ▼
Metadata + Embeddings        (Metadata Extractor + Embedding Generator output)
    │
    ▼
Vector Database
```

Metadata carried alongside each chunk into the Vector Database (full detail: `rag_design.md` Section 4.5, 6.5):

- Document ID
- Document version
- Page number(s)
- Section / heading path
- Chunk ID
- Extraction confidence (fidelity flag — full-text vs. reduced-fidelity/unparseable)
- Embedding model version

This metadata is what makes citation traceability (Section 1, `rag_design.md` Section 7.1) possible: it is captured once, at ingestion time, and never regenerated at query time.

### Query Processing Flow

```
Employee Question
    │
    ▼
Query Analysis                (Query Analyzer — routes conversational/unsupported/policy_query)
    │
    ▼
Query Embedding                (Embedding Provider, query-time)
    │
    ▼
Vector Retrieval                (Vector Store Provider similarity search)
    │
    ▼
Relevant Context                (Context Builder — budgeted, ordered)
    │
    ▼
LLM Generation                  (Response Generator)
    │
    ▼
Citation-backed Response        (Citation Mapper)
```

This diagram is a system-level condensation of the full query data flow diagram in `rag_design.md` Section 5 (Query Data Flow Diagram), which additionally shows the Query Reformulator step and the three short-circuit paths (conversational, unsupported, empty-retrieval, LLM-declines) — refer there for the complete branching logic.

---

## 7. Component Responsibilities

| Component | Responsibility | Input | Output |
|---|---|---|---|
| Ingestion Orchestrator | Sequence ingestion stages per document; isolate per-document batch failures | Source PDF(s) | Ingestion result summary(ies) |
| Query Orchestrator | Sequence query stages per request; apply routing/error short-circuits | Employee question + session ID | Final response (answer, citations, or decline) |
| Session Manager | Resolve session identity and bounded conversation history | Session ID + query | Session context (history + current query) |
| Query Analyzer | Classify the query before retrieval; route conversational/unsupported queries away from the grounded path | Session context | Query category + optional direct response |
| Query Reformulator | Resolve follow-up ambiguity using conversation history | Query + history | Reformulated query |
| Retriever | Embed query, search, filter, dedupe, optionally re-rank | Reformulated query | Ranked candidate chunk list (possibly empty) |
| Context Builder | Assemble a token-budgeted, ordered context payload | Ranked chunks + conversation history | Context payload + citation metadata |
| Prompt Assembler | Render the versioned, grounded prompt template | Context payload + query | Prompt payload |
| Response Generator | Call the LLM Provider and normalize the result | Prompt payload | Generated text + usage, or normalized failure |
| Citation Mapper | Resolve generated references to source citations; flag unverified claims | Generated text + citation metadata | Answer + structured citations + unverified-statement flag |

(Full responsibility detail, including failure modes and detailed I/O contracts, is in `rag_design.md` Sections 4–5; this table exists at the system-architecture level for quick reference and interview recall.)

---

## 8. Deployment Architecture

Two deployment views are defined, corresponding to the MVP and Future Production phases in `rag_design.md` Section 10.

### MVP Deployment

```
User
  │
  ▼
Python Application               (invoked directly — script/CLI/test harness)
  │
  ▼
Custom RAG Engine                (Orchestration + Pipeline Stage + Domain Model + Provider Interface layers)
  │
  ├──── Vector Database
  ├──── Embedding Provider
  └──── LLM Provider
```

The MVP deployment has **no Application Layer** — the Orchestration Layer's entry points (ingest a document, ask a question) are invoked directly by a script, notebook, or test harness. This is a deliberate scope decision, not an oversight: the initial implementation exists to build and validate correct RAG internals (retrieval quality, grounding, citation correctness) before investing in a service interface around it. It is consistent with the Phase 1–2 scope in `rag_design.md` Section 10. The Session Manager's storage in this deployment is the in-memory implementation described in Section 3 ("Session Management") — sufficient for a single-instance MVP, not for horizontal scaling.

### Future Production Deployment

```
Client
  │
  ▼
FastAPI Service                  (Application Layer — thin)
  │
  ▼
RAG Core Service                 (Orchestration + Pipeline Stage + Domain Model + Provider Interface layers)
  │
  ├───────────────┬─────────────────┐
  ▼               ▼                 ▼
Vector DB    Document Store    LLM Provider
                                (via Embedding Provider for query/chunk vectors)
```

**FastAPI is only a service interface layer. It should not contain RAG business logic.** Request validation, response formatting, and authentication-integration wiring live here; retrieval logic, prompt assembly, and citation mapping do not — those remain entirely inside the RAG Core Service, unchanged from the MVP deployment's internals. This is the deployment-level expression of SRS C-004/C-005 and Section 3's dependency-direction rule above: adding this layer must not require touching the layers beneath it. This deployment also assumes the Session Manager's externalized store implementation (Section 3) has replaced the MVP's in-memory one, behind the same interface.

---

## 9. Runtime Flow

### Query Flow

1. Employee submits a question.
2. Query Analyzer determines the request type (`policy_query` / `conversational` / `unsupported`).
3. (If `policy_query`) The query is reformulated if needed, then embedded.
4. Retriever searches the vector database for relevant chunks.
5. Context Builder prepares the evidence (budgeted, ordered context).
6. Prompt Assembler creates the grounded prompt.
7. LLM generates a response.
8. Citation Mapper validates and resolves references, producing the final cited answer (or the pipeline short-circuits to a declined/not-found response at steps 2, 4, or 7 — see `rag_design.md` Section 5, Query Data Flow Diagram).

### Ingestion Flow

1. HR Policy Owner supplies (or the System Administrator uploads) a document.
2. PDF is parsed.
3. Text is cleaned (preprocessing).
4. Semantic chunks are created.
5. Metadata is extracted.
6. Embeddings are generated.
7. Content is indexed into the vector database.

---

## 10. Cross-Cutting Architecture Concerns

These apply uniformly across both workloads and both layers of pipeline logic (Orchestration + Pipeline Stage). Full detail: `rag_design.md` Section 8.

### Configuration Management

- All operationally variable parameters (chunk size/overlap, top-K, similarity threshold, context token budget, model selection, log level) are externally configured, not hard-coded (SRS FR-1601).
- Environment-based settings distinguish at minimum development, testing, and production profiles (SRS FR-1602).
- Model selection (embedding model, LLM model/provider) is a configuration concern, not a code-level branch — this is what makes provider swap-out (Section 4) actually operable.
- Retrieval parameters (top-K, threshold, re-ranker on/off) are configuration, enabling regression testing of retrieval changes without redeployment (SRS NFR-TEST-003).

### Logging and Observability

- Every request and every ingestion run carries a correlation ID that threads through all stage-level logs (SRS FR-1502).
- Pipeline stage tracking: each stage transition is logged with stage name, duration, and outcome (SRS FR-1501).
- Latency metrics are derived from this same structured logging spine, per-stage and end-to-end (SRS NFR-OBS-002).
- Error tracking: every error carries a stable error code and category (recoverable/non-recoverable) alongside the correlation ID (SRS FR-1401–1402).

### Error Handling

- Retryable failures (transient API errors, timeouts) are retried with backoff at the Provider Interface boundary (implemented within the corresponding Provider Implementation); non-retryable failures fail the current unit of work without crashing the surrounding batch or session (SRS FR-1403, NFR-REL-003).
- Provider failures are normalized into a shared taxonomy before reaching the Orchestration Layer (Section 4), so orchestration error handling is provider-agnostic.
- Partial batch failures are isolated per document during ingestion — one bad PDF does not abort the rest of a batch (SRS FR-1404).
- User-safe error responses never leak internal details (stack traces, credentials, raw provider error text) to the caller (SRS FR-1402).

### Security

- Secret management: API keys and credentials are resolved through the configuration mechanism from a secure source, never hard-coded or logged (SRS FR-1604, NFR-SEC-002).
- Sensitive data protection: full document text is not logged at routine log levels; only identifiers and outcomes are (SRS FR-1505).
- Prompt injection awareness: employee query text is treated as untrusted input; the prompt template constrains the LLM to context-grounded answering, which also limits (without eliminating) the blast radius of an injection attempt embedded in a query (SRS NFR-SEC-003).
- Avoiding sensitive data in logs is a stated design constraint on the Logging concern above, not an afterthought — see FR-1505.

---

## 11. Architecture Principles

### Single Responsibility

Each stage performs one clear responsibility (parse, chunk, embed, retrieve, etc.) — no stage's failure mode or output contract depends on what another stage does internally.

### Dependency Inversion

Business logic (Orchestration, Pipeline Stage, and Domain Model layers) depends on Provider *interfaces*, never on concrete external SDKs directly; Provider Implementations depend on the SDKs and satisfy the interfaces from outside the business-logic chain (Section 3.0). This is the mechanism, not just the intent, behind Section 4's provider-swap claims.

### Configuration-Driven Design

Behavior — retrieval parameters, model selection, chunking strategy, log verbosity — is controlled through configuration (Section 10), not through code branches or redeployment.

### Provider Independence

External providers (embedding, vector store, LLM) can be replaced without changing pipeline logic, because nothing outside a Provider Implementation knows which vendor is behind the interface.

### Testability

Every stage supports isolated testing: deterministic stages (chunking, context budgeting, citation resolution) need no live external call at all; stages that do call a provider are testable against a stubbed Provider Interface (SRS NFR-TEST-001).

---

## 12. Technology Stack

Per this document's constraints, no technology choice below is finalized where an ADR is required — see Section 17 for the corresponding candidate list. This section records what is already decided at the architecture level vs. what remains an open MVP candidate. Note that "Decided" here means decided at the architecture level in this SAD, not that a formal ADR has been written yet — see Section 17 for which of these still need one authored.

### Decided

- **Python** — observed from the existing project scaffold (`app/` module layout); not a new decision introduced by this document.
- **Custom orchestration** — no LangChain or equivalent framework (SRS C-001/C-002); formalized as ADR-001 (Section 17).
- **Provider abstraction approach** — the three-interface boundary (Embedding, Vector Store, LLM) described in Section 4; formalized as ADR-002 (Section 17).

### Initial MVP Candidates (ADR Required)

| Area | Notes |
|---|---|
| Vector database | Must satisfy the Vector Store Interface (Section 4) and cloud portability (SRS C-007). Candidate space includes both self-hosted and managed options; none is selected here. See ADR-003. |
| Embedding model | Must satisfy the Embedding Provider Interface (Section 4); model/version must be tracked (SRS FR-603). See ADR-004. |
| LLM provider | Must satisfy the LLM Provider Interface (Section 4); must support provider swap by configuration regardless of which default is chosen (SRS NFR-EXT-003). See ADR-005. |
| PDF parser | Must support page-ordered text, structural, and table extraction to the fidelity level required by SRS FR-201–206. |
| Session storage | Backing store for the Session Manager's externalized conversation state (Section 3, "Session Management"; `rag_design.md` Section 5.1, Open Question 2). MVP may use an in-memory implementation behind the same interface — see Section 3. |

**API Layer (future):** directionally fixed as FastAPI per project instruction (SRS C-005); not yet built (Section 8, 9).

No row above should be read as committing the project to a specific vendor product; "Initial MVP Candidates" are intentionally left at the category level in this document.

---

## 13. Scalability Considerations

The architecture supports scaling along several independent axes without redesign:

- **Independent ingestion and query workloads** — the Ingestion and Query-Serving workloads share components and provider abstractions but have no runtime coupling; a spike in ingestion volume does not compete for the same request-handling capacity as query traffic (SRS NFR-SCALE-003, `rag_design.md` Section 2).
- **Stateless query serving** — request-handling components hold no in-process state (Section 1, Principle "Statelessness"), which is the precondition for horizontally scaling the Query Orchestrator across multiple instances (SRS NFR-SCALE-001).
- **Externalized session storage** — the architecture supports externalized session storage for scalable deployments (Section 3, "Session Management"); once a shared/external implementation is deployed behind the Session Manager's interface, any instance can serve any session's next turn. This property is **not** available while the MVP's in-memory implementation is in place — that trade-off is accepted deliberately for a single-instance MVP (Section 8).
- **Provider replacement** — the Provider Interface/Implementation split (Section 4) means scaling up to a higher-throughput or higher-capacity vector database or LLM provider is a configuration and adapter-implementation change, not a pipeline rewrite.
- **Batch document processing** — the Ingestion Orchestrator's per-document failure isolation (Section 3) already assumes and supports processing documents as an independent, parallelizable unit of work.

**MVP deployment may run as a single instance while maintaining boundaries required for future scaling.** The MVP is not architected differently from the scaled deployment — it is the same layered architecture (Section 3) running as one process instead of many, because the boundaries that make scaling possible (statelessness, an externalizable session store *interface*, provider abstraction) are architectural properties available from day one, even where the MVP's concrete implementation behind one of those interfaces (session storage) is intentionally the simplest option that satisfies the contract.

---

## 14. Architecture Trade-offs

### Custom Orchestration

**Decision:** Use custom orchestration instead of framework-managed workflows (e.g., LangChain).

**Reason:**
- Understand RAG internals directly rather than through a framework's abstractions.
- Maintain full execution control over retrieval, grounding, and citation logic — these are the system's core trust properties (Section 1) and are easier to guarantee when the control flow is visible and owned, not delegated to a framework's internal chain semantics.
- Improve interview explanation capability — every step of the pipeline can be described precisely, in terms this document and `rag_design.md` already use, without reference to a third-party framework's specific vocabulary or hidden behavior.

### Abstraction vs. Simplicity

**Decision:** Use abstractions only at external dependency boundaries (Embedding, Vector Store, LLM) — not everywhere internally.

**Reason:** Avoid unnecessary complexity while maintaining extensibility. Introducing an interface for every internal stage (e.g., the Semantic Chunker) with no external dependency and no plausible swap-out requirement would add indirection without benefit; the three provider boundaries are abstracted because they are the three points the SRS explicitly requires to be swappable (SRS NFR-EXT-001–003) and the three points where a vendor SDK is genuinely present.

### Prompt-Only vs. Architectural Grounding

**Decision:** Use retrieval validation and citation controls (empty-retrieval short-circuit, unverified-statement flagging, citation-metadata single-source-of-truth) rather than relying on prompt instructions alone.

**Reason:** Reduce unsupported responses structurally. As established in `rag_design.md` Section 6.3, this reduces risk and blast radius — it does not eliminate the possibility of an incorrect or unsupported answer. The trade-off is accepted deliberately: architectural controls plus prompt instructions are strictly stronger than prompt instructions alone, even though neither achieves a formal guarantee.

---

## 15. Future Evolution

The following extensions are consistent with this architecture's extensibility principles (Section 11) but are explicitly out of scope for the phases defined in `rag_design.md` Section 10 (Implementation Scope) and for this document:

- Agentic HR Assistant capability (multi-step reasoning, tool use) — see `rag_design.md` Section 10, Phase 4. Distinct from, and not an evolution of, the MVP Query Analyzer (Section 3).
- Employee profile integration (role/tenure-aware policy applicability).
- Leave eligibility reasoning (structured rule evaluation layered on top of retrieved policy text).
- HR workflow automation (e.g., initiating a leave request) — currently explicitly out of scope (SRS Section 3.2).
- Multi-language support (SRS AS-004 restricts v1.0 to English; FE-003 in the SRS's Future Enhancements).
- Enterprise authentication integration (currently assumed external per AS-002; a first-class integration point is one candidate future addition to the Application Layer, Section 3).

None of these require re-architecting the layers in Section 3 — they are extensions consistent with the existing dependency structure, most naturally landing in the Application Layer (auth), as new Pipeline Stages (relevance grading, per `rag_design.md` Section 6.5), behind a new or swapped Session Management implementation, or as a Phase 4 addition alongside — not inside — the existing Query Orchestrator.

---

## 16. Architecture Extensions Requiring Requirements Alignment

Some components described in this SAD and in `rag_design.md` are architectural additions that do not yet trace back to an approved SRS requirement. They are documented here — not silently included as if pre-approved, and not silently dropped as if never designed — so the gap is visible before `interfaces.md` locks their contracts in.

| Extension | Reason |
|---|---|
| Query Analyzer (Section 3; `rag_design.md` Section 5.2) | Routing capability not explicitly present in the SRS's FR list |
| Relevance grading (`rag_design.md` Section 6.5) | Future retrieval improvement capability, currently scoped as a v2+ enhancement, not tied to any FR |

**These are tracked architectural enhancements and should be formally accepted before becoming mandatory implementation scope.** Concretely: either (a) `requirements.md` is updated with a corresponding FR/NFR and this table entry is closed, or (b) the extension is explicitly deferred and the corresponding component in Section 3 is marked out-of-scope for the next implementation milestone. Until one of those happens, `interfaces.md` should still define the Query Analyzer's contract (since Section 3 already commits to its input/output shape for architectural coherence), but implementers and reviewers should treat it as *provisionally* in scope, not SRS-mandated scope.

---

## 17. Architecture Decisions Requiring ADRs

The following decisions are significant enough — either because they are already architecturally committed and warrant a formal rationale record, or because they remain genuinely open — that each should be captured as its own Architecture Decision Record before or during implementation, rather than left implicit in this SAD. Per this document's constraints, **no ADR content (options considered, consequences) is written here — only candidates are identified**, grouped by category.

### Architectural Decisions

Decisions about the system's own structure, already committed at the architecture level in this SAD; the ADR formalizes rationale and alternatives considered for governance record-keeping.

- **ADR-001** — Custom orchestration approach (Section 1, 14; alternative considered: LangChain or an equivalent framework).
- **ADR-002** — Provider abstraction boundary (Section 3.0, 4; why exactly three interfaces, not more or fewer).
- **ADR-009** — Domain model ownership (Section 3, "Domain Model Layer"; how domain models are structured, versioned, and kept independent of any single provider's response shape).

### Technology Decisions

Vendor/product-level decisions, all currently open (Section 12) — none is finalized in this document.

- **ADR-003** — Vector database selection.
- **ADR-004** — Embedding model selection.
- **ADR-005** — LLM provider selection.
- **ADR-006** — PDF parser selection.
- **ADR-007** — Session storage technology (Redis, database-backed, distributed cache, or another option — Section 3, "Session Management").

### Future Capability Decisions

Decisions gated on the Section 16 requirements-alignment process, not purely technical choices.

- **ADR-008** — Query Analyzer approach (rule-based vs. lightweight classifier vs. LLM call for MVP; contingent on Query Analyzer's requirements status per Section 16).

This document does not resolve any of these — resolving them is the explicit purpose of the ADR process itself, not this SAD.

---

## 18. Related and Forthcoming Documents

- [requirements.md](./requirements.md) — Software Requirements Specification (SRS); the source of truth for *what* the system must do and to what measurable standard.
- [rag_design.md](./rag_design.md) — RAG Architecture Design; the source of truth for pipeline-internal component design, retrieval strategy, citation mechanics, and evaluation approach.
- `interfaces.md` (not yet created) — will define the concrete contracts (method-level, but not implementation) for the Provider Interfaces (Section 4) and inter-stage data contracts (Section 3).
- `domain_models.md` (not yet created) — will define the data/entity shapes introduced conceptually in the Domain Model Layer (Section 3) and referenced in the Data Architecture flows (Section 6): chunk record, citation record, session context, configuration schema.

This document, `requirements.md`, and `rag_design.md` should be read together; where any two disagree, `requirements.md` governs over `rag_design.md`, and both govern over this document (the Document Control section above restates this: this SAD is a system-level view built on top of them, not a superseding authority).

---

*End of Document.*

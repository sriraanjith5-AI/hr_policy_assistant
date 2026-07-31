# Domain Models Specification

## Enterprise HR Policy Assistant — Shared Business Objects

| Field | Value |
|---|---|
| Document Type | Domain Models Specification |
| Project Name | Enterprise HR Policy Assistant |
| Version | 1.3 |
| Status | Revised — Stabilized, Ready for sequence_diagrams.md |
| Upstream Documents | [requirements.md](./requirements.md) (SRS v1.0), [rag_design.md](./rag_design.md) (v1.1), [architecture.md](./architecture.md) (SAD v1.2), [interfaces.md](./interfaces.md) (v1.1) |
| Downstream Documents (not yet created) | `sequence_diagrams.md`, `testing.md`, `deployment.md`, `tasks.md` |
| Prepared By | Principal AI Solution Architect |
| Date | 2026-07-29 |

---

## Document Control

`domain_models.md` is the fifth document in the Specification-Driven Development (SDD) chain:

```
requirements.md → rag_design.md → architecture.md → interfaces.md → domain_models.md →
sequence_diagrams.md → testing.md → deployment.md → tasks.md → implementation
```

This document gives field-independent, business-meaning definitions to every object `interfaces.md` Section 6 named ("This section names them; it does not define their attributes") plus the finer-grained concepts needed to describe them precisely. It defines **what each object means and how it relates to the others** — responsibility, lifecycle, and relationships — never storage columns, API payloads, or language-specific types.

**A modeling note before the definitions below:** the source material for this document (`rag_design.md`, `architecture.md`) names more candidate concepts than turn out to be independent business objects. Rather than transcribing every candidate name into its own top-level model, each one was tested against a simple question — *does this represent a distinct business concept with its own identity and lifecycle, or is it the same concept observed at a different processing moment?* Two merges resulted from that test (documented at Sections 6 and 8 below); everywhere else, a candidate that looked similar to another on the surface turned out to have a genuinely different lifecycle or cardinality, and was kept distinct (documented at Sections 7 and 9). This is a deliberate design choice, not an oversight — see the note at each merge point for the reasoning.

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-07-29 | Initial Domain Models Specification |
| 1.1 | 2026-07-29 | Final review pass before `sequence_diagrams.md`: added explicit ownership-layering validation against `architecture.md` v1.2; added a Model Boundary Validation table testing every model's business meaning, creator, consumer, and lifecycle justification; re-confirmed the Query/ReformulatedQuery and QueryContext/PromptContext merge decisions with the reviewer's exact confirmation language; added lifecycle-stage diagrams for `Document`, `Query`, and `ConversationSession` (processing-stage lifecycles, distinct from their identity/version lifecycles already documented); strengthened relationship diagrams with simplified canonical chains and explicit cardinality statements (and corrected one ordering inaccuracy in the process — see Section 12); added an explicit Citation resolution flow diagram; reconfirmed the `SearchResult`/`RetrievedChunk` distinction and its compatibility with a future re-ranking or relevance-grading stage; added a Domain Model Evolution section; added an Avoided Design Patterns section; added a full validation matrix cross-checking every `interfaces.md` contract against an existing domain model |
| 1.2 | 2026-07-29 | Added a Runtime Invariants section (new Section 18) formalizing six system-wide rules that must always hold across the models defined here; one invariant as originally proposed ("a Response cannot be generated without QueryContext") was refined during validation — it holds for grounded/cited responses but not for the declined "Not Found" path, which by design short-circuits before a `QueryContext` is ever built, per `rag_design.md` Section 5.9–5.10 — the refined wording states both cases explicitly rather than asserting the broader claim as originally worded; flagged a related open question about partial streamed output on provider failure (Open Decision 5); renumbered Open Decisions to Section 19 and Related Documents to Section 20 |
| 1.3 | 2026-07-29 | Stabilization pass before `sequence_diagrams.md`. **Corrected a real attribution error found during review:** `Response`'s declined state was previously documented as always created "by the Citation Mapper stage," but `rag_design.md` Section 5.10 ("Not Found Path") is a distinct component from Citation Mapper, and two of its three trigger conditions occur *before* a `QueryContext` or `GeneratedResponse` even exists — the third (LLM decline) occurs *after* both exist but still bypasses Citation Mapper. Section 9 now documents all three declined-response trigger paths precisely, with corrected creator attribution, and Section 14's ownership matrix and Runtime Invariant 1 (Section 19) were updated to match. Also: added an explicit Response-state clarification (grounded vs. declined are one shape, two states, not two categories); added a Streaming Response Note to Section 8 (`GeneratedResponse` represents a completed response only — streaming is a delivery detail, not a new domain state — resolving part of the ambiguity behind Open Decision 5, while the caller-facing streaming-failure question remains genuinely open); added a new Domain Model Guarantees section (Section 18); strengthened the `ExecutionMetadata`/`ErrorContext` ownership boundary statement in Section 11; added two more specific Domain Model Evolution guidelines (vector database migration, LLM provider response-semantics stability); added a Naming Aliases subsection and an Evaluation Traceability subsection to Section 17, plus a final consolidated traceability table; fixed a stale cross-reference in Section 6 left over from the previous renumbering pass; renumbered Sections 18–20 to 19–21 to accommodate the new Domain Model Guarantees section |

---

## 1. Purpose

Domain models represent concepts **owned by the HR Policy Assistant core system**, not by any external provider, database, or API contract. They provide the common language between:

- **Orchestrators** — which sequence stages by passing domain models between them, never provider-native or vendor-specific shapes (`interfaces.md` Section 3).
- **Pipeline stages** — every stage interface in `interfaces.md` Section 4 declares its input and output entirely in terms of the models defined here.
- **Provider interfaces** — the point where an external format (a vector database's raw response, an embedding API's raw output, an LLM's raw completion) is translated *into* a domain model, and never leaks past that boundary (`architecture.md` Section 3, "Provider implementations translate external formats into domain models").

Because every contract in `interfaces.md` already refers to these models by name, this document is the single place their business meaning is defined — no other document should introduce a competing definition.

---

## 2. Domain Modeling Principles

### Provider Independence

Models must not contain:
- SDK objects (no embedding-vendor response type, no vector-database result type, no LLM completion object)
- Vendor-specific fields (no field that only makes sense for one provider's API shape, e.g., a field that exists only because one specific vector database numbers its results that way)

Every model below is defined purely in terms that would still make sense if every provider behind the system were replaced tomorrow (`architecture.md` Section 4, 11; `interfaces.md` Section 2.1).

### Business Ownership

The core system owns domain meaning. A `Citation`, a `TextChunk`, a `ConversationSession` mean what this document says they mean — not what a vector database's SDK or an LLM API's response schema happens to call the equivalent concept. **External systems translate into and from domain models**; domain models never adapt themselves to an external system's shape (`architecture.md` Section 3, "Domain Model Layer — Ownership").

**Ownership is layer-scoped, and every model in this document was validated against `architecture.md`'s dependency direction:**

```
Application Layer
        ↓
Orchestration Layer
        ↓
Pipeline Stage Layer
        ↓
Domain Models
        ↓
Provider Interfaces
```

**Pipeline stages (and stage-equivalent responsibilities, such as the Not Found Path — see Section 9) own domain concepts.** Every model in Sections 3–11 is created and owned by exactly one such component. No domain model is owned by an Orchestrator *as* an orchestrator — orchestrators sequence and route, they do not decide business meaning (`interfaces.md` Section 3's "Orchestrator Responsibility Boundary") — and no domain model is owned by a Provider Interface.

**Provider implementations must translate external objects into domain models.** A Provider Implementation never returns its vendor SDK's native response type to the Pipeline Stage that called it — it returns the domain model the corresponding Provider Interface promises (`Embedding`, `SearchResult[]`, `GeneratedResponse`). This is validated per-model in Section 14 (Model Ownership Matrix) and audited in Section 13 (Model Boundary Validation).

### Traceability

Models must preserve:
- **Document lineage** — every `TextChunk` (and everything derived from it) can be traced back to the `Document` and `ExtractedDocument` it came from, without re-deriving that link at query time (`rag_design.md` Section 7.1).
- **Retrieval evidence** — every `RetrievedChunk` used in generation is traceable back to the `SearchResult` that surfaced it.
- **Citation information** — every `Citation` on a final `Response` is traceable back to a specific `TextChunk`, never inferred after the fact.

Traceability is not an add-on feature of these models — it is the reason several of them (`ExtractedDocument`, `ChunkMetadata`, `CitationReference`) exist as distinct objects rather than being collapsed into simpler ones.

### Testability

Models should support deterministic testing: every model here is a plain value/entity description with no hidden dependency on a live provider, a clock, or a database connection. A test can construct a `SearchResult` or a `TextChunk` by hand, entirely offline, and every stage interface in `interfaces.md` that consumes one will behave identically to how it behaves against a real pipeline (`interfaces.md` Section 9).

---

## 3. Core Document Models

### Document

**Represents:** An ingested HR policy document — the unit the HR Policy Owner supplies and the System Administrator manages the lifecycle of.

**Responsibility:** Carries identity and provenance for a single source policy document. It is the aggregate root of everything derived from one PDF — every `ExtractedDocument`, `TextChunk`, and `Embedding` that exists, exists because a `Document` was ingested.

**Identity/version lifecycle:** Created on first successful ingestion (`interfaces.md` 4.1). Updated (new version, same identity) on re-ingestion of a changed source file (SRS FR-105). Retired on explicit deletion (SRS FR-106), at which point every dependent `TextChunk` and `Embedding` is also retired. A `Document`'s identity is stable across re-ingestion — re-ingesting the same source produces a new version of the same `Document`, never a new one (SRS FR-104, NFR-REL-004).

**Processing-stage lifecycle** (within a single ingestion run, distinct from the identity/version lifecycle above — included because it clarifies what "in progress" means for a `Document` mid-ingestion):

```
Uploaded → Extracted → Processed → Indexed → Available
```

- *Uploaded* — accepted and validated by the Document Loader (`interfaces.md` 4.1).
- *Extracted* — an `ExtractedDocument` now exists for this version.
- *Processed* — `TextChunk[]` and their `ChunkMetadata` exist.
- *Indexed* — every chunk's `Embedding` is stored in the vector index.
- *Available* — this version is what the Retriever will surface for matching queries.

**Relationships:**
- `Document` **has-one** `DocumentMetadata` (current version's descriptive/classification data).
- `Document` **contains** `ExtractedDocument` (the parsed content this version produced).
- `Document` **produces** `TextChunk[]` (transitively, via `ExtractedDocument`) — **one document contains many chunks.**

### DocumentMetadata

**Represents:** Document-level identity, versioning, source, and classification information — the descriptive facts about a `Document` as a whole, distinct from the content extracted from it.

**Responsibility:** Answers "which document is this, what version, where did it come from, and how sensitive is it" — without describing the document's content.

**Includes (conceptually, not as a field list):**
- Document identity (the `Document`'s stable identifier)
- Version (the ingestion/re-ingestion version number, SRS FR-109)
- Source information (original filename, ingesting actor, ingestion timestamp, SRS FR-109)
- Classification information (the access-classification tag, SRS FR-504)

**Lifecycle:** Created alongside its `Document` on first ingestion; replaced (not merged) on re-ingestion, since a new version means new provenance facts — the prior version's `DocumentMetadata` is superseded, not edited in place. It has no lifecycle independent of its `Document`'s version lifecycle.

**Relationships:**
- **Belongs to** exactly one `Document` (current version).
- **Referenced by** every `ChunkMetadata` derived from this document's chunks (Section 4) — chunk-level metadata does not repeat document-level facts, it points back to them. (Not a duplicate of `ChunkMetadata` — see Section 17, "Naming Aliases and Near-Duplicates," for the explicit distinction.)

### ExtractedDocument

**Represents:** The PDF's content after parsing and preprocessing — both the raw extracted text and the normalized/cleaned text, together, as one audit-purposed record.

**Modeling decision — merge:** `rag_design.md` describes the PDF Parser's raw output and the Text Preprocessor's normalized output (Sections 4.2, 4.3) as two pipeline stage outputs, and SRS FR-305 requires both to remain retrievable for audit. They were tested against the "distinct business concept" question and found to share an identical lifecycle and ownership: both are created together during one ingestion run, both are retained together for the same reason (audit — FR-305), and neither is ever independently modified afterward. They are modeled here as one object, `ExtractedDocument`, carrying both the raw and normalized text as two facets of the same audit record, rather than as two separate top-level models.

**Responsibility:** Preserves what was actually extracted from the source PDF — including page-level extraction-fidelity information (full-text vs. reduced-fidelity vs. unparseable, SRS FR-205) — independent of how it was later chunked. This is the object the "Document Store" concept in `rag_design.md` Section 4.9 persists. **This is not merely a processing-step artifact left over from parsing** — it has its own retention justification (audit, FR-305) independent of whether any `TextChunk` derived from it still exists, which is why it survives the "remove models that exist only because of processing steps" test.

**Lifecycle:** Created once per ingestion (or re-ingestion) run, immediately after parsing and preprocessing complete. Never mutated afterward. Superseded (not edited) on re-ingestion, following the same version discipline as `Document`.

**Relationships:**
- `Document` **contains** `ExtractedDocument` (one per document version).
- `ExtractedDocument` **is the source of** `TextChunk[]` (chunking reads from it, but chunking does not mutate it).

---

## 4. Chunking Models

### TextChunk

**Represents:** The smallest retrievable knowledge unit — a semantically bounded segment of a document's extracted text, and a permanent piece of the system's stored knowledge.

**Responsibility:** Is the unit everything downstream operates on. Used by:
- **Embedding generation** — one `Embedding` is produced per `TextChunk` (Section 5).
- **Vector storage** — `TextChunk` (with its `ChunkMetadata` and `Embedding`) is what gets indexed.
- **Retrieval** — a `TextChunk` is what a `SearchResult` ultimately references.

**Lifecycle:** Created during chunking, from an `ExtractedDocument` (`rag_design.md` Section 4.4). Immutable once created — a content change means a new version of the parent `Document`, which produces new `TextChunk` instances, not edits to existing ones (this is what makes re-ingestion's "replace, don't merge" behavior — SRS FR-702 — well-defined).

**Relationships:**
- **Derived from** exactly one `ExtractedDocument` (and transitively, one `Document`).
- **Has-one** `ChunkMetadata`.
- **Has-one** `Embedding` (once embedding generation completes) — **one chunk has exactly one current embedding.**
- **Referenced by** `SearchResult` (Section 7) at retrieval time.

### ChunkMetadata

**Represents:** Chunk-scoped descriptive information — where in the document this chunk came from, and how it was produced.

**Includes (conceptually, not as a field list):**
- Document ID (reference back to the owning `Document`)
- Page number(s)
- Section / heading path
- Chunk ID
- Extraction confidence (the fidelity indicator inherited from the source `ExtractedDocument` page, SRS FR-205)
- Embedding model version (recorded once embedding completes, SRS FR-603)

This document does not define storage columns for any of the above — only that these are the concepts a `ChunkMetadata` must be able to answer questions about.

**Lifecycle:** Created alongside its `TextChunk`, at chunking time, for the structural fields; enriched once (not repeatedly) when the Metadata Extractor stage (`interfaces.md` 4.5) attaches policy-domain fields and once more when the Embedding Generator stage (`interfaces.md` 4.6) records the embedding model version. Immutable after that — same rationale as `TextChunk`. It has no lifecycle independent of its `TextChunk`.

**Relationships:**
- **Belongs to** exactly one `TextChunk`.
- **References** (does not duplicate) its owning `Document`'s `DocumentMetadata` for document-level facts (title, classification, etc.) — a design choice that keeps document-level updates from requiring a rewrite of every chunk's metadata. (Not a duplicate model — see Section 17, "Naming Aliases and Near-Duplicates.")

---

## 5. Embedding Models

### Embedding

**Represents:** A vector representation of a piece of text (a chunk at ingestion time, or a query at retrieval time), together with the information needed to know whether it is comparable to another vector.

**Vector meaning:** The vector itself carries no business meaning on its own — its business meaning is entirely relational: two `Embedding`s produced by the same model/version are comparable via similarity; two produced by different models/versions are not, and must not be silently compared (`rag_design.md` Section 3.1, Risk R-003).

**Model information:** Every `Embedding` carries the identity and version of the model that produced it, as a first-class fact — not an incidental detail, because it is what makes the comparability rule above enforceable. **No specific provider is named or implied by this model** — "model information" here means an opaque model identifier/version string, not a vendor SDK's model-selection type.

**Relationship to `TextChunk`:** One `Embedding` belongs to exactly one `TextChunk` (or, at query time, one `Query`) — it is never shared across chunks, and a chunk never has more than one *current* `Embedding` (re-embedding with a new model replaces, rather than adds to, the chunk's `Embedding` — SRS FR-606).

**Lifecycle:** Created by the Embedding Generator stage (ingestion) or the Retriever stage (query time, transient — a query's `Embedding` is not persisted). Replaced, not edited, if the embedding model changes. Has no lifecycle independent of the `TextChunk`/`Query` it represents.

---

## 6. Query Processing Models

### Query

**Represents:** An employee's information request, throughout its lifecycle — from submission, through any reformulation, to being consumed by retrieval.

**Modeling decision — merge, reconfirmed:** The source material describes a separate "Query Reformulator output" concept (`interfaces.md` 4.10: reformulated query text + original query text, both retained). Re-tested against the "distinct business concept" question during this review: a reformulated query is not a new question with its own identity — it is the *same* question, carrying an additional, optional resolved form. It shares `Query`'s lifecycle exactly (created and discarded within one turn, never independently persisted). **The reformulation process may update the query representation, but does not create a separate domain entity.** It remains modeled here as an attribute-level distinction within `Query` (an original form and an optional resolved form), not as a separate top-level model (previously named `ReformulatedQuery`). The *mechanism* that produces the resolved form remains an open decision (Section 20) — this merge only resolves the model's shape, not how reformulation is implemented.

**Responsibility:** Carries the question text, in both the form the employee typed and (when applicable) the self-contained form used for retrieval, plus a link to the `ConversationSession` it was asked within.

**Identity lifecycle:** Created per request. Never persisted independently — it lives inside a `ConversationMessage` once the turn completes (Section 10).

**Processing-stage lifecycle** (within a single request, distinct from identity lifecycle above; shown here as the grounded/happy path — see Section 9 for the three ways this path can short-circuit into a declined `Response` instead):

```
Received → Retrieved → Context Built → Answered → Cited
```

- *Received* — submitted, session resolved (`interfaces.md` 4.8).
- *Retrieved* — a `SearchResult[]` now exists for this `Query` (possibly empty, per Section 7).
- *Context Built* — a `QueryContext` now exists.
- *Answered* — a `GeneratedResponse` now exists.
- *Cited* — a final `Response`, with `Citation[]` resolved (or the unverified-statement flag set), now exists and completes this `Query`'s `ConversationMessage`.

**Relationships:**
- **Asked within** exactly one `ConversationSession`.
- **Produces** an `Embedding` at retrieval time (transient, not persisted independently — Section 5).
- **Provisional, pending Query Analyzer approval (`interfaces.md` 4.9):** if/when the Query Analyzer extension is formally accepted (`architecture.md` Section 16), a `Query` will additionally carry a query-category classification. This is not modeled as a committed field here because the component producing it is itself provisional (Section 20).

### QueryContext

**Represents:** The full set of information required to answer a question — the query, the retrieved evidence, and the relevant session context, assembled together.

**Responsibility:** Is the single assembled bundle that generation is grounded on. This is the object the Context Builder stage (`interfaces.md` 4.12) produces and the Prompt Assembler stage (`interfaces.md` 4.13) consumes.

**Lifecycle:** Created per request, after retrieval completes, and **only** when retrieval produced at least one usable chunk — see Section 18, "QueryContext" guarantee. Discarded once the request completes — never persisted independently (though the `RetrievedChunk`s and `Query` it references may be logged for evaluation purposes, per `rag_design.md` Section 9).

**Relationships:**
- **Contains** one `Query`.
- **Contains** `RetrievedChunk[]` (Section 7) — not `SearchResult[]` directly; see Section 7 for why that distinction matters.
- **References** the relevant portion of the current `ConversationSession`'s history.
- **Carries** a truncation indicator (whether the evidence had to be cut to fit a token budget, `rag_design.md` Section 4, FR-904).

---

## 7. Retrieval Models

### SearchResult

**Definition (reconfirmed):** Raw candidates returned from vector search.

**Represents:** A single candidate returned by similarity search — the retrieval system's raw output, before any selection or filtering for use in generation.

**Responsibility:** Carries what the Retriever stage (`interfaces.md` 4.11) gets back from the Vector Store Provider Interface, translated into domain terms: a matched chunk reference, similarity information, and a metadata reference.

**Includes (conceptually):**
- Matched chunk reference (which `TextChunk` this candidate corresponds to)
- Similarity information (the relevance score, and which retrieval stage produced it — pre- or post-re-ranking)
- Metadata reference (the candidate's `ChunkMetadata`, carried along so downstream stages don't need a second lookup)

**Lifecycle:** Created per retrieval call. Discarded (not persisted) once the request completes, except where retained for evaluation logging (`rag_design.md` Section 9; Section 17, "Evaluation Traceability").

### RetrievedChunk

**Definition (reconfirmed):** Evidence selected after filtering, ranking, and deduplication.

**Represents:** Evidence that has been selected for use in generation — the subset (and ordering) of candidates that actually made it into the `QueryContext`.

**Why this exists as a distinct model, not a removal candidate:** The simplest possible version of this system might try to skip straight from `TextChunk` to "evidence used in the answer." That framing hides a real distinction this system needs: `TextChunk` is the **stored knowledge unit** — permanent, exists whether or not any query ever retrieves it. `RetrievedChunk` is the **selected evidence for answering** — transient, exists only because a specific query's retrieval, filtering, deduplication, and (optionally) re-ranking process chose it. The meaning genuinely changes between the two, which is exactly the case Section 2's modeling test says to keep distinct, not collapse. This is also why `RetrievedChunk` "must represent evidence selected for generation, not merely raw vector search output" — see Section 18, "RetrievedChunk" guarantee.

**Difference between `SearchResult` and `RetrievedChunk`:** A `SearchResult` is a *candidate* — the Retriever may produce more of them than are ultimately used (an over-fetched candidate set, per `rag_design.md` Section 6.1), and some are discarded by threshold filtering, deduplication, or the token budget in the Context Builder. A `RetrievedChunk` is *evidence* — a `SearchResult` that survived selection, was assigned a position in the final ordered context, and is now eligible to be cited. Every `RetrievedChunk` began as a `SearchResult`; not every `SearchResult` becomes a `RetrievedChunk`. This distinction exists specifically because "was it a retrieval candidate" and "was it actually used as evidence" are different facts the system must be able to answer independently — the second is what a `Citation` (Section 9) ultimately points back to, and conflating the two would make it impossible to tell whether an unused-but-retrieved chunk should ever have been surfaced.

**Future re-ranking remains supported without a new model:** if a re-ranking step (`rag_design.md` Section 6.1 step 5) or a future relevance-grading stage (`rag_design.md` Section 6.5) is added, it operates on `SearchResult[]` *before* `RetrievedChunk[]` selection — it changes which `SearchResult`s are selected and in what order, not the shape of either model. No new domain model is required to support either enhancement.

**Lifecycle:** Created by the Context Builder stage (`interfaces.md` 4.12) from a subset of the `SearchResult[]` it receives. Lives only inside a `QueryContext`.

**Relationships:**
- **Derived from** exactly one `SearchResult`.
- **Contained by** exactly one `QueryContext` — **one query may retrieve multiple chunks.**
- **Referenced by** `CitationReference` (Section 9), if the generated answer cites it.

---

## 8. Generation Models

**Modeling decision — merge, reconfirmed:** The source material's Generation Models grouping originally requested a separate `PromptContext` object ("grounded information supplied to LLM"). Re-tested during this review: this is the same assembled evidence bundle as `QueryContext` (Section 6) — same identity, same lifecycle, same contents — observed at the moment it is handed to the Prompt Assembler rather than at the moment it was built. It is not modeled as a second object; `QueryContext` is the single canonical name used throughout this document, confirmed as **assembled information required to generate a response.**

**The rendered LLM prompt text remains an implementation artifact. It must NOT become a domain model.** It is a template rendering of `QueryContext` plus configuration, with no independent business meaning beyond "the text sent to the LLM this one time." Keeping it out of the domain model is what "keep processing artifacts separate from domain concepts" means in practice — see also Section 16 (Avoided Design Patterns).

### GeneratedResponse

**Represents:** The model-generated answer, before citation resolution.

**Responsibility:** Carries what the LLM actually produced — text, plus the signals needed to decide what happens next: token usage and a finish reason (`interfaces.md` 4.14). It is explicitly *not* the object returned to the employee — that is `Response`, below, which only exists after citation resolution.

**Includes (conceptually):**
- The generated text
- A finish-reason signal, including the two grounding-relevant outcomes: the model declining because context was insufficient, and the model succeeding with an answer to be resolved into citations (`rag_design.md` Section 6.3; `interfaces.md` Section 7, "Not Error Conditions")
- Token usage, for cost tracking (SRS NFR-COST-001)

**Streaming Response Note:**

- **Current MVP reference path:** blocking (non-streaming) generation. `interfaces.md` 4.14 supports a streaming mode as a configuration option, but no default has been fixed (`architecture.md` Section 17, ADR-candidate territory) — the MVP reference path assumed throughout this document is the simpler blocking call, consistent with the MVP's "no Application Layer, direct invocation" framing (`architecture.md` Section 8).
- **What `GeneratedResponse` represents:** a **completed response only**. It is never a partial or in-progress state. In streaming mode, individual text deltas are a *delivery detail* at the LLM Provider Interface boundary (`interfaces.md` 5.3, "a stream of text deltas") — they are not domain objects in their own right, the same way the rendered prompt text is not a domain object. A `GeneratedResponse` comes into existence only once the underlying call — streamed or not — reaches a finish reason.
- **Why this supports future streaming without redesign:** because `GeneratedResponse`'s meaning ("the model's completed output for this request") does not change depending on how it was delivered. Adding or changing streaming behavior is a Provider Implementation and Response Generator concern (`interfaces.md` 4.14, 5.3); it never requires a new or different domain model.
- **Open decision, restated precisely (Section 20, item 5):** this resolves *whether `GeneratedResponse` itself can be partial* (it cannot, by definition) but not what a caller should do with tokens already delivered to it before a mid-stream failure. **Streaming failure semantics require sequence diagram and deployment contract definition.**

**Lifecycle:** Created by the Response Generator stage (`interfaces.md` 4.14) only on a completed provider call (see Runtime Invariant 4, Section 19). Consumed once, by the Citation Mapper stage (`interfaces.md` 4.15), and then discarded — it does not outlive the request except where retained for evaluation logging.

**Relationships:**
- **Produced from** one `QueryContext` (via the rendered-prompt processing artifact, not modeled).
- **Consumed by** exactly one Citation Mapper invocation *when generation succeeds with citable content* — see Section 9 for the case where a `GeneratedResponse` exists but Citation Mapper is bypassed.

---

## 9. Citation Models

This section received a focused review to confirm the model set supports three things end to end: grounded answers, citation traceability, and unverified-statement detection.

### Response State Clarification — One Shape, Two States

`Response` (below) is **one domain concept with two states, not two separate response categories.** Every `Response` instance has the identical shape (answer text, `Citation[]`, unverified-statement flag, truncation indicator) regardless of state — what differs is which fields carry content and what upstream lineage produced them.

| | Grounded state | Declined state |
|---|---|---|
| **Created by** | Citation Mapper (`interfaces.md` 4.15) | The Not Found Path (`rag_design.md` Section 5.10) |
| **`QueryContext` exists?** | Always | Sometimes — see the three trigger cases below |
| **`GeneratedResponse` exists?** | Always | Sometimes — see the three trigger cases below |
| **`Citation[]`** | Zero or more, resolved | Always empty, by construction |
| **`unverified_statement_flag`** | Meaningfully true or false — reflects whether every `CitationReference` in the `GeneratedResponse` resolved | Always `false` — there is no `GeneratedResponse` to have parsed `CitationReference`s from in two of the three trigger cases, and in the third, Citation Mapper never runs to evaluate them |

**The declined state has three distinct trigger paths, with different upstream lineage** (`rag_design.md` Section 5.9–5.10, Query Data Flow Diagram):

1. **Query Analyzer classifies `unsupported`** — no `QueryContext` exists yet, no `GeneratedResponse` exists yet. The Not Found Path is reached almost immediately.
2. **Retriever/Context Builder finds no usable evidence** — `SearchResult[]` came back empty (or nothing survived threshold filtering); the Context Builder does not construct a `QueryContext` for zero evidence (Section 6, `QueryContext`; Section 18 guarantee) — no `GeneratedResponse` exists.
3. **LLM declines due to insufficient context** — a `QueryContext` *and* a `GeneratedResponse` **do** exist (the request reached generation), but the Not Found Path is invoked in place of Citation Mapper, so no `CitationReference` resolution ever occurs and `Citation[]` is empty by construction, not by absence of upstream evidence.

**Why "the Not Found Path" and not "the Query Orchestrator" is the declined state's creator:** `rag_design.md` Section 5.10 names this as its own component, distinct from Citation Mapper (5.8) — the Query Orchestrator *invokes* it as part of sequencing (a permitted orchestration action), but the component that actually assembles the declined `Response` shape is the Not Found Path, not the orchestrator deciding business meaning on its own. This keeps Runtime Invariant 5 (Section 19) — "orchestrators cannot modify domain model meaning" — intact without requiring an exception: the Not Found Path's declined-`Response` assembly is a fixed, content-free template (there is no evidence-dependent decision being made), and it is attributed to its own named responsibility, not to the orchestrator.

*(This is a correction from the previous revision of this document, which stated that `Response` — in both states — was "created by the Citation Mapper stage." That was accurate only for the grounded state; see the v1.3 changelog entry above.)*

### Citation Resolution Flow

```
Generated Claim
      │
      ▼
CitationReference
      │
      ▼
Citation Resolution
      │
      ▼
Source Evidence
```

A claim inside a `GeneratedResponse` is associated with a `CitationReference` (an in-text pointer). The Citation Mapper resolves that reference against the evidence carried in `QueryContext`. A successful resolution produces a `Citation` pointing at source evidence (a `TextChunk`, and transitively its `Document`). **A missing citation reference does not automatically become a technical error. It becomes `unverified_statement_flag`, as defined in `rag_design.md` Section 7.3** — a quality signal on a successful, *grounded* `Response`, not a failure record (`interfaces.md` Section 7, "Not Error Conditions"; Section 11 below).

### Citation

**Represents:** A single piece of evidence supporting a claim in an answer — the resolved, structured pointer back to a source. **Must represent a resolved source reference only** — a `Citation` never exists in an unresolved or pending state (see Section 18, "Citation" guarantee); an unresolved reference is a `CitationReference` (below), never a partially-formed `Citation`.

**Includes (conceptually):**
- Document reference (which `Document`)
- Section
- Page
- Chunk reference (which `TextChunk`, and transitively which `RetrievedChunk`)

**Lifecycle:** Created by the Citation Mapper stage (`interfaces.md` 4.15), by resolving a `CitationReference` against `QueryContext`'s carried evidence. Immutable once created; attached to exactly one `Response` (always in the grounded state — see above).

**Relationships:**
- **Resolved from** a `CitationReference`.
- **Points to** a `TextChunk` (and, transitively, the `Document`/`DocumentMetadata` that produced it) — never re-derived at read time (Section 2, "Traceability").
- **Attached to** a `Response` — **one response may contain multiple citations.**

### CitationReference

**Represents:** The mapping between a generated claim and the source evidence that supports it — the *link*, distinct from the resolved `Citation` object it produces.

**Why this is distinct from `Citation`:** A `Citation` is the resolved, structured output — it answers "what source supports something in this answer." A `CitationReference` is the *unresolved* pointer that exists inside the `GeneratedResponse`'s text itself (e.g., an in-text reference token, `rag_design.md` Section 7.2) — it answers "which specific claim, in this specific answer, does this apply to." The distinction matters because it is the thing that makes an *unresolvable* reference meaningful: when a `CitationReference` cannot be resolved into a `Citation`, that is precisely the condition that sets a `Response`'s `unverified_statement_flag` (`rag_design.md` Section 7.3) — a fact that cannot be represented if the two concepts are collapsed into one.

**Lifecycle:** Created (implicitly, by being present in the generated text) alongside `GeneratedResponse`. Resolved into zero or one `Citation` by the Citation Mapper — but only reached in the grounded path; a `GeneratedResponse` that exists but is routed to the Not Found Path (trigger case 3, above) has any `CitationReference`s it might have carried left unresolved and irrelevant, since the answer is discarded in favor of the declined shape. Not persisted independently of the `Response` it contributed to.

**Relationships:**
- **Found within** a `GeneratedResponse`.
- **Resolves to** zero or one `Citation` (zero is the unverified-statement case, in the grounded state only).

### Response (Final Answer)

**Represents:** The citation-backed or declined answer actually returned to the employee — the object `interfaces.md` Section 6 named `Response`. See "Response State Clarification" above for the full grounded/declined breakdown; this is where grounding, traceability, and unverified-statement detection all become visible together: an answer that is either fully cited, partially cited-with-a-flag, or declined — never silently ungrounded.

**Responsibility:** In the grounded state, aggregates a `GeneratedResponse`'s text with its resolved `Citation[]` and the unverified-statement signal. In the declined state, is assembled directly by the Not Found Path with empty answer content and no citations. Either way, it is the one object every caller of the Query Orchestrator (`interfaces.md` 3.2) receives.

**Includes (conceptually):**
- Answer text (carried from `GeneratedResponse` in the grounded state; empty in the declined state)
- `Citation[]` (zero or more; always zero in the declined state)
- Unverified-statement flag (true if any `CitationReference` failed to resolve; always false in the declined state)
- A truncation indicator (carried from the `QueryContext` it was grounded on, where one exists)

**Lifecycle:** Created by the Citation Mapper stage (grounded) or the Not Found Path (declined) — see "Response State Clarification" above for the precise attribution per trigger case. Persisted, at minimum, as the most recent turn in its `ConversationSession` (Section 10), regardless of state.

**Relationships:**
- **Produced from** one `GeneratedResponse` and zero-or-more resolved `Citation`s (grounded state), or assembled directly with no upstream evidence lineage (declined state).
- **Recorded as** the assistant side of one `ConversationMessage` (Section 10).

---

## 10. Conversation Models

### ConversationSession

**Represents:** An employee's interaction session — the continuity that lets a follow-up question refer back to an earlier one.

**Includes (conceptually):**
- Session identity (a stable identifier, whose source — externally issued vs. system-generated — is an open architectural question, `architecture.md` Section 17, ADR candidate)
- Message history (an ordered collection of `ConversationMessage`, bounded per SRS FR-1303) — **one session contains many messages.**
- Lifecycle state (active, reset, expired)

**This document does not decide storage technology** for `ConversationSession` — **the model supports both MVP in-memory storage and future Redis, database-backed, or distributed-cache storage.** In-memory (MVP) and externalized (future production) are equally valid backing implementations behind the same interface (`interfaces.md` 4.8; `architecture.md` Section 3, "Session Management"). This document defines no Redis keys, no database tables, and no persistence mechanism of any kind — that is entirely a Provider Implementation concern (Section 2, "Provider Independence"), independent of which storage technology is eventually selected (ADR-007, `architecture.md` Section 17).

**Identity/state lifecycle:**

```
Created → Active → Reset / Expired
```

- *Created* — first turn of a new session.
- *Active* — accepting new `ConversationMessage`s.
- *Reset* — history cleared, identity retained (explicit user action, SRS FR-1305).
- *Expired* — per configured session lifetime; a business-meaningful transition, because it determines what context a later follow-up can legitimately draw on, not an implementation detail of the backing store.

**Relationships:**
- **Contains** `ConversationMessage[]` (ordered, bounded).
- **Referenced by** every `Query` asked within it.

### ConversationMessage

**Represents:** One turn within a session — a user message and, once processed, its assistant response.

**Includes (conceptually):**
- User message (the `Query` as originally asked)
- Assistant response (the `Response` produced for it, once available — grounded or declined, per Section 9)
- Timestamp information (when the turn occurred, for ordering and for session-lifetime calculations)

**Lifecycle:** Created when a `Query` is submitted (user side populated immediately); completed when the corresponding `Response` is produced (assistant side populated once, regardless of whether that `Response` is grounded or declined). Immutable once completed — a `ConversationMessage` is never edited, only appended after by later messages in the same session.

**Relationships:**
- **Belongs to** exactly one `ConversationSession`.
- **Contains** one `Query` and, once complete, one `Response`.

---

## 11. Error and Observability Models

**Ownership boundary, stated explicitly:** `ExecutionMetadata` and `ErrorContext` belong to **observability and error-tracking concerns** — they are cross-cutting metadata, never business objects, never pipeline state objects, and never response objects. Neither is ever embedded as a required field inside `Response`, `GeneratedResponse`, `QueryContext`, or any other business-facing model defined in Sections 3–10. A `Response`'s truncation indicator and `unverified_statement_flag` are business signals belonging to `Response` itself; `ExecutionMetadata` separately, and independently, logs how long the call took and under which correlation ID — the two are correlated (by correlation ID) but never merged into one model.

### ExecutionMetadata

**Represents:** The operational envelope attached to every component invocation, regardless of outcome.

**Includes (conceptually):**
- Correlation ID
- Timestamps (start, and on completion, end)
- Processing duration
- Component execution details (which orchestrator, stage, or provider interface this record belongs to)

**Responsibility:** Is the one operational record every interface call in `interfaces.md` Section 8 implicitly produces. It is always present — on success and on failure alike — which is what distinguishes it from `ErrorContext` below.

**Lifecycle:** Created at the start of a call, finalized at its end. Retained per the system's logging configuration (SRS FR-1501–1503), not defined here.

### ErrorContext

**Represents:** Normalized failure information — present only when a call fails.

**Includes (conceptually):**
- Error category (from the shared taxonomy — `interfaces.md` Section 7)
- Component (which component raised it)
- Correlation identifier (shared with the containing `ExecutionMetadata`, not a separate one)

**Modeling decision — containment, not a peer:** `ErrorContext` is not modeled as an independent top-level entity with its own lifecycle parallel to `ExecutionMetadata`. Per `interfaces.md` Section 8, error information is one field of the same operational record, present conditionally. Modeling it as a fully separate aggregate would imply it can exist without an `ExecutionMetadata`, which is never true — every `ErrorContext` is *part of* the `ExecutionMetadata` for the call that failed. It is documented here as its own named concept (because "what counts as an error, and how it's categorized" is genuine, reusable business meaning — SRS FR-1401) but is composed within, not alongside, `ExecutionMetadata`.

**Explicitly excludes** the four business outcomes `interfaces.md` Section 7 enumerates as *not* errors — an empty `SearchResult[]`, an LLM decline due to grounding, a truncated `QueryContext`, and an unresolved `CitationReference` (`unverified_statement_flag`). None of these ever populates an `ErrorContext`; each is represented in its own model above as a normal, successful field value (a `Response` with empty `Citation[]`, a `Response.unverified_statement_flag = true`, a `QueryContext` with its truncation indicator set) — never as a failure record. This mirrors `interfaces.md` Section 7's explicit warning almost verbatim, because the same misclassification risk exists at the domain-model level as at the interface level.

---

## 12. Domain Model Relationships

### Ingestion Relationship (Canonical Chain)

```
Document → ExtractedDocument → TextChunk → Embedding
```

- One `Document` contains many `TextChunk`s (via one `ExtractedDocument`).
- One `TextChunk` has exactly one current `Embedding`.

### Query Relationship (Canonical Chain — Corrected Order, Grounded Path Only)

```
Query → SearchResult → RetrievedChunk → QueryContext → GeneratedResponse → Citation
```

*A note on this ordering:* an earlier draft of this chain listed `QueryContext` immediately after `Query`, ahead of `SearchResult`/`RetrievedChunk`. That ordering does not match the actual system flow — `QueryContext` is *assembled from* `RetrievedChunk[]`, which is *derived from* `SearchResult[]`, which is produced only after the `Query` has been embedded and searched (`rag_design.md` Section 5, Query Data Flow Diagram; `interfaces.md` 4.11–4.12). The order above reflects the corrected, accurate sequence.

*A note on scope:* this chain shows the **grounded path only** — the path a `Query` follows when it is not short-circuited. See Section 9, "Response State Clarification," for the three declined-path variants, each of which exits this chain at a different point (before `SearchResult`, before `QueryContext`, or after `GeneratedResponse`).

- One `Query` may retrieve multiple chunks (`SearchResult[]`, narrowed to `RetrievedChunk[]`).
- One `QueryContext` is built from many `RetrievedChunk`s and exactly one `Query`.
- One `GeneratedResponse` may contain multiple `CitationReference`s, each resolving to zero or one `Citation`.
- One `Response` may contain multiple citations.

### Ingestion Flow (Full)

```
Document
   │ has-one
   ▼
DocumentMetadata

Document
   │ contains
   ▼
ExtractedDocument
   │ is the source of
   ▼
TextChunk ──has-one──► ChunkMetadata (references DocumentMetadata)
   │
   │ has-one
   ▼
Embedding
```

### Query Flow (Full, Grounded Path)

```
ConversationSession ──contains──► ConversationMessage[] ──contains──► Query

Query ──asked within──► ConversationSession
   │
   ▼ (produces, transient)
Embedding
   │
   ▼ (via Retriever)
SearchResult[] ──derived from (subset)──► RetrievedChunk[]
   │                                            │
   │                                            ▼
   │                                     QueryContext ◄──contains── Query
   │                                            │
   │                                            ▼ (via Prompt Assembler,
   │                                               rendered-prompt artifact
   │                                               not modeled)
   │                                     GeneratedResponse
   │                                            │
   │                            resolves CitationReference(s) within it
   │                                            ▼
   │                                     Citation[] ──attached to──► Response
   │                                                                     │
   ▼                                                                     ▼
                                                            ConversationMessage
                                                          (assistant side, completes the turn)
```

For the declined-path exits from this diagram (Not Found Path, three trigger cases), see Section 9.

### Cross-Cutting

```
Every call across both flows above produces one:

ExecutionMetadata
   │ (on failure only)
   ▼
ErrorContext (never populated by: empty SearchResult[], grounding-driven
              decline, truncated QueryContext, or unresolved CitationReference —
              see Section 11)
```

These are conceptual relationship diagrams, not database ER diagrams — no cardinality below is a foreign-key constraint; each is a business rule this document is asserting (e.g., "a `TextChunk` never has more than one *current* `Embedding`" is a rule the Embedding Generator's contract must honor, not a schema decision).

---

## 13. Model Boundary Validation

Every model above was tested against five questions before being kept: *why does it exist, what business meaning does it represent, which component creates it, which components consume it, and does it justify its own lifecycle (rather than existing only because of a processing step)?* This table records the answers compactly; the prose sections above give the full reasoning.

| Model | Why It Exists (Business Meaning) | Created By | Consumed By | Lifecycle Justification |
|---|---|---|---|---|
| `Document` | Identity/provenance for one source policy document | Document Loader | PDF Parser, Metadata Extractor, Vector Indexer | Independent — own version/retirement lifecycle |
| `DocumentMetadata` | Document-level identity, version, source, classification | Document Loader | Metadata Extractor (via reference), reporting | Tied to `Document`'s version lifecycle — no independent identity |
| `ExtractedDocument` | Audit-retained parsed content (raw + normalized) | PDF Parser / Text Preprocessor | Semantic Chunker, Document Store (audit) | Independent — retained for FR-305 audit regardless of chunk lifecycle |
| `TextChunk` | Permanent stored knowledge unit | Semantic Chunker | Metadata Extractor, Embedding Generator, Vector Indexer, Retriever | Independent — own identity, immutable, versioned via parent `Document` |
| `ChunkMetadata` | Chunk-scoped location/provenance facts | Metadata Extractor | Embedding Generator, Vector Indexer, Retriever, Citation Mapper | Tied to `TextChunk` — no independent identity |
| `Embedding` | Comparable vector representation + model version | Embedding Generator / Retriever (transient) | Vector Indexer, Vector Store Provider Interface | Tied to its `TextChunk`/`Query` — replaced, not versioned independently |
| `Query` | The employee's information request, across its lifecycle | Session Manager / Query Reformulator | Query Analyzer, Retriever, Prompt Assembler, Context Builder | Independent — own per-request lifecycle, short but real |
| `QueryContext` | Assembled grounding bundle for generation | Context Builder | Prompt Assembler | Tied to one request — no identity beyond it; never exists with zero evidence (Section 18) |
| `SearchResult` | Raw retrieval candidate | Retriever | Context Builder | Transient, but meaning is distinct: unfiltered candidate |
| `RetrievedChunk` | Selected evidence for answering | Context Builder | Citation Mapper (via `QueryContext`) | Transient, but meaning is distinct: chosen, not merely surfaced |
| `GeneratedResponse` | Pre-citation LLM output, completed only | Response Generator | Citation Mapper (grounded path only) | Tied to one request — exists only to separate generation from citation resolution |
| `Citation` | Resolved evidence pointer | Citation Mapper | `Response`, evaluation harness | Independent — immutable once resolved, attached permanently to its `Response` |
| `CitationReference` | Unresolved claim-to-evidence link | Citation Mapper (parsed from `GeneratedResponse`) | Citation Mapper (internal resolution step) | Transient, but meaning is distinct: makes "unresolvable" representable |
| `Response` | The final answer, grounded or declined | Citation Mapper (grounded) / Not Found Path (declined) | Query Orchestrator, Session Manager | Independent — persisted as part of `ConversationMessage`, in either state |
| `ConversationSession` | Interaction continuity across turns | Session Manager | Query Analyzer, Query Reformulator, Context Builder | Independent — own created/active/reset/expired lifecycle |
| `ConversationMessage` | One completed turn | Session Manager | Query Reformulator (history), evaluation harness | Independent — immutable once completed |
| `ExecutionMetadata` | Universal per-call operational envelope | every orchestrator, stage, provider interface | Logging/observability sink | Independent — created and finalized per call |
| `ErrorContext` | Normalized failure detail | the component that raised the failure | Orchestrators (retry/fail classification) | Not independent — composed within `ExecutionMetadata`, never a peer |

**Removal check:** no model in this document exists solely because of a processing step with no distinct business meaning. The two models with the shortest, most transient lifecycles (`SearchResult`, `CitationReference`) were kept specifically *because* their meaning is distinct from their nearest neighbor (`RetrievedChunk`, `Citation` respectively) — removing either would make an important system behavior (candidate-vs-evidence, resolved-vs-unresolved) unrepresentable. `QueryContext`/`PromptContext` and `Query`/`ReformulatedQuery` are the only two candidates that failed this test, and both were merged (Sections 6, 8). No new model was introduced in this stabilization pass — the `Response` correction (Section 9) fixed an attribution error, not a modeling gap.

---

## 14. Model Ownership Matrix

Every row below was checked against `architecture.md`'s dependency direction (Section 2 above): the **Owner Component** column is always a Pipeline Stage or a stage-equivalent responsibility (never an Orchestrator *deciding* business meaning, never a Provider Interface), confirming no domain model's ownership leaks across a layer boundary.

| Model | Owner Component | Used By |
|---|---|---|
| `Document` | Document Loader | PDF Parser, Metadata Extractor, Vector Indexer, Ingestion Orchestrator |
| `DocumentMetadata` | Document Loader | Metadata Extractor (referenced by `ChunkMetadata`), System Administrator-facing reporting |
| `ExtractedDocument` | PDF Parser / Text Preprocessor | Semantic Chunker, Document Store (audit) |
| `TextChunk` | Semantic Chunker | Metadata Extractor, Embedding Generator, Vector Indexer, Retriever |
| `ChunkMetadata` | Metadata Extractor | Embedding Generator, Vector Indexer, Retriever, Citation Mapper |
| `Embedding` | Embedding Generator (ingestion) / Retriever (query, transient) | Vector Indexer, Vector Store Provider Interface |
| `Query` | Session Manager / Query Reformulator | Query Analyzer, Retriever, Prompt Assembler, Context Builder |
| `QueryContext` | Context Builder | Prompt Assembler |
| `SearchResult` | Retriever | Context Builder |
| `RetrievedChunk` | Context Builder | Citation Mapper (via `QueryContext`) |
| `GeneratedResponse` | Response Generator | Citation Mapper (grounded path) |
| `Citation` | Citation Mapper | Response, evaluation harness (`rag_design.md` Section 9) |
| `CitationReference` | Citation Mapper (parsed from `GeneratedResponse`) | Citation Mapper (internal resolution step) |
| `Response` | **Citation Mapper (grounded state) / Not Found Path, `rag_design.md` 5.10 (declined state)** — corrected in v1.3, see Section 9 | Query Orchestrator, Session Manager (persisted into `ConversationMessage`) |
| `ConversationSession` | Session Manager | Query Analyzer, Query Reformulator, Context Builder |
| `ConversationMessage` | Session Manager | Query Reformulator (history), evaluation harness |
| `ExecutionMetadata` | every orchestrator, stage, and provider interface | Logging/observability sink (`interfaces.md` Section 8) |
| `ErrorContext` | the component that raised the failure | Orchestrators (recoverable/non-recoverable classification, `interfaces.md` Section 7) |

No model above has more than one owner *per instance*. Where a model has two plausible creators listed (`Embedding`, and now `Response`), these are mutually exclusive per-instance — a given instance is created by exactly one of the two, never both, depending on which path it took. The `Response` row's two creators are not an ownership violation: both Citation Mapper and the Not Found Path are stage-equivalent responsibilities (never the Query Orchestrator deciding business meaning on its own — see Section 9).

---

## 15. Domain Model Evolution

Domain models evolve with business requirements — this document is not expected to be the final word on any model's shape, but changes should follow these guidelines rather than happening ad hoc:

- **Domain models evolve with business requirements.** A model changes when `requirements.md` or `rag_design.md` changes in a way that alters business meaning — not because an implementation detail suggests a more convenient shape.
- **Changes should preserve compatibility where possible.** Adding an optional concept to an existing model (e.g., a new classification field on `DocumentMetadata`) should not require every consumer of that model to change simultaneously.
- **Provider replacement should not require domain model changes.** This is the same guarantee `interfaces.md` Section 10 makes for interface contracts, restated at the model level: swapping the vector database, embedding provider, or LLM provider behind their respective Provider Interfaces must never require a change to `Embedding`, `SearchResult`, or `GeneratedResponse`'s shape. If it does, a provider-specific detail leaked into the model, and that is the defect to fix — not the trigger to accept the model change.
- **Vector database migration should not leak schema objects.** Migrating from one vector database to another (ADR-003, `architecture.md` Section 17) must never surface that database's native result schema through `SearchResult` or `RetrievedChunk` — the Vector Store Provider Implementation performing the migration is responsible for continuing to satisfy the same `SearchResult` shape this document defines (Section 7), regardless of how the new database structures its own responses internally.
- **LLM provider changes should not affect response semantics.** Switching the LLM provider (ADR-005) must never change what a `GeneratedResponse` or `Response` *means* — the finish-reason vocabulary (Section 8), the citation resolution flow (Section 9), and the grounded/declined state distinction (Section 9) are all provider-independent business rules, not artifacts of any one LLM vendor's API shape.
- **Breaking model changes require sequence and test review.** Removing or repurposing an existing concept within a model (not merely adding to it) requires checking every consumer listed in Section 14's ownership matrix, and must be reviewed against `sequence_diagrams.md` and `testing.md` before being accepted — a model change that looks safe in isolation can still break an assumption a sequence diagram or test suite depends on.

No version numbers are defined for individual models in this document — that mechanism, if adopted, is a decision for `testing.md`/`tasks.md`, consistent with how `interfaces.md` Section 10 deferred the same question for interface contracts.

---

## 16. Avoided Design Patterns

The following are intentionally **not** present anywhere in this document, and should be treated as review-blocking if introduced later:

### Provider Leakage

Example of what is **not allowed**:

```
EmbeddingModel(OpenAIResponse)
```

A domain model must never be defined in terms of, or wrap, a specific vendor's SDK response type. `Embedding` (Section 5) carries a model identifier/version as an opaque string — never an object shaped by a specific provider's API.

### Framework Leakage

Example of what is **not allowed**:

```
LangChain Document
```

No domain model in this document is, wraps, or is defined in terms of a LangChain, LlamaIndex, or any other orchestration/RAG framework's native object. `Document` and `TextChunk` (Sections 3–4) are this system's own concepts, defined independently of how any framework happens to name an analogous idea (`requirements.md` C-001; `architecture.md` Section 1).

### Processing-Artifact Models

Examples of what is **not allowed** as a domain object:

```
RenderedPrompt
PromptTemplateResult
```

Neither the rendered LLM prompt text (Section 8) nor any other pure template-rendering output is modeled here. These are processing artifacts of the Prompt Assembler stage — they have no business meaning beyond "text sent to the LLM this one time" and no independent lifecycle. This is the same test applied throughout this document (Section 13, "Removal check") — a candidate that exists only because of a processing step, with no distinct business meaning, is not a domain model.

---

## 17. Validation Against `interfaces.md`

Every pipeline stage, orchestrator, and provider interface in `interfaces.md` was checked against this document to confirm its declared input and output reference an existing domain model (or are explicitly, and intentionally, non-domain — marked *n/a (processing artifact)* below).

| Interface | Input Models | Output Models |
|---|---|---|
| Ingestion Orchestrator (3.1) | `Document` (source reference) | Ingestion result — composition of `Document` + per-`TextChunk` outcomes, not a new model |
| Query Orchestrator (3.2) | `Query`, `ConversationSession` | `Response` (grounded or declined) |
| Document Loader (4.1) | raw source (pre-domain) | `Document` |
| PDF Parser (4.2) | `Document` | `ExtractedDocument` |
| Text Preprocessor (4.3) | `ExtractedDocument` (raw facet) | `ExtractedDocument` (normalized facet — same object, per Section 3 merge) |
| Semantic Chunker (4.4) | `ExtractedDocument` | `TextChunk[]` (unenriched) |
| Metadata Extractor (4.5) | `TextChunk`, `DocumentMetadata` | `TextChunk` + `ChunkMetadata` |
| Embedding Generator (4.6) | `TextChunk` | `Embedding` |
| Vector Indexer (4.7) | `TextChunk` + `Embedding` | Ingestion result summary (composition, not a new model) |
| Session Manager (4.8) | session identifier (pre-domain) | `ConversationSession` |
| Query Analyzer (4.9, provisional) | `ConversationSession` | query category (provisional — not yet a committed `Query` field, Section 20) |
| Query Reformulator (4.10) | `Query`, `ConversationSession` | `Query` (resolved form — same object, per Section 6 merge) |
| Retriever (4.11) | `Query` (via its transient `Embedding`) | `SearchResult[]` |
| Context Builder (4.12) | `SearchResult[]`, `ConversationSession` | `RetrievedChunk[]`, `QueryContext` (or the no-context signal that routes to the Not Found Path, Section 9) |
| Prompt Assembler (4.13) | `QueryContext` | *n/a (processing artifact)* — rendered prompt text, Section 16 |
| Response Generator (4.14) | *n/a (processing artifact)* — rendered prompt text | `GeneratedResponse` |
| Citation Mapper (4.15) | `GeneratedResponse`, `QueryContext` (citation metadata) | `Citation[]`, `Response` (grounded state only) |
| Not Found Path (`rag_design.md` 5.10) | none, or `GeneratedResponse` (trigger case 3, discarded — Section 9) | `Response` (declined state) |
| Embedding Provider Interface (5.1) | text (from `TextChunk` or `Query`) | `Embedding` |
| Vector Store Provider Interface (5.2) | `Embedding`, search criteria | `SearchResult[]` |
| LLM Provider Interface (5.3) | *n/a (processing artifact)* — rendered prompt text | `GeneratedResponse` |

**Result:** every interface's domain-facing input and output resolves to a model defined in Sections 3–11. The three cells marked *n/a (processing artifact)* are exactly the rendered-prompt boundary this document deliberately excludes from the domain model (Sections 8, 16) — their appearance here confirms the exclusion is consistent across every interface that touches it, not an oversight at just one. The Not Found Path row is new in this revision — it was missing from the previous validation pass, which is part of what allowed the `Response` attribution error (Section 9) to go unnoticed until now.

### Naming Aliases and Near-Duplicates

`interfaces.md` Section 6 named nine domain concepts using shorthand labels; this document uses fuller canonical names for some of them. None of the following pairs are duplicate or competing models — each is either a simple naming alias (same concept, different label) or a deliberate refinement (one concept split into two more precise ones), and both are recorded here so a reader moving between the two documents isn't left to guess:

| `interfaces.md` label | This document's name | Relationship |
|---|---|---|
| `Chunk` | `TextChunk` | Alias — same concept, fuller name used here |
| `Metadata` | `DocumentMetadata` + `ChunkMetadata` | Refinement, not a duplication — `interfaces.md` used one placeholder name for "attached to a chunk or document"; this document splits it into the document-level facts (`DocumentMetadata`) and the chunk-level facts that *reference* them (`ChunkMetadata`), per Sections 3–4. They are not duplicates of each other: `ChunkMetadata` never repeats a `DocumentMetadata` fact, it points to it. |
| `Session` | `ConversationSession` | Alias — same concept, fuller name used here |
| *(not named in `interfaces.md`)* | `Response` vs. `GeneratedResponse` | **Not an alias — genuinely distinct**, see Section 8–9. `GeneratedResponse` is the pre-citation LLM output; `Response` is the final, citation-resolved (or declined) answer. Conflating them would make the citation-resolution step (and the declined-state bypass of it) unrepresentable. |
| *(not named in `interfaces.md`)* | `QueryContext` vs. `PromptContext` | **Alias by merge** — `PromptContext` was a candidate name in early source material; tested and merged into `QueryContext` (Section 8). Not a live naming distinction going forward — `PromptContext` should not appear in `sequence_diagrams.md` or later documents. |
| *(not named in `interfaces.md`)* | `SearchResult` vs. `RetrievedChunk` | **Not an alias — genuinely distinct**, see Section 7. Candidate vs. selected evidence; conflating them would make "was this ever actually used as evidence" unanswerable. |

No renames were made during this review — every name in Sections 3–11 was already the correct, most precise name available; this subsection exists to document the *mapping*, not to change anything.

### Evaluation Traceability

`architecture.md` Section 5 defines Evaluation as a first-class capability. It observes — read-only — the models already defined in this document; it does not require its own persisted domain object. **No `EvaluationResult` model is introduced.** The three quality dimensions `rag_design.md` Section 9.2–9.3 measures are each a read over an existing chain:

**Retrieval quality:**
```
Query → SearchResult → RetrievedChunk
```
(Precision@K, Recall@K, Hit Rate@K, MRR — computed by comparing the `SearchResult`/`RetrievedChunk` set against a labeled expected answer, per `rag_design.md` Section 9.2.)

**Generation quality:**
```
QueryContext → GeneratedResponse
```
(Faithfulness, answer relevance, completeness — computed by comparing `GeneratedResponse`'s content against the evidence carried in `QueryContext`, per `rag_design.md` Section 9.3.)

**Citation quality:**
```
GeneratedResponse → Citation
```
(Citation correctness, and the aggregate `unverified_statement_flag` rate — computed from the `CitationReference`-to-`Citation` resolution outcomes across a labeled question set, per `rag_design.md` Section 9.1 item 4.)

The evaluation harness's metrics (Precision@K, MRR, faithfulness scores, etc.) are **computed values derived from these models at evaluation time** — they are not fields stored on `SearchResult`, `GeneratedResponse`, or `Citation` themselves, and they are not persisted as part of any domain model defined in this document. Where evaluation needs to retain a `Query`, `SearchResult`, `RetrievedChunk`, or `Response` for later comparison, it retains the existing model unchanged (Sections 6, 7, 9) — it does not wrap or extend it.

### Final Consolidated Traceability Table

A condensed, single-glance version of the validation above, at the granularity most useful for a `sequence_diagrams.md` author:

| Interface | Input Domain Models | Output Domain Models |
|---|---|---|
| Ingestion Orchestrator | `Document` | Indexed content (`TextChunk[]` + `Embedding[]`, composed) |
| Retriever | `Query` | `SearchResult[]` / `RetrievedChunk[]` (candidate vs. selected — Section 7) |
| Context Builder | `RetrievedChunk[]` | `QueryContext` |
| Response Generator | `QueryContext` | `GeneratedResponse` |
| Citation Mapper | `GeneratedResponse` | `Citation[]`, `Response` (grounded) |
| Not Found Path | (none) or `GeneratedResponse` | `Response` (declined) |
| Session Manager | session identifier | `ConversationSession` |
| Session Manager (per turn) | `ConversationSession` | `ConversationMessage` |
| Evaluation Harness | `Query` + `Response` (and the intermediate chain each references) | Metrics (computed, not a stored domain model) |

**Checks confirmed:**
- Every interface references an existing domain concept — none requires a model this document does not define.
- No domain model exists without at least one consumer (cross-checked against Section 14's "Used By" column).
- No interface's contract implies a missing model — the Not Found Path gap found during this review (above) has been closed.

---

## 18. Domain Model Guarantees

These are the specific runtime promises each model must uphold — stated per-model, distinct from the cross-model Runtime Invariants in Section 19. No implementation fields are defined here; each guarantee is a business-meaning constraint.

### QueryContext

Must represent:
- Retrieved evidence (`RetrievedChunk[]`, never empty — Section 6, Section 9)
- Context assembly metadata (the truncation indicator; which portion of `ConversationSession` history was included)
- Source traceability (every `RetrievedChunk` it contains remains traceable to its origin `SearchResult`, `TextChunk`, and `Document` — Section 2, "Traceability")

### RetrievedChunk

Must represent:
- Evidence selected for generation — **not merely raw vector search output.** A `RetrievedChunk` is never a bare copy of a `SearchResult`; it exists only because a selection decision (threshold, dedup, budget, ordering) was applied (Section 7).

### Citation

Must represent:
- A resolved source reference **only.** A `Citation` is never partially resolved, pending, or provisional — an in-progress or failed resolution is a `CitationReference` that has not (yet, or ever) become a `Citation` (Section 9).

### GeneratedResponse

Must distinguish:
- A **supported answer** — a completion with citable content, eligible for Citation Mapper processing.
- A **declined answer** — a completion whose finish reason indicates the context was insufficient, routed to the Not Found Path instead of Citation Mapper (Section 9).

Both are the same `GeneratedResponse` shape (Section 8) — the distinction lives in the finish-reason signal, not in a different type. This is the same "one shape" pattern documented for `Response` (Section 9) and is deliberate: the distinguishing information for both models is a signal *on* the object, not a fork *of* the object.

---

## 19. Runtime Invariants

The following rules must always remain true across every flow this document describes. Each was checked against the models and lifecycles defined in Sections 3–11 before being accepted as stated below.

### 1. A grounded Response requires QueryContext and GeneratedResponse; a declined Response's requirements depend on which of three trigger paths produced it.

Fully detailed in Section 9, "Response State Clarification" — restated compactly here: a `Response` that carries `Citation[]` is never created without a `QueryContext` and a `GeneratedResponse` having existed first. A declined `Response` may exist with neither (unsupported query, empty retrieval) or with both but no citation resolution having run (LLM decline). All three declined cases share one property: `Citation[]` is always empty and `unverified_statement_flag` is always `false`.

### 2. QueryContext cannot exist without retrieved evidence or an explicit no-context outcome.

A `QueryContext` (Section 6) is only ever constructed from a non-empty `RetrievedChunk[]`. When the Retriever's `SearchResult[]` is empty, the Context Builder does not construct a `QueryContext` with zero evidence and pass it downstream — it produces the explicit no-context signal that drives the declined `Response` path (invariant 1) instead. There is no such thing, in this model, as a `QueryContext` with an empty evidence set that proceeds to generation.

### 3. Citation cannot be created without CitationReference resolution.

Restates Section 9's `Citation` lifecycle directly: every `Citation` is "created by the Citation Mapper stage, by resolving a `CitationReference`." There is no path in this model that constructs a `Citation` directly from a claim without first having a `CitationReference` to resolve — an unresolvable claim produces the `unverified_statement_flag` (Section 9), never a fabricated `Citation`.

### 4. Provider failures cannot create partial GeneratedResponse.

A `GeneratedResponse` (Section 8) is only ever created on a *completed* LLM Provider call — including a completion whose finish reason is a grounding-driven decline (a successful call, per `interfaces.md` Section 7, "Not Error Conditions"). A genuine provider failure (rate-limited, timeout, transient, unknown — `interfaces.md` Section 5.3) never produces a `GeneratedResponse` at all; it produces an `ErrorContext` (Section 11) instead, and the Response Generator stage reports the failure rather than a partial result. This is the same "no partial pipeline output ever surfaced as complete" principle already stated for the system generally (SRS FR-1405, `architecture.md` Section 8.1), restated here specifically for `GeneratedResponse`. Section 8's Streaming Response Note further clarifies that `GeneratedResponse` represents a completed response only, by definition — there is no such thing as a "partial `GeneratedResponse`" instance to begin with, regardless of transport.

**Caveat — the caller-facing question is still open.** Section 8 resolves what `GeneratedResponse` itself can represent (completed only); it does not resolve what a *caller* should do with stream tokens it already received before a mid-stream failure was reported. **Streaming failure semantics require sequence diagram and deployment contract definition** — Open Decision 5 (Section 20).

### 5. Orchestrators cannot modify domain model meaning.

Restates `interfaces.md` Section 3's "Orchestrator Responsibility Boundary" at the model level: both orchestrators (Section 14's ownership matrix) pass domain models between stages unchanged. An orchestrator may *read* a model to decide routing (e.g., whether a `SearchResult[]` is empty, whether a `Response` carries citations) but never constructs, mutates, or reinterprets a domain model's business meaning itself. The Query Orchestrator's invocation of the Not Found Path (Section 9) is not an exception to this rule — the Not Found Path, not the orchestrator, is the component that assembles the declined `Response`, and it does so from a fixed, evidence-independent template, not a business decision.

### 6. Domain models cannot contain provider-specific objects.

Restates Section 2 ("Provider Independence") and Section 16 ("Avoided Design Patterns — Provider Leakage") as a runtime rule, not just a design-time principle: at no point during execution does any model instance (an `Embedding`, a `SearchResult`, a `GeneratedResponse`) carry a vendor SDK object as part of its actual runtime state. Translation happens once, at the Provider Implementation boundary, before the domain model instance is ever constructed (`architecture.md` Section 3, "Provider implementations translate external formats into domain models").

---

## 20. Open Decisions

The following remain genuinely unresolved by this document — distinct from the merge decisions in Sections 6 and 8, and distinct from the `Response` attribution error corrected in Section 9 (that was a documentation bug, not an open design question):

1. **Query Analyzer output model.** `Query`'s provisional query-category field (Section 6) is not committed as part of this domain model, because the Query Analyzer component itself is provisional pending requirements alignment (`architecture.md` Section 16; `interfaces.md` 4.9). If/when it is approved, this document will need a small addition (a query-category value) rather than a new top-level model.
2. **Query Reformulator mechanism.** The *model shape* is resolved (merged into `Query`, Section 6) — what remains open is *how* the resolved form is produced (deterministic transformation vs. LLM-assisted rewriting, `interfaces.md` 4.10), which has no bearing on this document but is flagged for `sequence_diagrams.md` and `tasks.md`.
3. **Session persistence details.** `ConversationSession`'s storage technology (in-memory vs. Redis vs. database-backed vs. distributed cache) is explicitly out of scope for this document (Section 10) and remains an open ADR (`architecture.md` ADR-007).
4. **Citation validation rules.** This document defines what a `Citation` and a `CitationReference` *are*, but not the precise rules for resolution confidence (e.g., how partial or ambiguous reference-token matches are handled, or whether a single claim may carry more than one `Citation`). `rag_design.md` Section 7 establishes the resolve-or-flag behavior at a high level; the precise matching rules are an implementation decision for `sequence_diagrams.md`/`tasks.md`, not a domain-model gap.
5. **Partial streamed output on provider failure.** Section 8 now resolves that `GeneratedResponse` itself is never partial — but whether tokens already delivered to a caller before a mid-stream LLM Provider failure must be explicitly invalidated, or are implicitly void once the call is reported as failed, is not resolved here. **Streaming failure semantics require sequence diagram and deployment contract definition** — flagged for `sequence_diagrams.md`, which will need to show the streaming failure path explicitly.

---

## 21. Related and Forthcoming Documents

- [requirements.md](./requirements.md) — the source of truth for *what* the system must do.
- [rag_design.md](./rag_design.md) — the source of truth for the pipeline design these models support.
- [architecture.md](./architecture.md) — the source of truth for system-level layering and the Domain Model Layer's place within it.
- [interfaces.md](./interfaces.md) — the source of truth for how these models are consumed and produced across component boundaries; this document is subordinate to it.
- `sequence_diagrams.md` (not yet created) — will show these models flowing through the diagrams in Section 12 above as concrete, timed sequences, including the three declined-path variants documented in Section 9 and the streaming-failure path flagged in Section 20.
- `testing.md`, `deployment.md`, `tasks.md` (not yet created) — later in the SDD chain; out of scope here.

Where this document and an upstream document disagree, the upstream document governs, per the SDD chain order above.

---

*End of Document.*

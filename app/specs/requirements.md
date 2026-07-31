# Software Requirements Specification (SRS)

## Enterprise HR Policy Assistant — Retrieval-Augmented Generation (RAG) Platform

| Field | Value |
|---|---|
| Document Type | Software Requirements Specification |
| Project Name | Enterprise HR Policy Assistant |
| Version | 1.0 |
| Status | Draft — Pending Review |
| Prepared By | Principal AI Solution Architect |
| Development Methodology | Specification-Driven Development (SDD) |
| Date | 2026-07-29 |

---

## Document Control

This document is the **single source of truth** for the Enterprise HR Policy Assistant. No implementation work (code, class design, folder structure, dependency selection beyond what is constrained herein) may begin until this specification has been reviewed and formally approved by all listed stakeholder roles. Any change to requirements after approval must be tracked via a version increment and a change log entry.

| Version | Date | Description | Author |
|---|---|---|---|
| 1.0 | 2026-07-29 | Initial draft for review | Principal AI Solution Architect |

---

## 1. Executive Summary

The Enterprise HR Policy Assistant is a production-grade Retrieval-Augmented Generation (RAG) system that allows employees to ask natural-language questions about internal HR policies (leave, benefits, code of conduct, reimbursement, compliance, etc.) and receive accurate, citation-backed answers grounded in the organization's authoritative HR policy documents.

Unlike a demonstration chatbot, this system is designed to production engineering standards: it must be observable, secure, reliable, testable, modular, and cost-aware. It is built with custom orchestration logic rather than a high-level orchestration framework (e.g., LangChain), giving the engineering team full control and transparency over the retrieval and generation pipeline. The system is designed to be framework-independent at its core, with a clear path to exposure via a FastAPI service layer and deployment via Docker to any cloud provider.

This document defines **what** the system must do and **how well** it must do it. It intentionally does not define **how** the system is implemented internally (no code, no class diagrams, no folder layout) — those decisions belong to the design and implementation phases that follow formal approval of this specification.

---

## 2. Business Objectives

| ID | Objective | Success Indicator |
|---|---|---|
| BO-001 | Reduce time employees spend searching for HR policy information | Median time-to-answer for a policy question is measurably reduced versus manual document search |
| BO-002 | Reduce repetitive HR helpdesk load for common policy questions | Measurable reduction in low-complexity HR ticket volume attributable to self-service Q&A |
| BO-003 | Increase trust in AI-generated answers through verifiable citations | Every answer traceable to source document(s), section(s), and page(s) |
| BO-004 | Demonstrate production-grade AI engineering practice | System meets all non-functional requirements defined in Section 7 and passes acceptance criteria in Section 10 |
| BO-005 | Ensure the platform can evolve without a rewrite | System satisfies extensibility and modularity requirements (Section 7.7, 7.9) enabling new document types, LLM providers, or vector stores to be added without core rework |
| BO-006 | Keep the platform operable within a predictable cost envelope | Cost-per-query and monthly infrastructure cost are tracked and bounded per NFR-COST requirements |

---

## 3. Scope

### 3.1 In Scope

- Ingestion of internal HR policy documents (PDF format, see FR-101) into a searchable knowledge base.
- Parsing, cleaning, chunking, and metadata-tagging of policy documents.
- Generation and storage of vector embeddings for semantic search.
- A retrieval pipeline that finds the most relevant policy content for a given employee question.
- Construction of grounded prompts and generation of natural-language answers via a Large Language Model (LLM).
- Citation of source document, section, and page for every factual claim in a generated answer.
- Multi-turn conversational support (follow-up questions with context retention).
- Structured error handling, logging, and configuration management suitable for production operation.
- Non-functional characteristics (performance, scalability, reliability, security, observability, etc.) required for enterprise deployment.

### 3.2 Out of Scope (v1.0)

- Authentication/Identity provider integration (assumed to be handled by a surrounding enterprise gateway — see Assumptions).
- A user-facing web or chat UI (the system exposes a backend capability; UI is a future enhancement).
- Write-back actions (e.g., submitting leave requests, updating employee records). The system is read-only/advisory.
- Support for non-HR document domains.
- Real-time document co-authoring or policy authoring workflows.
- Multi-language translation of source policies (only the language(s) explicitly listed in FR-102 are supported in v1.0).
- Fine-tuning or training custom LLMs or embedding models.

### 3.3 Deployment Scope

The system must be designed so that its core logic is deployable as a containerized service (Docker) fronted in the future by a FastAPI application layer, and portable across at least one major public cloud provider without code changes to core logic (cloud portability, see NFR-SCALE and Constraints, Section 8).

---

## 4. Stakeholders

| Role | Interest / Responsibility |
|---|---|
| Solution Architect | Owns overall technical design consistency, ensures NFRs are architecturally achievable, approves this SRS |
| Engineering Manager | Owns delivery timeline, resourcing, and risk tracking against this SRS |
| AI/ML Engineer | Implements ingestion, embedding, retrieval, and generation pipeline against these requirements |
| Backend/Platform Engineer | Implements configuration, logging, error handling, and future FastAPI/Docker integration |
| QA Engineer | Derives test plans and acceptance test cases directly from Sections 6, 7, and 10 |
| HR Policy Owner (Business Stakeholder) | Provides authoritative source documents, validates answer correctness and citation accuracy |
| Security/Compliance Officer | Reviews data handling, access control assumptions, and audit requirements |
| End User (Employee) | Consumes the system's answers; primary source of usability/accuracy expectations |
| DevOps/SRE | Owns deployment, monitoring, and operational runbooks post-implementation |

---

## 5. Assumptions

| ID | Assumption |
|---|---|
| AS-001 | HR policy source documents are provided as digitally generated or scanned PDF files supplied by the HR Policy Owner. |
| AS-002 | Authentication and authorization of end users are handled by an external identity provider/API gateway; this system trusts an already-authenticated caller identity passed to it. |
| AS-003 | The system operates within a single organizational tenant (no multi-tenant document isolation required in v1.0). |
| AS-004 | Source HR policy documents are in English for v1.0. |
| AS-005 | An LLM API (hosted, e.g., Anthropic Claude or equivalent) and an embeddings API/library are available and reachable from the deployment environment. |
| AS-006 | A vector database (self-hosted or managed) is available and reachable from the deployment environment. |
| AS-007 | Document updates (new/revised policies) occur periodically (not real-time streaming) and can be handled via a re-ingestion process. |
| AS-008 | The HR Policy Owner is responsible for the accuracy of source documents; the system is responsible for faithfully retrieving and representing their content. |
| AS-009 | Expected query volume is consistent with a single enterprise (hundreds to low thousands of employees), not internet-scale public traffic. |

---

## 6. Functional Requirements

Each functional requirement includes a unique ID, description, and acceptance-relevant detail. Requirements are grouped by pipeline stage.

### 6.1 Document Ingestion

**FR-101** — The system shall accept HR policy source documents in PDF format as the primary supported input type for v1.0.

**FR-102** — The system shall support ingestion of documents written in English; documents in unsupported languages shall be rejected with a clear error (see FR-901).

**FR-103** — The system shall allow ingestion of a single document or a batch of multiple documents in one ingestion run.

**FR-104** — The system shall assign a unique, stable document identifier to each ingested source document, derived deterministically from document content and/or filename, such that re-ingesting an unchanged document does not create duplicate entries.

**FR-105** — The system shall support re-ingestion (update) of a previously ingested document, replacing outdated chunks and embeddings associated with the prior version while preserving the document identifier.

**FR-106** — The system shall support removal (deletion) of a previously ingested document and all its derived chunks, embeddings, and metadata from the knowledge base.

**FR-107** — The system shall validate that an incoming file is a well-formed, non-corrupted PDF before processing, and shall reject malformed files with a descriptive error.

**FR-108** — The system shall enforce a configurable maximum file size per document (see FR-1601 for configuration) and reject files exceeding it with a descriptive error.

**FR-109** — The system shall record ingestion provenance for every document: source filename, ingestion timestamp, ingesting user/process identifier, and document version number.

### 6.2 PDF Parsing

**FR-201** — The system shall extract the full textual content of each page of an ingested PDF, preserving reading order to the extent supported by the underlying parsing library.

**FR-202** — The system shall extract and retain page-number boundaries so that any extracted text span can be traced back to its originating page number(s).

**FR-203** — The system shall detect and extract structural elements where present, including section headings, subheadings, and numbered/bulleted lists, to support downstream semantic chunking and metadata extraction.

**FR-204** — The system shall detect tabular content and extract it in a form that preserves row/column relationships to the extent supported by the underlying parsing library; where extraction fidelity is insufficient, the system shall flag the page as "reduced-fidelity extraction" in metadata rather than silently discarding content.

**FR-205** — The system shall handle scanned/image-based PDF pages by flagging them as requiring OCR or as unparseable, and shall not silently produce empty or corrupted text for such pages; the ingestion result shall report which pages, if any, failed full-text extraction.

**FR-206** — The system shall reject or flag PDFs protected by a password/encryption in a way that prevents text extraction, and shall report this as an ingestion failure with a descriptive error rather than partial/silent failure.

### 6.3 Text Preprocessing

**FR-301** — The system shall normalize extracted text by removing artifacts introduced by PDF extraction (e.g., hyphenation line-breaks, repeated headers/footers, page-number strings, non-semantic whitespace).

**FR-302** — The system shall preserve semantically meaningful formatting (e.g., list structure, section numbering) during normalization rather than flattening all text into an undifferentiated block.

**FR-303** — The system shall detect and remove exact-duplicate boilerplate text (e.g., repeated legal disclaimers on every page) when such repetition would degrade chunk quality, while retaining at least one canonical occurrence in metadata.

**FR-304** — The system shall normalize character encoding to a consistent standard (UTF-8) across all processed text.

**FR-305** — The system shall preserve the original, unmodified extracted text alongside the normalized/cleaned text for audit and debugging purposes.

### 6.4 Semantic Chunking

**FR-401** — The system shall split normalized document text into chunks suitable for embedding and retrieval, using semantically coherent boundaries (e.g., section, paragraph, or topic boundaries) rather than fixed character counts alone.

**FR-402** — The system shall enforce a configurable target chunk size (measured in tokens) and a configurable maximum chunk size, with chunking logic that respects semantic boundaries before falling back to hard splits when a semantic unit exceeds the maximum size.

**FR-403** — The system shall apply configurable overlap between adjacent chunks to preserve context continuity across chunk boundaries.

**FR-404** — The system shall never split a chunk in the middle of a sentence where a sentence boundary can be reasonably detected.

**FR-405** — Each chunk shall retain a reference to its position within the source document (document ID, page number(s), section/heading path) sufficient to reconstruct its origin.

**FR-406** — The system shall assign each chunk a unique, stable chunk identifier.

**FR-407** — The chunking strategy shall be configurable (chunk size, overlap, splitting strategy) without requiring code changes (see FR-1601).

### 6.5 Metadata Extraction

**FR-501** — The system shall extract and attach the following metadata, at minimum, to every chunk: source document ID, source filename, document title (if determinable), section/heading path, page number(s), document version, ingestion timestamp, and chunk ID.

**FR-502** — The system shall attempt to extract policy-domain metadata where identifiable in the source document, including but not limited to: policy category (e.g., "Leave", "Benefits", "Code of Conduct"), effective date, and policy owner/department.

**FR-503** — The system shall mark metadata fields that could not be confidently extracted as explicitly absent/null rather than inferring or fabricating values.

**FR-504** — The system shall support attaching a document-level access classification tag (e.g., "General", "Confidential") to support future access-control extensibility, even if access enforcement itself is out of scope for v1.0 (see Section 3.2).

**FR-505** — Extracted metadata shall be stored alongside each chunk's embedding in the vector database and shall be retrievable together with the chunk content at query time.

### 6.6 Embedding Generation

**FR-601** — The system shall generate a vector embedding for every chunk produced during ingestion, using a configurable embedding model accessed via a library/API (not a hand-rolled model).

**FR-602** — The system shall generate a vector embedding for every incoming user query at retrieval time, using the same embedding model/version used for the corresponding indexed chunks.

**FR-603** — The system shall record the embedding model name and version used to produce each stored vector, so that mismatched-model retrieval can be detected and prevented.

**FR-604** — The system shall support batch embedding generation during ingestion to enable efficient processing of multi-document ingestion runs.

**FR-605** — The system shall handle embedding API failures (rate limits, timeouts, transient errors) with retry logic and shall report unrecoverable failures per-chunk without aborting the entire ingestion batch, where feasible.

**FR-606** — The system shall support re-embedding of existing chunks when the configured embedding model is changed, without requiring re-parsing or re-chunking of source documents.

### 6.7 Vector Database Storage

**FR-701** — The system shall persist chunk text, chunk metadata (Section 6.5), and chunk embeddings in a vector database accessed via a library/API.

**FR-702** — The system shall support upsert semantics: inserting new chunks and updating/replacing chunks associated with a re-ingested document version (see FR-105) without leaving orphaned stale vectors.

**FR-703** — The system shall support deletion of all vectors associated with a given document ID (see FR-106).

**FR-704** — The system shall support metadata-filtered vector search (e.g., restrict search to a policy category or document) in addition to pure semantic similarity search.

**FR-705** — The vector database interaction shall be abstracted such that the underlying vector database technology can be replaced without requiring changes to ingestion or retrieval business logic (see NFR-EXT requirements, Section 7.7).

### 6.8 Semantic Retrieval

**FR-801** — The system shall, given a user query, retrieve the top-K most semantically relevant chunks from the vector database, where K is configurable.

**FR-802** — The system shall support a configurable minimum similarity-score threshold below which retrieved chunks are discarded as irrelevant.

**FR-803** — The system shall support hybrid retrieval (combining semantic similarity with metadata filters such as policy category) when such filters are inferable from the query or supplied explicitly.

**FR-804** — The system shall support re-ranking of an initial retrieved candidate set to improve precision of the final chunk set passed to context construction (mechanism configurable/pluggable; no specific re-ranking algorithm is mandated by this SRS).

**FR-805** — If no chunks meet the relevance threshold, the system shall return a clearly identified "no relevant policy information found" result rather than forcing generation from irrelevant context.

**FR-806** — The system shall deduplicate near-identical retrieved chunks (e.g., overlapping chunks from FR-403) before passing them to context construction.

### 6.9 Context Construction

**FR-901** — The system shall assemble retrieved chunks into a bounded context payload for the LLM, respecting a configurable maximum context token budget.

**FR-902** — The system shall order assembled context chunks by relevance and/or document structure in a deterministic, explainable manner.

**FR-903** — The system shall preserve, for every chunk included in context, the metadata required to later produce a citation (document, section, page) (see FR-1201).

**FR-904** — When the total token size of retrieved relevant chunks exceeds the configured context budget, the system shall apply a defined truncation/selection strategy (e.g., highest-relevance-first) and shall record that truncation occurred.

**FR-905** — In multi-turn conversations, the system shall incorporate relevant prior conversation turns into context construction per the conversation support requirements (Section 6.13), in addition to newly retrieved chunks.

### 6.10 Prompt Generation

**FR-1001** — The system shall construct LLM prompts using a defined, versioned prompt template that separates system instructions, retrieved context, conversation history (if any), and the current user question.

**FR-1002** — The system shall instruct the LLM, via the prompt, to answer only using the supplied retrieved context and to explicitly decline to answer when the context is insufficient, rather than relying on the model's general/background knowledge.

**FR-1003** — The system shall instruct the LLM, via the prompt, to produce answers in a format that includes inline or structured references to the source chunk(s) used, sufficient to support citation generation (FR-1201).

**FR-1004** — Prompt templates shall be stored/managed as configuration/versioned assets, not hard-coded inline within business logic, to support iteration without core code changes.

**FR-1005** — The system shall support injecting a small number of few-shot examples into the prompt template to standardize answer format and tone, where such examples are configured.

### 6.11 LLM Response Generation

**FR-1101** — The system shall submit the constructed prompt to a configured LLM via an API/library and obtain a generated natural-language answer.

**FR-1102** — The system shall support configuration of the LLM provider, model name, and key generation parameters (e.g., temperature, max output tokens) without requiring code changes.

**FR-1103** — The system shall enforce a configurable timeout on LLM generation calls and treat a timeout as a recoverable error subject to the error-handling requirements in Section 6.15.

**FR-1104** — The system shall detect and handle LLM API failures (rate limiting, service errors, content-policy refusals) distinctly, and surface an appropriate user-facing message for each category rather than a generic failure.

**FR-1105** — The system shall support streaming of the generated answer to the caller where the underlying LLM API supports streaming, as a configurable mode.

**FR-1106** — The system shall not fabricate an answer when the LLM indicates it cannot answer from the supplied context; in that case, the system shall return a "not found in policy documents" style response rather than allowing hallucinated content to reach the user (supports BO-003).

### 6.12 Citation Generation

**FR-1201** — Every generated answer that includes factual content drawn from retrieved context shall be accompanied by one or more citations identifying, at minimum: source document title/filename, section/heading (if available), and page number(s).

**FR-1202** — The system shall map each cited claim back to the specific chunk(s) that supplied it, such that a reviewer can verify the answer against the original source text.

**FR-1203** — If the LLM's generated answer references information not traceable to any retrieved chunk, the system shall flag the answer as containing an unverified/uncited statement rather than presenting it as fully grounded.

**FR-1204** — Citations shall be returned as structured data (not only inline prose) so that a downstream client (e.g., a future UI) can render them distinctly from answer text.

**FR-1205** — When the system returns a "no relevant policy information found" result (FR-805, FR-1106), no citations shall be fabricated.

### 6.13 Conversation Support

**FR-1301** — The system shall support multi-turn conversations in which a user may ask follow-up questions that depend on prior turns within the same session.

**FR-1302** — The system shall maintain conversation history scoped to a session identifier, and shall not leak conversation history across unrelated sessions.

**FR-1303** — The system shall support configurable conversation history length (number of turns or token budget) to bound prompt growth in long conversations.

**FR-1304** — The system shall resolve ambiguous follow-up queries (e.g., pronouns referring to a prior topic) using conversation history as part of query understanding/reformulation prior to retrieval.

**FR-1305** — The system shall allow a session to be explicitly reset/cleared, discarding prior conversation history.

**FR-1306** — The system shall persist conversation history for the duration of a session in a manner that survives a single request/response cycle, with the persistence mechanism itself left as an implementation decision consistent with Section 8 constraints.

### 6.14 Error Handling

**FR-1401** — The system shall define distinct, catalogued error categories at minimum for: ingestion errors, parsing errors, embedding errors, retrieval errors, LLM generation errors, and configuration errors.

**FR-1402** — Every error surfaced to a caller shall include a stable error code, a human-readable message, and sufficient context (e.g., document ID, chunk ID, session ID) to support debugging, without leaking internal implementation details (e.g., stack traces, credentials) to end users.

**FR-1403** — The system shall distinguish between recoverable errors (subject to retry, e.g., transient API failures) and non-recoverable errors (e.g., malformed input), and shall apply retry logic with backoff only to the former.

**FR-1404** — The system shall fail a single document's ingestion without aborting a concurrent batch ingestion of other documents (partial-failure isolation).

**FR-1405** — The system shall never present a fabricated or partially-generated answer to the user as if it were complete when an underlying pipeline stage failed; a failed stage shall result in a clear error/degraded-response indication instead.

### 6.15 Logging

**FR-1501** — The system shall emit structured (machine-parseable) logs for every pipeline stage: ingestion, parsing, chunking, embedding, retrieval, prompt construction, LLM generation, and citation generation.

**FR-1502** — Each log entry relevant to a user query shall include a correlation/request ID that allows all logs for a single query to be traced end-to-end across pipeline stages.

**FR-1503** — The system shall log, at minimum, per query: retrieved chunk IDs and relevance scores, LLM model/version used, generation latency, and whether citations were produced.

**FR-1504** — The system shall support configurable log levels (e.g., DEBUG, INFO, WARN, ERROR) without requiring code changes.

**FR-1505** — The system shall avoid logging sensitive content (e.g., full document text bodies at INFO level in production) beyond what is necessary for operability, consistent with Section 7.6 security requirements.

### 6.16 Configuration Management

**FR-1601** — All operationally variable parameters — including but not limited to chunk size/overlap, top-K retrieval count, similarity threshold, context token budget, LLM provider/model/parameters, embedding model, log level, and file size limits — shall be externally configurable without requiring code changes or redeployment of application logic.

**FR-1602** — The system shall support distinct configuration profiles for at least development, testing, and production environments.

**FR-1603** — The system shall validate configuration values at startup and fail fast with a descriptive error if required configuration is missing or invalid, rather than failing later during request processing.

**FR-1604** — Secrets (API keys, database credentials) shall be sourced from a secure configuration mechanism (e.g., environment variables or a secrets manager) and shall never be committed to source control or logged in plaintext.

**FR-1605** — The system shall report its effective configuration (with secrets redacted) via an internal diagnostic capability to support troubleshooting.

---

## 7. Non-Functional Requirements

### 7.1 Performance

**NFR-PERF-001** — For a query against an already-ingested knowledge base, the system shall return a complete answer (non-streaming mode) within a configurable target latency budget, with a default target of end-to-end p95 latency ≤ 8 seconds under nominal load (excluding network transit to the end client).

**NFR-PERF-002** — In streaming mode, the system shall emit the first generated token within a configurable target, with a default target of p95 time-to-first-token ≤ 3 seconds under nominal load.

**NFR-PERF-003** — Semantic retrieval (vector search) shall complete within p95 ≤ 500ms for a knowledge base of up to 100,000 chunks under nominal load.

**NFR-PERF-004** — Document ingestion throughput shall process a 50-page PDF (parsing through embedding, excluding LLM calls) in a target of ≤ 2 minutes under nominal load.

### 7.2 Scalability

**NFR-SCALE-001** — The system shall support horizontal scaling of the retrieval/generation request path (i.e., stateless request handling) to accommodate concurrent user load, with the initial target of at least 50 concurrent active sessions without degradation beyond the latency budgets in 7.1.

**NFR-SCALE-002** — The system shall support a knowledge base of at least 10,000 pages of source HR policy documents (approx. 100,000+ chunks) without requiring architectural redesign.

**NFR-SCALE-003** — Ingestion and query-serving workloads shall be independently scalable (i.e., a spike in ingestion load shall not degrade query-serving latency, and vice versa).

### 7.3 Reliability

**NFR-REL-001** — The query-serving path shall achieve a target availability of 99.5% measured monthly, excluding scheduled maintenance windows.

**NFR-REL-002** — The system shall degrade gracefully when a downstream dependency (LLM API, embedding API, vector database) is unavailable, returning a clear service-degraded error rather than hanging indefinitely or crashing (ties to FR-1103, FR-1401).

**NFR-REL-003** — The system shall apply retry-with-backoff for transient failures on all external API calls (LLM, embeddings, vector database), with a configurable maximum retry count and backoff strategy.

**NFR-REL-004** — Ingestion of a document shall be idempotent: re-running ingestion on an unchanged document shall not corrupt or duplicate existing knowledge base entries (ties to FR-104, FR-702).

**NFR-REL-005** — No single document's ingestion failure shall be capable of corrupting or degrading retrieval quality for previously successfully ingested documents (ties to FR-1404).

### 7.4 Maintainability

**NFR-MAINT-001** — Each pipeline stage (ingestion, parsing, chunking, embedding, retrieval, prompt construction, generation, citation) shall be independently modifiable such that a change to one stage's internal logic does not require changes to unrelated stages, verified through the modularity requirements in 7.9.

**NFR-MAINT-002** — All configurable parameters (Section 6.16) shall be centrally documented, with default values and valid ranges specified.

**NFR-MAINT-003** — The system's prompt templates (FR-1004) shall be independently versioned so that a prompt change can be tracked, reviewed, and rolled back without touching business logic code.

### 7.5 Observability

**NFR-OBS-001** — The system shall expose health-check capability sufficient to distinguish "process is running" from "process is ready to serve requests" (dependencies reachable).

**NFR-OBS-002** — The system shall expose operational metrics at minimum for: request rate, error rate, latency percentiles (p50/p95/p99) per pipeline stage, retrieval relevance score distribution, and LLM token usage per query.

**NFR-OBS-003** — Every user-facing request shall be traceable end-to-end via a correlation ID present in logs and, where applicable, metrics (ties to FR-1502).

**NFR-OBS-004** — The system shall support alerting integration (i.e., emit signals suitable for external alerting) on elevated error rates, elevated latency, and downstream dependency failures; the specific alerting tool is an implementation decision outside this SRS's scope.

### 7.6 Security

**NFR-SEC-001** — All communication with external APIs (LLM provider, embedding provider, vector database) shall use encrypted transport (TLS).

**NFR-SEC-002** — Secrets and credentials shall never appear in logs, error messages, or version-controlled configuration files (ties to FR-1604).

**NFR-SEC-003** — The system shall treat all employee-submitted query text as untrusted input and shall sanitize/validate it before use in downstream processing (e.g., preventing prompt-injection payloads from overriding system instructions where technically mitigable).

**NFR-SEC-004** — The system shall support restricting ingestion capability to authorized processes/roles only, distinct from query-serving access (ties to AS-002).

**NFR-SEC-005** — The system shall support the document-level access classification tag (FR-504) as a forward-compatible hook for future access-control enforcement, even though enforcement itself is out of scope for v1.0.

**NFR-SEC-006** — The system shall not transmit full source document contents to any third-party service beyond what is strictly required for embedding generation and LLM-based answer generation.

**NFR-SEC-007** — The system shall maintain an audit trail (via logging, Section 6.15) of ingestion actions (who ingested/updated/deleted which document, when) sufficient to support a compliance review.

### 7.7 Extensibility

**NFR-EXT-001** — The embedding provider/model shall be replaceable via configuration and an abstracted interface, without requiring changes to ingestion, retrieval, or generation business logic (ties to FR-601, FR-705).

**NFR-EXT-002** — The vector database technology shall be replaceable via an abstracted interface without requiring changes to ingestion or retrieval business logic (ties to FR-705).

**NFR-EXT-003** — The LLM provider/model shall be replaceable via configuration and an abstracted interface without requiring changes to retrieval or context-construction logic (ties to FR-1102).

**NFR-EXT-004** — The system's core logic shall be exposable through additional interface layers (e.g., a future FastAPI HTTP layer) without modification to core ingestion/retrieval/generation logic, i.e., core logic shall not assume a specific transport or interface framework.

**NFR-EXT-005** — The document ingestion pipeline shall be designed such that support for additional source document formats beyond PDF (e.g., DOCX, HTML) can be added by introducing a new parser component without altering downstream chunking, embedding, or retrieval logic.

### 7.8 Testability

**NFR-TEST-001** — Each pipeline stage (Section 6) shall be independently testable in isolation (unit-testable) via well-defined inputs/outputs, without requiring a live LLM, embedding API, or vector database connection for core logic tests.

**NFR-TEST-002** — The system shall support integration testing of the full ingestion-to-answer pipeline using a reproducible, version-controlled test document set and test query set with expected-citation assertions.

**NFR-TEST-003** — The system shall support deterministic or bounded-variance evaluation of answer quality (e.g., retrieval precision/recall against a labeled test set) to support regression testing of retrieval and prompt changes over time.

**NFR-TEST-004** — Error-handling paths (Section 6.14) shall be independently testable by simulating downstream dependency failures (LLM timeout, embedding API error, vector database unavailability).

### 7.9 Modularity

**NFR-MOD-001** — The system shall be decomposed into independently addressable functional components corresponding to the pipeline stages in Section 6 (ingestion, parsing, preprocessing, chunking, metadata extraction, embedding, vector storage, retrieval, context construction, prompt generation, LLM generation, citation generation, conversation management, error handling, logging, configuration).

**NFR-MOD-002** — Components shall communicate through well-defined data contracts (inputs/outputs) rather than shared mutable state, so that a component's internal implementation can change without affecting callers, consistent with the "no LangChain orchestration, custom orchestration logic" constraint (Section 8).

**NFR-MOD-003** — The orchestration logic that sequences pipeline stages shall be separable from the individual stage implementations, such that the orchestration flow itself can be inspected, tested, and modified independently of any single stage's internal logic.

### 7.10 Cost Optimization

**NFR-COST-001** — The system shall track and report LLM token consumption (input + output) and embedding API call volume per query and in aggregate, to support cost monitoring.

**NFR-COST-002** — The system shall support configuration of context token budgets (FR-901) and top-K retrieval counts (FR-801) specifically as cost-control levers, documented as such.

**NFR-COST-003** — The system shall avoid redundant embedding generation: an unchanged document or unchanged chunk shall not be re-embedded on repeat ingestion runs (ties to FR-105, NFR-REL-004).

**NFR-COST-004** — The system shall support caching of identical or near-duplicate queries within a session to avoid redundant LLM calls, where such caching does not compromise answer freshness requirements.

**NFR-COST-005** — A target cost-per-query ceiling shall be configurable and monitorable, with the system emitting a warning signal (via observability, Section 7.5) when actual average cost-per-query exceeds the configured ceiling over a rolling window.

---

## 8. Constraints

| ID | Constraint |
|---|---|
| C-001 | The system shall NOT use LangChain (or equivalent high-level RAG orchestration frameworks) for pipeline orchestration. |
| C-002 | Pipeline orchestration (sequencing ingestion, retrieval, prompt construction, generation, citation) shall be custom-built logic owned by the engineering team. |
| C-003 | Third-party libraries/APIs may be used only for: embedding generation, PDF parsing, vector database access, and LLM API access. Use of additional libraries for orchestration, chunking strategy, or business logic frameworks is disallowed. |
| C-004 | The system's core logic shall be framework-independent — it shall not be architecturally coupled to any specific web framework. |
| C-005 | The system shall be designed such that a FastAPI layer can be added in the future to expose HTTP endpoints without requiring changes to core pipeline logic (see NFR-EXT-004). |
| C-006 | The system shall be deployable as a Docker container. |
| C-007 | The system shall be cloud-portable — it shall not depend on a proprietary, single-cloud-only managed service for any core capability (embedding, LLM, vector store) in a way that prevents deployment to an alternative cloud provider; provider-specific services must be substitutable via configuration/abstraction (see NFR-EXT-001 through 003). |
| C-008 | This project follows Specification-Driven Development: no implementation code, class design, or folder structure shall be produced or finalized until this SRS is formally reviewed and approved by the stakeholders listed in Section 4. |

---

## 9. Risks

| ID | Risk | Likelihood | Impact | Mitigation Direction |
|---|---|---|---|---|
| R-001 | PDF parsing fidelity loss (tables, multi-column layouts, scanned pages) leads to incomplete or incorrect chunk content | Medium | High | FR-204, FR-205 mandate explicit fidelity flagging rather than silent failure; QA must include visually complex policy PDFs in test set |
| R-002 | LLM hallucination despite grounding instructions, producing plausible but incorrect policy answers | Medium | High | FR-1002, FR-1106, FR-1203 mandate context-only answering and uncited-statement flagging; requires evaluation against labeled test set (NFR-TEST-003) |
| R-003 | Embedding/LLM model drift or version changes silently degrading retrieval or answer quality | Low-Medium | Medium | FR-603 mandates model/version tracking; NFR-TEST-003 mandates regression evaluation before model upgrades |
| R-004 | Sensitive HR content (e.g., compensation specifics tied to individuals, if present in source docs) exposed inappropriately | Low | High | NFR-SEC-005/FR-504 access classification hooks; Security/Compliance stakeholder review of actual source documents prior to ingestion |
| R-005 | Cost overrun from uncontrolled LLM/embedding usage at scale | Medium | Medium | NFR-COST-001 through 005 mandate tracking, budgets, and alerting |
| R-006 | Vector database or LLM provider outage causing full service unavailability | Low-Medium | High | NFR-REL-002/003 mandate graceful degradation and retry logic |
| R-007 | Chunking strategy misconfiguration degrading retrieval precision after a policy document format change | Medium | Medium | FR-407 configurability plus NFR-TEST-003 regression evaluation catches degradation before production rollout |
| R-008 | Prompt injection via crafted employee queries attempting to override system instructions | Low-Medium | Medium | NFR-SEC-003 mandates input treatment as untrusted; FR-1002 constrains LLM to context-grounded answering |
| R-009 | Scope creep toward chat-UI or write-back features during implementation, diluting focus on core RAG quality | Medium | Medium | Section 3.2 explicitly excludes these from v1.0; Engineering Manager to enforce scope boundary |

---

## 10. Acceptance Criteria

The Enterprise HR Policy Assistant v1.0 shall be considered accepted when all of the following are demonstrated:

**AC-001 — Ingestion correctness.** A representative batch of HR policy PDFs (including at least one multi-column layout, one table-containing document, and one scanned/image page) is ingested; ingestion results correctly reflect success, reduced-fidelity, or failure per document/page per FR-201–FR-206.

**AC-002 — Idempotent re-ingestion.** Re-ingesting an unchanged document produces no duplicate chunks or vectors (FR-104, FR-702, NFR-REL-004), verified by knowledge base entry count before/after.

**AC-003 — Grounded, cited answers.** For a labeled test set of at least 30 representative HR policy questions with known correct source locations, the system returns answers whose citations (FR-1201) correctly identify the source document/section/page for at least the target precision threshold agreed with QA (to be finalized as a measurable percentage during test plan derivation from this SRS).

**AC-004 — Refusal on missing information.** For a set of out-of-scope or unanswerable test questions (no relevant policy content exists), the system returns a "not found" response with no fabricated citation, in 100% of test cases (FR-805, FR-1106, FR-1205).

**AC-005 — Conversational continuity.** A scripted multi-turn conversation with at least one pronoun-dependent follow-up question is correctly resolved and answered using conversation history (FR-1301–FR-1306).

**AC-006 — Failure isolation.** Simulated failure of a single document during batch ingestion does not prevent successful ingestion of the remaining documents in the batch (FR-1404).

**AC-007 — Dependency outage handling.** Simulated unavailability of the LLM API, embedding API, and vector database (each independently) results in a clear, non-hanging, non-crashing error response in each case (NFR-REL-002).

**AC-008 — Configuration-driven behavior change.** At least three operational parameters (e.g., top-K, chunk size, LLM model) are changed via configuration alone and verified to take effect without code modification (FR-1601).

**AC-009 — Observability completeness.** For a sample query, the full request can be traced end-to-end across all pipeline stage logs using a single correlation ID, and all metrics listed in NFR-OBS-002 are populated.

**AC-010 — Performance targets met.** Measured p95 latency for non-streaming queries and p95 retrieval time meet or beat the targets in NFR-PERF-001 and NFR-PERF-003 under the defined nominal load test.

**AC-011 — No orchestration framework dependency.** A dependency audit confirms no LangChain (or equivalent orchestration framework) is present in the dependency manifest (C-001).

**AC-012 — Cost visibility.** Token usage and estimated cost per query are visible in logs/metrics for a sample of test queries (NFR-COST-001).

---

## 11. Future Enhancements

The following are explicitly deferred beyond v1.0 and are noted here to distinguish "deferred" from "rejected":

- **FE-001** — Web/chat user interface for direct employee interaction.
- **FE-002** — Role-based access control enforcing the document classification tag introduced in FR-504/NFR-SEC-005.
- **FE-003** — Multi-language source document support and query translation.
- **FE-004** — Support for additional source formats (DOCX, HTML, intranet wiki pages) per the extensibility hook in NFR-EXT-005.
- **FE-005** — Write-back integrations (e.g., initiating a leave request from within a conversation).
- **FE-006** — Automated policy-change detection and proactive notification to previously-asked users when a relevant policy is updated.
- **FE-007** — Feedback loop capturing user thumbs-up/down on answers to drive retrieval/prompt evaluation datasets (extends NFR-TEST-003).
- **FE-008** — Multi-tenant support for organizations with multiple HR policy sets (e.g., by subsidiary or region).
- **FE-009** — Advanced re-ranking model integration as a first-class, benchmarked component (builds on the pluggable hook in FR-804).

---

## 12. Glossary

| Term | Definition |
|---|---|
| RAG (Retrieval-Augmented Generation) | An architecture pattern in which an LLM's response is grounded by retrieving relevant content from an external knowledge source at query time, rather than relying solely on the model's parametric knowledge. |
| Chunk | A semantically coherent segment of a source document, sized for embedding and retrieval. |
| Embedding | A numeric vector representation of text that captures semantic meaning, used to perform similarity-based search. |
| Vector Database | A data store optimized for storing and querying high-dimensional embedding vectors via similarity search. |
| Semantic Retrieval | The process of finding content relevant to a query based on meaning (via embeddings) rather than exact keyword match. |
| Context Construction | The process of assembling retrieved chunks (and, where applicable, conversation history) into the input supplied to the LLM. |
| Citation | A structured reference back to the specific source document, section, and page that supports a claim made in a generated answer. |
| Grounding | Constraining an LLM's generated response to be based on supplied retrieved context rather than the model's general/background knowledge. |
| Hallucination | A generated statement presented as fact that is not supported by the supplied grounding context. |
| Top-K | The number of highest-ranked candidate chunks returned by a retrieval operation. |
| Orchestration Logic | The custom control-flow code that sequences pipeline stages (ingestion, retrieval, generation, etc.) — explicitly required to be hand-built rather than provided by a framework such as LangChain (see Constraint C-001/C-002). |
| SDD (Specification-Driven Development) | A development methodology in which a formally reviewed and approved specification precedes and governs all implementation work. |
| p95 / p99 Latency | The 95th/99th percentile of a latency distribution — the value below which 95%/99% of observed measurements fall; used to characterize tail latency rather than average-case performance. |
| Nominal Load | The expected typical (non-peak, non-degraded) operating request volume against which performance targets are defined. |
| Correlation ID | A unique identifier attached to a single request/query that allows all associated log entries across pipeline stages to be traced together. |

---

## Approval

This SRS requires sign-off from the following roles before implementation planning may begin (per Constraint C-008):

| Role | Name | Signature/Approval | Date |
|---|---|---|---|
| Solution Architect | | | |
| Engineering Manager | | | |
| QA Lead | | | |
| AI Engineer | | | |
| HR Policy Owner | | | |
| Security/Compliance Officer | | | |

*End of Document.*

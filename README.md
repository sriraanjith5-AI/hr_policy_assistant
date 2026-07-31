# Enterprise HR Policy Assistant

A production-grade Retrieval-Augmented Generation (RAG) system that lets employees ask natural-language questions about internal HR policy and receive accurate, citation-backed answers — built as a full Specification-Driven Development (SDD) project from requirements through architecture, interfaces, domain models, runtime sequences, testing strategy, deployment architecture, and an implementation-ready task roadmap, before a single line of application logic was written.

This repository is a demonstration of production-level AI engineering practice, not a chatbot demo: every architectural decision is documented, every component is traceable back to a requirement, and grounding/citation integrity is enforced structurally rather than asserted.

---

## Overview

Employees currently resolve HR policy questions by searching static documents or filing tickets with HR — slow for the employee and a source of repeated load on HR staff for questions the policy documents already answer. This system makes policy content queryable in natural language while preserving full traceability back to the source document, so every answer is either grounded and cited, or explicitly declined — never fabricated.

The system is built as a **custom-orchestrated RAG pipeline**, deliberately without a RAG orchestration framework, so that every step of the pipeline — retrieval, context assembly, prompt construction, generation, and citation resolution — is transparent, independently testable, and fully explainable.

## Goals

- Ground every substantive answer in retrieved, citable source content — never the model's parametric knowledge.
- Keep the system fully explainable and inspectable: every component has a defined contract, can be reasoned about independently, and can be replaced without a redesign.
- Avoid vendor and framework lock-in at every external boundary — embeddings, vector storage, and LLM generation are each independently swappable.
- Keep transport (how a request reaches the system) fully decoupled from the RAG logic itself.
- Make the system's own hallucination-risk posture honest and measurable, rather than asserted: structural controls reduce risk, evaluation quantifies what remains.

## Key Architectural Principles

- **Custom RAG orchestration.** No LangChain, LlamaIndex, or equivalent orchestration framework — a purpose-built orchestrator sequences pipeline stages under full team control ([ADR-001](app/specs/decisions/ADR-001-custom-orchestration.md)).
- **Provider abstraction.** The only three points where a vendor SDK is ever touched — embeddings, vector storage, and LLM access — sit behind narrow interfaces. Nothing else in the system calls a vendor SDK directly ([ADR-002](app/specs/decisions/ADR-002-provider-abstraction-boundary.md)).
- **Dependency inversion.** Every dependency in the system points at an interface, never a concrete implementation — the mechanism that makes provider swaps, stage-level unit testing, and cloud portability possible without a rewrite.
- **Stage-based pipeline architecture.** Every functional responsibility — parsing, chunking, retrieval, prompt assembly, generation, citation mapping — is an independently addressable, independently testable component, never steps folded into one large function.
- **Retrieval-grounded generation.** The LLM is only ever invoked with retrieved context attached, and is instructed to answer only from that context. An empty retrieval, or an LLM's own admission that the context is insufficient, is routed to an explicit "not found" response — never silently answered anyway.
- **Citation traceability.** Citation metadata has a single source of truth, established at ingestion time, and is carried unmodified through to the final answer — never re-derived or guessed at query time.
- **Structural, not asserted, grounding.** The architecture minimizes unsupported answers through controlled retrieval, context validation, and citation traceability — it reduces hallucination risk structurally rather than relying on prompt instructions alone, and never claims to eliminate it. Evaluation exists specifically to measure the residual risk, not to guarantee it away.

## Specification-Driven Development (SDD) Workflow

This project follows Specification-Driven Development: the specification is the source of truth, and implementation proceeds only after the full specification chain is reviewed and approved. No implementation code, class design, or folder structure was finalized ahead of the corresponding specification.

```
requirements.md → rag_design.md → architecture.md → interfaces.md → domain_models.md →
sequence_diagrams.md → testing.md → deployment.md → tasks.md → implementation
                                          │
                                          ├──► evaluation/benchmark_spec.md
                                          └──► evaluation/metrics_dictionary.md
                                          │
                                          └──► decisions/ADR-001 … ADR-005
```

| Document | What It Defines |
|---|---|
| `requirements.md` | Functional and non-functional requirements (FR/NFR), constraints, acceptance criteria — the SRS |
| `rag_design.md` | Custom RAG pipeline design: retrieval strategy, citation generation, evaluation approach |
| `architecture.md` | System-level architecture: layering, component ownership, deployment views, ADR candidates |
| `interfaces.md` | Contracts between orchestrators, pipeline stages, and provider interfaces |
| `domain_models.md` | The shared business objects every component exchanges, and the runtime invariants that must always hold |
| `sequence_diagrams.md` | Timed, ordered runtime collaboration diagrams for every major flow (grounded answer, declined answer, ingestion, failure handling, conversation, evaluation) |
| `testing.md` | The full testing pyramid — unit, contract, component, integration, evaluation, resilience, performance, regression, acceptance — traced back to requirements |
| `deployment.md` | Runtime topology, configuration/secret strategy, operational readiness, scaling, resilience, backup/recovery |
| `tasks.md` | The implementation roadmap — every task traced to a requirement, contract, domain model, sequence, test, and operational requirement |
| `evaluation/benchmark_spec.md` | Golden question schema, scoring methodology, and governance for RAG quality evaluation |
| `evaluation/metrics_dictionary.md` | The single authoritative definition, formula, and owner for every metric used anywhere in this project |
| `decisions/ADR-*.md` | Architecture Decision Records — the specific technical decisions and the ones deliberately left open |

## Repository Structure

```
entreprise-rag/
├── app/
│   ├── chunking/          # Semantic chunking stage
│   ├── config/             # Configuration management (planned)
│   ├── embeddings/         # Embedding generation stage
│   ├── llm/                 # LLM provider integration (planned)
│   ├── loaders/             # Document loading / PDF parsing
│   ├── prompts/            # Prompt templates (planned)
│   ├── retrieval/           # Retrieval stage (planned)
│   ├── skills/               # (reserved)
│   ├── utils/                # Shared utilities
│   ├── vectorstore/         # Vector store integration (planned)
│   ├── specs/                # The full SDD specification suite
│   │   ├── requirements.md
│   │   ├── rag_design.md
│   │   ├── architecture.md
│   │   ├── interfaces.md
│   │   ├── domain_models.md
│   │   ├── sequence_diagrams.md
│   │   ├── testing.md
│   │   ├── deployment.md
│   │   ├── tasks.md
│   │   ├── evaluation/
│   │   │   ├── benchmark_spec.md
│   │   │   └── metrics_dictionary.md
│   │   └── decisions/
│   │       ├── ADR-001-custom-orchestration.md
│   │       ├── ADR-002-provider-abstraction-boundary.md
│   │       ├── ADR-003-vector-database-selection.md
│   │       ├── ADR-004-embedding-model-selection.md
│   │       └── ADR-005-llm-provider-selection.md
│   └── requirements.txt
├── data/                    # Sample/test documents (see data/README.md)
├── tests/                   # Test suite (planned, per testing.md)
├── main.py
└── main_test.py
```

## Current Project Status

**Architecture and specifications are complete. Implementation is about to begin.**

The full nine-document SDD chain — from `requirements.md` through `tasks.md` — has been written, internally cross-referenced, and iteratively reviewed for consistency across every document. Every pipeline stage, orchestrator, and provider interface has a defined contract; every runtime flow has a corresponding sequence diagram; every test category is mapped to the specification it validates; every operational concern has a named owner. Some early scaffolding code exists under `app/` (loaders, chunking, embeddings, utils) as exploratory groundwork, but the system as specified has not yet been implemented against the finalized interfaces and domain models.

Three technology decisions — vector database, embedding model, and LLM provider — are **deliberately left open** ([ADR-003](app/specs/decisions/ADR-003-vector-database-selection.md), [ADR-004](app/specs/decisions/ADR-004-embedding-model-selection.md), [ADR-005](app/specs/decisions/ADR-005-llm-provider-selection.md)), each with evaluation criteria defined but no candidate selected. This is possible without blocking implementation because the Provider Interface abstraction (ADR-002) lets every other component be built and tested against a stubbed provider first.

## Technology Philosophy

- **Technology-neutral by design.** The specification suite intentionally avoids naming a vector database, embedding model, or LLM provider anywhere except as an open decision — see `app/specs/decisions/`.
- **Framework-independent core.** No RAG orchestration framework is used or planned. FastAPI is the confirmed future transport layer and Docker the confirmed packaging format, but neither dominates the architecture — the core pipeline logic has no dependency on either.
- **Cloud-portable.** No proprietary, single-cloud-only service is required for any core capability — a direct consequence of the provider abstraction boundary, not a separate constraint bolted on afterward.
- **Provider swap without a rewrite.** Because every external dependency sits behind an interface, changing the vector database, embedding model, or LLM provider is a Provider Implementation change and a re-run of the Evaluation suite — never a Pipeline Stage or Orchestrator change.

## Planned Implementation Roadmap

Implementation follows `app/specs/tasks.md`, organized into the same phases `rag_design.md` already scoped:

1. **Phase 1 — Core RAG MVP.** Domain models, provider contracts, all fifteen pipeline stages, both orchestrators — enough to answer a grounded question and correctly decline an ungrounded one, end to end, via direct invocation.
2. **Phase 2 — Engineering Hardening.** Concrete provider implementations (once ADR-003/004/005 resolve), configuration and secret management, structured logging/error handling, the evaluation harness, regression test automation.
3. **Phase 3 — Production Readiness.** The FastAPI application layer, Docker packaging, health checks, externalized session storage, metrics, backup/recovery automation.
4. **Phase 4 — Agentic Extension.** Explicitly **not planned** in the current roadmap — noted only so the boundary is deliberate, not accidental (`rag_design.md` §10, `tasks.md` §7).

Every task in `tasks.md` cites the specific requirement, interface contract, domain model, sequence diagram, and test case it implements — there is no unscoped or untraced implementation work in this project.

## Future Enhancements

Beyond Phase 3, tracked as deliberately deferred (not forgotten) in `requirements.md` and `architecture.md`:

- Role-based access control enforcing the document classification tag already modeled in the domain layer.
- Multi-language source document support.
- A feedback loop capturing answer quality signals to grow the evaluation dataset.
- Multi-tenant support for organizations with multiple HR policy sets.
- Agentic capabilities — employee-context-aware reasoning, HR system integrations, tool-based decision support (Phase 4).

## License

No license has been selected yet. All rights reserved by the author pending a license decision. This section will be updated once a license is chosen.

---

*This project was built end-to-end using Specification-Driven Development — every document in `app/specs/` was reviewed, refined, and cross-validated against every other document before implementation began.*

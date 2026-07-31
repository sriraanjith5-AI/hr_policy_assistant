# Coding Standards

## Enterprise HR Policy Assistant — Lightweight Python Implementation Standards

## 1. Document Control

| Field | Value |
|---|---|
| Document Type | Coding Standards |
| Project Name | Enterprise HR Policy Assistant |
| Version | 1.0 |
| Status | Draft — Pending Review |
| References | [ARCHITECTURE_GUIDELINES.md](./ARCHITECTURE_GUIDELINES.md), [interfaces.md](./interfaces.md) (v1.1), [domain_models.md](./domain_models.md) (v1.3), [testing.md](./testing.md) (v1.0) |
| Prepared By | Principal AI Solution Architect |
| Date | 2026-07-31 |

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-07-31 | Initial Coding Standards |

## 2. Purpose

This document is a lightweight, standard-library-only set of Python implementation conventions. It assumes no framework, no dependency-injection container, and no ORM — consistent with ADR-001 and ADR-002's rejection of orchestration/agent frameworks and this project's "stdlib unless already approved" discipline (`requirements.md` C-003). It contains **no runnable application code** — every example below is a minimal, illustrative shape (a signature, a skeleton, an import block), never business logic. Where a recommendation is not already mandated by an upstream specification, it is explicitly marked **Open Recommendation** rather than presented as a rule.

## 3. Python Version Policy

**Open Recommendation.** No upstream specification pins a Python version. As a practical floor: several conventions recommended below (`dataclasses`, `typing.Protocol`) require Python 3.8 or later to use without an additional dependency. A currently-supported Python 3 release is assumed; the exact minor version is not yet decided and should be pinned once the runtime environment (`deployment.md`) is finalized.

## 4. Repository Layout

Not restated here — see `ARCHITECTURE_GUIDELINES.md` §5 for the authoritative folder-to-layer mapping. This document only adds naming conventions within that already-frozen layout.

## 5. Package Naming

Every package name is `snake_case` and matches the architectural layer it implements exactly: `core`, `domain`, `providers`, `orchestrators`, `pipeline`, `utils` (already established in Sprint 1). A new subpackage follows the same rule — e.g., `pipeline/ingestion/`, `pipeline/query/`.

## 6. Module Naming

One module (`.py` file) implements one class, in the common case of a Pipeline Stage, Orchestrator, or Provider Implementation. The module name is the `snake_case` form of the class it contains.

## 7. File Naming

Pattern: `<component_name_snake_case>.py`. Example: a Provider Implementation for a technology `X` implementing capability `Y` follows `<x>_<y>_provider.py` (see §10).

## 8. Class Naming

`PascalCase`, and — for any class implementing an `interfaces.md` §4 stage or §5 provider — the class name matches the component name used in `interfaces.md` **verbatim**. No invented suffixes (no `Impl`, no `Manager` unless `interfaces.md` itself uses that word). This keeps a stage name grep-able identically across specification and code.

## 9. Interface Naming

Pattern: `<Capability>ProviderInterface` — e.g., `EmbeddingProviderInterface`, `VectorStoreProviderInterface`, `LLMProviderInterface`, matching the three interfaces ADR-002 and `interfaces.md` §5 define. No additional Provider Interfaces exist without an `interfaces.md` update first (`ARCHITECTURE_GUIDELINES.md` §19).

## 10. Provider Implementation Naming

Pattern: `<Technology><Capability>Provider` — e.g., a hypothetical `SomeVectorDatabaseProvider` implementing `VectorStoreProviderInterface`. The technology name only appears at this layer, never above it (`ARCHITECTURE_GUIDELINES.md` §10).

## 11. Function Naming

`snake_case`, verb-first for anything that performs an action (`embed_text`, `resolve_session`, `build_context`). A function or method that only returns a value without side effects may be a plain noun phrase (`retrieved_chunks`) if used as a property.

## 12. Method Design

One clear responsibility per method, matching the Single Responsibility principle already applied at the stage level (`architecture.md` §11). A method's parameters and return type are expressed in domain-model types wherever a domain model exists for that concept — passing a raw `dict` or bare string where `domain_models.md` already defines a model for that concept (a citation, a chunk, a query context) is a form of the "primitive obsession" anti-pattern (§26) and defeats the purpose of having a Domain Model Layer at all.

## 13. Constructor Injection

Every dependency a class needs (a Provider Interface instance, a resolved configuration value, a logger) is passed into `__init__` — a class never instantiates its own dependency internally. Illustrative shape, not runnable logic:

```python
class Retriever:
    def __init__(self, vector_store: VectorStoreProviderInterface, top_k: int) -> None:
        self._vector_store = vector_store
        self._top_k = top_k
```

## 14. Dependency Injection Rules

No dependency-injection framework or container is used (consistent with ADR-001's rejection of framework machinery). All wiring is plain constructor injection, assembled at one composition point. **Open Recommendation**: the exact location of that composition point (e.g., an application entry-point module) is not yet decided.

## 15. Configuration Access

A component receives already-resolved configuration **values** through its constructor — never a raw configuration object, file handle, or `os.environ` reference. Only the module inside `core/config/` reads environment variables or configuration files directly (`ARCHITECTURE_GUIDELINES.md` §14).

## 16. Logging Conventions

A component obtains its logger from one shared access point in `core/logging/` — never `logging.getLogger(__name__)` called ad hoc per module, and never `print()`. **Open Recommendation**: whether that access point is a factory function, a constructor-injected logger instance, or another mechanism is not yet decided. Whichever mechanism is chosen, it must produce the fields `ARCHITECTURE_GUIDELINES.md` §15 requires.

## 17. Exception Conventions

Pattern: `<Category>Error`, matching `interfaces.md` §7's taxonomy exactly — `ValidationError`, `ParsingError`, `EmbeddingError`, `RetrievalError`, `LLMError`, `CitationValidationError`, `ConfigurationError` — every one inheriting a single shared base defined once in `core/exceptions/`. Illustrative shape only:

```python
class ApplicationError(Exception):
    """Base for every exception in the shared taxonomy."""

class RetrievalError(ApplicationError):
    """Vector store / retrieval failure category (interfaces.md Section 7)."""
```

## 18. Type Hint Policy

Every public function and method signature — parameters and return type — carries a type hint, using domain-model types wherever applicable (§12). This costs nothing (standard-library `typing`) and makes the domain-model-typed contracts in `interfaces.md` mechanically checkable rather than only documented. **Open Recommendation**: whether a static type checker is added to the review/CI process is a separate tooling decision, not addressed here.

## 19. Dataclass Usage

**Open Recommendation.** No specification mandates a specific Python representation for domain models — `domain_models.md` deliberately stops at conceptual definitions. The standard-library `dataclasses` module is recommended as the default representation for domain models: it adds no dependency beyond the standard library, and it naturally expresses a domain model as plain, provider-independent, framework-independent data (`domain_models.md` §2). A third-party validation library (e.g., a schema-validation package) was considered and is not recommended at this stage — it would add a dependency outside the four already permitted by `requirements.md` C-003 for no requirement currently justifying it. Illustrative shape only:

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Citation:
    source_document_id: str
    page_number: int
    excerpt: str
```

## 20. Protocol vs. ABC Guidance

**Open Recommendation.** No specification mandates how a Provider Interface is expressed in Python. `typing.Protocol` (structural typing) is recommended over `abc.ABC` (nominal typing) for Provider Interfaces specifically, because a Provider Interface is a contract about *shape*, not about a shared class hierarchy — a Provider Implementation satisfies it by matching the method signatures, with no explicit inheritance required. `abc.ABC` remains a reasonable alternative if the team prefers explicit nominal typing with runtime `isinstance` enforcement; either choice is compatible with ADR-002 and neither is frozen by this document. Illustrative shape only (no method bodies — a contract, not logic):

```python
from typing import Protocol

class EmbeddingProviderInterface(Protocol):
    def embed(self, text: str) -> "Embedding":
        ...
```

## 21. Docstring Style

Every public class and function carries at minimum a one-line summary docstring. Google-style docstrings are recommended for anything needing more than one line (Args/Returns/Raises sections), for consistency and readability, without requiring additional tooling to enforce.

## 22. Import Ordering

Three groups, separated by a blank line, each alphabetized within itself: (1) standard-library imports, (2) permitted third-party imports (only ever present in a Provider Implementation module or the PDF Parser stage module — `ARCHITECTURE_GUIDELINES.md` §18), (3) local application imports. This ordering makes a boundary violation visually obvious: a third-party import inside a Pipeline Stage module stands out immediately because group (2) should be empty there.

## 23. Circular Dependency Avoidance

Because the dependency direction is strictly one-way (`ARCHITECTURE_GUIDELINES.md` §7), a circular import is never a Python packaging inconvenience to route around with a local import or a lazy import trick — it is a signal that a boundary has been violated, or that a shared abstraction two modules both need is missing from `domain/` or `core/` and should be extracted there instead.

## 24. Testing Conventions

Test module layout mirrors implementation module layout, one test module per implementation module, under `tests/<category>/`, using the nine categories `testing.md` §3 already defines (unit, contract, component, integration, evaluation, resilience, performance, regression, acceptance). `tests/__init__.py` already documents this expansion as pending — creating the nine subpackages is a Sprint 2 task, not part of this document's scope.

## 25. Code Review Checklist

- [ ] Does every class/interface/provider name match its `interfaces.md` vocabulary verbatim (§8–§10)?
- [ ] Does every public signature carry type hints, expressed in domain-model types where one exists (§12, §18)?
- [ ] Is every dependency constructor-injected, with no class instantiating its own dependency (§13)?
- [ ] Does any raised exception fall outside the shared `<Category>Error` taxonomy (§17)?
- [ ] Is there a raw `os.environ` read or file open outside `core/config/` (§15)?
- [ ] Is there a `print()` or ad hoc `getLogger()` call outside the shared logging access point (§16)?
- [ ] Does every public class/function have at least a one-line docstring (§21)?

## 26. Common Anti-patterns

| Anti-pattern | Rule Violated |
|---|---|
| A Pipeline Stage instantiates a Provider Implementation directly instead of receiving a Provider Interface via constructor injection | §13; `ARCHITECTURE_GUIDELINES.md` §9 |
| A broad `except Exception:` swallows a failure instead of raising/propagating a shared-taxonomy exception | §17; `ARCHITECTURE_GUIDELINES.md` §16 |
| A stage returns a raw `dict` or string instead of the domain model `interfaces.md` specifies for that stage's output | §12; `ARCHITECTURE_GUIDELINES.md` §13 |
| An Orchestrator contains a conditional that inspects a domain model's content (e.g., an embedding's values) rather than routing on an already-reported outcome | `ARCHITECTURE_GUIDELINES.md` §11 |
| A Pipeline Stage reads `os.environ` directly instead of receiving a resolved value via its constructor | §15 |
| A Provider Implementation imports from `pipeline/` or `orchestrators/` | `ARCHITECTURE_GUIDELINES.md` §9 |
| An empty retrieval result, an LLM decline, a truncated context, or an unresolved citation is raised or logged as an error | `ARCHITECTURE_GUIDELINES.md` §16 |

## 27. Future Extension Guidance

Adding a new provider technology behind an already-existing Provider Interface requires exactly one new file in `providers/implementations/` and zero changes anywhere else — this is the payoff of ADR-002's boundary, and any change that requires touching a Pipeline Stage or Orchestrator to swap a provider technology indicates the boundary was not respected somewhere. Adding a new Pipeline Stage or Provider Interface entirely is a specification change first (`ARCHITECTURE_GUIDELINES.md` §19), an implementation change second.

---

*End of Document.*

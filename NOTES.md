
# Engineering Intelligence Platform (EIP)

## Engineering Notes and Design Decisions

Version: 0.1.1

Assignment: Loop Senior AI/ML Engineer Take-Home

---

## 1. Objective

The objective was to build an engineering intelligence service
that provides deterministic collaboration analytics and
evidence-grounded AI interpretations using GitHub data.

The primary design principle is that analytical correctness
should not depend on the language model.

The system separates metric computation, analytical context,
reasoning, validation, evaluation and presentation into
independently understandable components.

The implementation also includes a lightweight application
interface, conversational intelligence, persistent execution
history and containerized deployment.

## 2. Setup and Execution

The recommended reviewer execution path is a token-free
Docker Compose demonstration environment.

The default deployment automatically provisions local Ollama
inference and restores a bundled historical GitHub snapshot.

Optional Live Mode supports authenticated ingestion through
three independently executable stages:

1. GitHub Bronze ingestion.
2. Silver standardization.
3. Gold analytical transformations.

A read-only GitHub token is required only for source ingestion.

Demo and Live Mode use isolated persistent database volumes.
An optional Docker Desktop configuration supports native
Ollama inference.

The README provides deployment instructions, configuration
options, API examples and testing commands.

## 3. Architectural Decisions

### 3.1 Separation of analytical and AI workloads

The deterministic analytical layer is responsible for
computing engineering metrics.

The AI layer consumes analytical context rather than acting
as the authoritative source of numerical results.

This separation enables:

- Reproducible analytical results.
- Independent testing of metric computation.
- Reduced numerical hallucination risk.
- Evidence traceability.
- Model-independent analytical capabilities.

The language model is used for interpretation, explanation
and synthesis rather than unrestricted metric generation.

### 3.2 Domain-oriented repository organization

The backend is separated into data engineering, analytics,
AI intelligence and API domains.

The frontend is organized around application capabilities,
including analytical reporting, AI insights, history and Copilot.

This organization keeps source ingestion, analytical logic,
model orchestration and application presentation separated.

Additional data sources, metrics and model providers can
be introduced without redesigning the complete application.

### 3.3 Medallion data architecture

A Bronze, Silver and Gold architecture was selected to
separate source observations from analytical consumption.

Bronze preserves original source observations and ingestion
metadata.

Silver standardizes and validates source records for
consistent analytical use.

Gold provides PR lifecycle facts and period-level analytical
facts.

Although this architecture introduces additional
implementation complexity for a small service, it provides
clear boundaries for data quality, traceability and
future source expansion.

### 3.4 SQLite persistence

SQLite was selected because the assignment prioritizes a
small, reproducible, locally executable service.

It avoids requiring a separately managed database service
and supports transactional persistence.

The database infrastructure includes:

- Version-controlled SQL definitions.
- Explicit schema deployment transactions.
- Foreign-key enforcement.
- Automatic transaction commit and rollback.
- Write-ahead logging for concurrent reads.
- Persistent source and intelligence records.

SQLite is appropriate for the local evaluation workload.
A larger multi-user deployment would require reassessment
of database concurrency and operational requirements.

## 4. Source Ingestion and Data Quality

The initial source is the GitHub REST API.

The ingestion pipeline retrieves:

- Repository metadata.
- Historical pull request observations.
- Pull request details.
- Pull request reviews.

Historical source extraction and detailed enrichment are
bounded by configurable reporting windows.

The ingestion process validates repository identity,
public repository status, identifiers and PR timestamp
integrity.

Raw observations are retained in Bronze, including records
that may not qualify for subsequent analytical processing.

The latest valid PR observation is selected for enrichment.

PR detail and review records are persisted together after
review pagination has completed.

A completed enrichment batch can therefore distinguish a
valid empty review response from incomplete review retrieval.

### 4.1 API rate limits and source coverage

Source extraction is governed by configurable limits for
pagination, API requests and minimum quota reserves.

Historical boundary detection is treated as an estimation
heuristic rather than proof of exhaustive source coverage.

The pipeline records source coverage separately from
execution status.

An ingestion execution can succeed while source coverage
remains estimated or partial.

This distinction is important because missing source
observations should not automatically be interpreted as
zero engineering activity.

### 4.2 Reporting boundaries

Reporting periods are represented using UTC date boundaries
with an exclusive end date.

Consistent period boundaries reduce ambiguity in metric
calculation and period comparison.

The analytical results remain dependent on the available
source and enrichment coverage.

## 5. Deterministic Engineering Analytics

The deterministic HTTP endpoint provides engineering
collaboration insights for a selected reporting period.

The analytical layer is backed by standardized lifecycle
records and period-level Gold facts.

Metric definitions are maintained separately from source
ingestion through a version-controlled metric registry.

This provides a consistent foundation for application
reporting and AI reasoning.

Deterministic analytical requests do not require a
language model.

The service distinguishes unavailable analytical data
from invalid reporting-period requests through appropriate
HTTP error responses.

## 6. AI Intelligence Architecture

### 6.1 Analytical context

The AI intelligence workflow operates on analytical
context derived from the deterministic data layer.

The context provides the factual basis for interpreting
engineering performance and identifying meaningful signals.

The intelligence layer is responsible for reasoning,
not for replacing the underlying metric calculations.

### 6.2 Narrative generation and hypotheses

The report workflow identifies analytical signals and
constructs engineering intelligence around available evidence.

Hypotheses represent possible explanations for observed
engineering behavior rather than established causal facts.

A hypothesis should be supported by relevant evidence and
should remain distinguishable from directly measured
observations.

For example, a change in review latency alongside a change
in merge performance may support investigation of review
bottlenecks, but does not establish causation.

### 6.3 Numerical grounding

Numerical grounding constrains AI-generated responses to
available analytical evidence.

The numerical validation layer checks generated numerical
claims against their supporting context.

This reduces the risk of fabricated metrics, unsupported
comparisons and incorrectly interpreted numerical values.

Numerical correctness is necessary but is not sufficient
to establish that an interpretation is meaningful.

### 6.4 Evidence validation

The evidence validation layer evaluates whether generated
claims are supported by the available analytical context.

Evidence chains are intended to connect interpretations
with the underlying analytical observations.

Unsupported claims should not be presented as established
engineering facts.

### 6.5 Evaluation and confidence

Evaluation scores and confidence scores represent different
concepts.

An evaluation or deterministic validation score indicates
how an output performs against the applicable validation
or evaluation criteria.

A confidence score expresses the strength of the
interpretation based on the available supporting evidence.

A deterministic validation score of 100 does not imply
that a narrative hypothesis has 100 percent confidence.

These concepts are displayed separately in the application.

The confidence score is not presented as a statistically
calibrated probability.

### 6.6 Local language model inference

Ollama was selected to provide locally hosted inference
without requiring a commercial LLM API subscription.

The configured default model is Qwen 3 4B Instruct
(`qwen3:4b-instruct`). Alternative Ollama models remain
configurable through the local environment.

The default was selected based on observed local execution
behavior and a smaller model download footprint, not a
statistically validated model quality comparison.

Local inference provides control over model configuration
and reduces external data transmission.

Trade-offs include model availability, hardware requirements,
inference latency and differences in reasoning quality
across model configurations.

## 7. Engineering Copilot

The Copilot extends the intelligence service with
conversational analytical exploration.

Its supporting architecture includes:

- Intent routing.
- Conversation context.
- Query planning.
- Metric query compilation.
- Analytical tool execution.
- Deterministic factual answers.
- Grounded AI reasoning.
- Response validation.

Simple conversations and supported factual questions can
be handled without unnecessary model inference.

Questions requiring interpretation can use the AI
intelligence workflow and supporting analytical evidence.

The intent is to provide an analytical assistant rather
than an unrestricted chatbot disconnected from the
engineering data platform.

## 8. Persistence, Caching and Auditability

GitHub observations and analytical facts are persisted
locally in SQLite.

Intelligence execution history preserves generated outputs
and associated execution information.

The narrative retrieval endpoint is separated from
the generation endpoint.

Retrieving existing approved intelligence does not
automatically invoke the model.

Previously generated intelligence may be reused when
the applicable cache and analytical context conditions
are satisfied.

This reduces repeated inference and supports consistent
report retrieval.

The history interface provides visibility into historical
intelligence executions and their evaluation details.

Historical execution snapshots support investigation
of generated intelligence.

## 9. Security

The application is designed to operate with read-only
GitHub credentials against public repositories.

Credentials are configured locally through environment
configuration and are excluded from Git and Docker build
contexts.

The backend validates source repository identity and
public repository status.

SQL values are parameterized, while dynamically selected
ingestion tables are restricted to an internal allowlist.

Ingestion error reporting records exception categories
without intentionally exposing request credentials,
headers or raw source content.

The application ports are bound to localhost in the
provided Docker Compose configuration.

The local inference architecture avoids transmitting
analytical context to a hosted commercial LLM API.

The implementation does not constitute a fully hardened
multi-tenant production service.

Additional production security requirements would include
authentication, authorization, secret management, request
limits and deployment-specific network controls.

## 10. Reliability and Testing

The automated backend test suite covers areas including:

- Data engineering and analytical behavior.
- API contracts.
- Intelligence context and cache compatibility.
- Intent routing.
- Query planning and compilation.
- Deterministic factual answers.
- Numerical grounding and validation.
- Report hypotheses and generation policies.
- Intelligence history and persistence.
- Default model configuration and overrides.
- Historical intelligence bootstrap and period discovery.
- Bootstrap cache reuse, rejection and HTTP error handling.

At the latest validated development checkpoint:

- 336 automated backend tests passed.
- Ruff lint checks passed.
- Frontend lint returned zero errors and warnings.
- TypeScript and production frontend build succeeded.
- Docker backend and frontend reported healthy status.
- Cached narrative API retrieval was verified.

These checks establish implementation confidence but
do not replace end-to-end acceptance testing or
statistical evaluation of model-generated intelligence.

## 11. Trade-offs and Known Limitations

| Decision | Benefit | Limitation |
|---|---|---|
| SQLite | Simple local persistence | Limited write scalability |
| Medallion architecture | Traceability and clear data boundaries | Additional implementation complexity |
| Bounded ingestion | Controlled API consumption | Historical coverage may be incomplete |
| Local LLM | Privacy and independence from commercial APIs | Hardware and latency constraints |
| Deterministic analytics | Reproducible numerical results | Requires maintained metric definitions |
| Governed reasoning | Reduced unsupported claims | Cannot eliminate all interpretation errors |
| Intelligence caching | Reduced repeated inference | Requires careful context compatibility |
| Local deployment | Reproducible evaluation environment | Not a multi-tenant production service |

Additional known considerations:

- GitHub collaboration signals are proxies for engineering
  behavior and should not be treated as complete measures
  of individual productivity.

- Repository activity alone cannot establish the causal
  explanation behind every observed engineering pattern.

- Review and detail enrichment may have narrower coverage
  than basic pull request history.

- Local inference latency varies by hardware and model.

- Confidence scores are not statistically calibrated.

- Python dependencies are not fully locked to exact
  versions in the current project configuration.

- The frontend production build reports a bundle-size
  optimization warning.

- The backend test environment reports a non-blocking
  Starlette HTTP client deprecation warning.

## 12. What I Would Do With Another Day

The next development iteration would prioritize
reliability and measurable intelligence quality rather
than adding unrelated application features.

### Priority 1: Intelligence evaluation benchmark

Build a curated dataset of engineering questions,
analytical evidence and expected factual outcomes.

Measure numerical accuracy, evidence support,
unsupported claim frequency and hypothesis quality
across model configurations.

### Priority 2: Operational resilience

Introduce more robust incremental synchronization,
interrupted-ingestion recovery and explicit freshness
monitoring.

Improve source coverage communication and cache
invalidation observability.

### Priority 3: Reproducibility and acceptance testing

Expand automated fresh-install validation and end-to-end
application testing around the bundled demonstration dataset.

Introduce fully locked backend dependencies and
document model resource requirements.

### Priority 4: Production readiness

Introduce authentication, authorization,
distributed execution controls, structured operational
telemetry and production-grade secret management.

Evaluate whether the persistence layer should move
to PostgreSQL as concurrency requirements increase.

## 13. AI Assistance Disclosure

AI-assisted development tools, including ChatGPT,
were used during the implementation.

AI assistance supported:

- Architecture exploration and design discussions.
- Implementation and code refinement.
- Test development and edge-case analysis.
- Debugging and troubleshooting.
- Prompt and intelligence workflow refinement.
- Documentation preparation.

Generated suggestions were incorporated through an
iterative development process involving local execution,
code refinement and automated validation.

The architecture, implementation decisions and resulting
submission remain the responsibility of the author.

## 14. Conclusion

EIP demonstrates an approach to engineering intelligence
in which deterministic analytics, governed AI reasoning
and persistent evidence are treated as complementary
components.

The objective is not simply to generate engineering
narratives, but to make their factual foundations,
interpretations and limitations inspectable.

## Governed LLM Interpretation and Evaluation

Narrative generation uses a hybrid intelligence architecture:

- The LLM selects a meaningful analytical observation.
- The application renders numerical statements from authoritative Gold facts.
- When comparable enrichment evidence is available, the LLM may generate
  qualitative hypotheses, alternative explanations and recommended investigations.
- When enrichment comparisons are unavailable, the report is restricted
  to factual observations.
- A supported deterministic hypothesis may be used when appropriate.
- Model-authored interpretations undergo numerical grounding, evidence
  validation and a separate LLM evaluation invocation.
- Approved intelligence is persisted and reused through a compatible cache.

### Live Validation

The Apache Airflow reporting period from November 20 to November 27,
2026 (exclusive), successfully demonstrated:

- Generator: qwen3:4b-instruct
- Generator prompt version: 1.9.0
- Generation latency: 17.043 seconds
- Evaluation latency: 18.15 seconds
- Approval status: AUTO_APPROVED
- Evaluation score: 100/100
- Hypothesis confidence: 60/100
- Numerical grounding: passed
- Persistent cache reuse: passed

### Evaluation Limitations

The generator and evaluator currently use the same model through separate
invocations, which may result in correlated errors.

An evaluation score is not proof of analytical correctness. Hypothesis
confidence is an evidence-based heuristic rather than a calibrated probability.

The live validation also identified an opportunity to improve counter-evidence
selection and distinguish directly supported interpretations from plausible
but unverified explanations. Code change size must not be treated as a direct
measure of technical complexity.


## Fresh-Clone Acceptance Validation

An isolated clone of the public repository was deployed
using a separate Docker Compose project, local database
and application ports. The existing host Ollama runtime
and read-only GitHub credential were reused.

Apache Airflow data was ingested into an initially empty
analytical database on November 27, 2026.

| Validation | Observed result |
|---|---|
| Bronze source records | 8,790 |
| Bronze PR observations | 5,000 |
| Valid Silver pull requests | 4,999 |
| Invalid PR observations excluded | 1 |
| Enriched merged pull requests | 714 |
| Review records | 3,075 |
| Gold lifecycle records | 4,999 |
| Registered metrics | 14 |
| Materialized reporting periods | 3 |
| Gold period facts | 42 |
| SQLite integrity | Passed |
| Deterministic analytics endpoint | Passed |
| Persistent intelligence cache | Passed |
| Persistence across backend restart | Passed |
| Backend regression suite | 328 passed |
| Source coverage | ESTIMATED |

The ingestion attempted 1,481 GitHub API requests.
Historical coverage remains estimated rather than
confirmed exhaustive.

### Historical Intelligence Bootstrap

Historical AI intelligence is initially empty in a fresh
installation.

The optional bootstrap utility discovers supported
reporting periods through the analytical API and invokes
the existing narrative endpoint chronologically.

It preserves all numerical grounding, evidence validation,
evaluation and persistence policies.

The live bootstrap processed three reporting periods:

| Reporting period (exclusive end) | Outcome |
|---|---|
| November 6 to November 13 | Newly approved |
| November 13 to November 20 | Newly approved |
| November 20 to November 27 | Existing approved cache reused |

Subsequent forced generation for the latest period
retrieved both earlier eligible intelligence records.

Existing cached narratives are not automatically regenerated
when additional historical intelligence becomes available.
Explicit forced generation is required when refreshed
historical context is needed.

Historical context retrieval does not establish that the
model meaningfully synthesizes every retrieved observation.

### Observed Model Evaluation Behavior

Two local model configurations were exercised against
the same analytical reporting period.

- Qwen 2.5 7B generated a numerically valid candidate
  that was rejected after semantic evaluation identified
  an insufficiently supported interpretation.
- Qwen 3 4B Instruct generated an approved candidate
  with an evaluation score of 100 and confidence of 60.

Manual inspection identified incomplete counter-evidence
selection, imprecise statistical terminology, speculative
explanations and occasional mixed-language output.

A hypothesis concerning larger code changes was approved
despite a decline in median lines changed.

Automated approval is not equivalent to independently
verified analytical correctness. Separate model evaluation
cannot eliminate correlated reasoning errors.

A curated evaluation benchmark, stronger counter-evidence
checks, language consistency validation and improved cache
freshness policies remain future development priorities.

### Execution Trade-off

Ingestion and transformation stages execute sequentially
through documented commands. Historical AI generation
is available as a separate optional utility.

Recurring scheduling and distributed workflow orchestration
are outside the current local evaluation scope.

## Reviewer Experience and Deployment Automation

The default deployment removes mandatory GitHub credentials
and separately installed language model infrastructure.

### Architecture

- Containerized Ollama provides local inference.
- An initialization service provisions the configured model.
- A separate initializer restores the historical snapshot.
- The backend starts after both initialization services succeed.
- Nginx provides dynamic Docker DNS resolution.
- Named volumes preserve analytical state and model files.
- The application header identifies Demo Mode.

### Snapshot provenance and integrity

The bundled snapshot was derived from independently ingested
public Apache Airflow GitHub observations.

It contains one ingestion execution record, 4,999 Gold
lifecycle records, 42 period metric records and five
historical intelligence executions.

Raw Bronze payloads and Silver records are excluded.
Contributor identifiers are consistently pseudonymized.
Retained public PR identifiers prevent guarantees of
complete anonymization.

The initializer validates snapshot version, checksum,
table structure, record counts and SQLite integrity.
Initialization is transactional and does not overwrite
an existing database.

### Validation results

| Validation | Result |
|---|---|
| Analytical equivalence after pseudonymization | Six reporting requests passed |
| Historical intelligence cache compatibility | Three periods passed |
| Idempotent database initialization | Passed |
| Token-free backend deployment | Passed |
| Frontend connectivity after backend recreation | Passed |
| Fresh containerized AI inference | Passed |
| Persistent intelligence cache reuse | Passed |
| Native Ollama connectivity from Docker | Passed |
| Live Mode environment configuration | Passed |
| Backend automated tests | 336 passed |

Containerized CPU inference using qwen3:4b-instruct
completed a full generation and evaluation request
in 176.37 seconds.

Observed Ollama memory utilization was approximately
4.52 GiB during inference.

The generated narrative received an evaluation score
of 100 and hypothesis confidence of 60.

Manual inspection nevertheless identified an incomplete,
mixed-language hypothesis and an insufficiently supported
explanation. Automated approval is not independent proof
of analytical correctness.

### Deployment trade-offs

The historical snapshot enables immediate evaluation
but does not represent continuously refreshed source data.

Cached narratives reduce inference latency. Fresh generation
remains dependent on available compute resources.

Historical model outputs are preserved without rewriting
their original evaluation records.

The Ollama image is pinned by digest. Model tags and
other dependencies are not fully content-addressed.

## Multi-Source Extensibility

GitHub was deliberately selected as the initial source to
demonstrate a complete engineering intelligence workflow.

The current implementation remains GitHub-specific at
several ingestion and transformation boundaries. It is
not yet a fully source-agnostic integration platform.

### Equivalent source systems

A future GitLab or Bitbucket integration would introduce:

1. Source-specific authentication and ingestion adapters.
2. Source-specific Bronze observations and lineage.
3. A canonical Silver engineering entity model.
4. Source-aware Gold lifecycle and period metrics.
5. Source and repository filters in the API and frontend.

GitHub pull requests and GitLab merge requests would map
to a canonical change-request entity.

Identifiers would incorporate source and repository
identity to avoid collisions.

Metric definitions would require semantic compatibility
checks. Review events and approval events should not
automatically be considered equivalent.

Combined metrics would be recomputed from eligible
underlying observations rather than averaging
repository-level medians or percentages.

### Complementary source systems

Jira, CI/CD platforms and incident management systems
would extend the canonical analytical model with
complementary engineering entities.

Cross-source relationships could connect work items,
change requests, builds, deployments and incidents.

This would enable broader engineering delivery analytics,
subject to reliable identity resolution and data coverage.

### Impact on AI Intelligence

The AI layer would continue consuming governed analytical
context rather than unrestricted raw source observations.

Source identity, metric applicability, coverage boundaries
and cross-source relationships would become explicit
components of the analytical context.

Evidence references and cache compatibility keys would
incorporate the applicable source and repository scope.

The objective is to reuse the reasoning, validation,
evaluation and presentation architecture while extending
the underlying integration and semantic models.

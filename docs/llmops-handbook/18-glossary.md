# 18 — Glossary of Key Terms

> **Part XI — Reference.** Concise definitions for the vocabulary used across the handbook. Terms are grouped by area; see the linked chapter for depth.

---

## Core & lifecycle

- **LLMOps** — Operational discipline for developing, deploying, operating, securing, and improving LLM-powered applications. → [`01`](01-foundations.md)
- **MLOps** — Operational discipline for the machine-learning lifecycle (data, training, serving, monitoring); LLMOps extends it. → [`01`](01-foundations.md)
- **Foundation model** — A large, general-purpose pre-trained model adapted to many tasks.
- **GPAI (General-Purpose AI)** — EU AI Act term for foundation models with broad capability; carries provider obligations. → [`11`](11-governance-and-compliance.md)
- **Inference** — Running a trained model to produce output for a given input.
- **Fine-tuning** — Further training a base model on domain data to adapt behavior.
- **Non-determinism** — Property whereby identical inputs can yield different outputs (sampling). → [`01`](01-foundations.md)

## PromptOps — [`02`](02-promptops.md)

- **Prompt** — Instructions/context given to a model (system prompt, exemplars, tool defs, schema).
- **System prompt** — Persistent instructions that set model role and rules.
- **Prompt registry** — Versioned store of prompts loaded by ID + version at runtime.
- **Few-shot examples** — In-context examples that steer model behavior.
- **Content hash** — Hash of exact prompt bytes used, recorded for reproducibility.

## RAGOps — [`03`](03-ragops.md)

- **RAG (Retrieval-Augmented Generation)** — Grounding LLM output in retrieved context.
- **Chunk** — A segment of a source document indexed for retrieval.
- **Embedding** — Vector representation of text for semantic similarity.
- **Vector store / vector DB** — Database for similarity search over embeddings.
- **Hybrid retrieval** — Combining dense (vector) and sparse (keyword/BM25) search.
- **Reranking** — Re-scoring retrieved candidates (often with a cross-encoder) for precision.
- **Faithfulness / groundedness** — Degree to which an answer is supported by provided context.
- **Freshness lag** — Time between source update and its appearance in the index.
- **Tombstone** — A deletion marker removing stale/removed docs from the index.

## EvalOps — [`04`](04-evalops.md)

- **EvalOps** — Continuous, gate-driven evaluation of quality/safety/cost.
- **Golden dataset** — Curated, versioned test cases with expected outputs/rubrics.
- **LLM-as-judge** — Using an LLM to score outputs against a rubric.
- **Offline / online eval** — Pre-release scoring vs. production-traffic scoring.
- **Regression gate** — CI check that blocks changes falling below quality thresholds.
- **Tolerance band** — Allowed variance around a baseline to handle non-determinism.

## Guardrails — [`05`](05-guardrails-ops.md)

- **Guardrail** — Runtime control constraining inputs, outputs, or actions.
- **Input / output / action guardrail** — Controls applied before, after, or on tool use.
- **Jailbreak** — Input crafted to bypass a model's safety constraints.
- **Fail-closed / fail-open** — On error, block (secure) vs. allow (available).
- **Human-in-the-loop (HITL)** — Requiring human approval for certain actions.

## FinOps — [`06`](06-llm-finops.md)

- **Token** — Unit of text the model processes/bills on (input + output).
- **Cost per resolved request** — Total spend ÷ successful outcomes.
- **Model cascade / routing** — Trying cheaper models first, escalating on need.
- **Prompt caching** — Reusing computation/response for stable prompt prefixes.
- **Circuit breaker** — Automatic cutoff when a budget/limit is exceeded.

## Gateway & ModelOps — [`07`](07-model-gateway-and-modelops.md)

- **Model gateway / AI gateway** — Central control plane for all LLM traffic.
- **Model registry** — Versioned catalog of models in use.
- **Model alias** — Stable name apps call, mapped to a pinned model version.
- **Version pinning** — Fixing an exact model version (never `latest`).
- **Fallback** — Routing to an alternate provider/model on failure.
- **PEFT / LoRA / QLoRA** — Parameter-efficient fine-tuning: train small adapter weights over a frozen base model (QLoRA adds quantization).
- **SFT / DPO / RLHF** — Supervised fine-tuning / Direct Preference Optimization / Reinforcement Learning from Human Feedback — behavior- and preference-alignment methods.
- **Eval contamination** — Leakage of eval/golden cases into training data, invalidating scores.

## Observability — [`08`](08-observability-and-opentelemetry.md)

- **OpenTelemetry (OTel)** — CNCF standard for traces, metrics, logs.
- **GenAI semantic conventions** — Standard `gen_ai.*` attribute names for LLM telemetry.
- **Trace / span** — A request's execution path / a single operation within it.
- **SLI / SLO / error budget** — Indicator / objective / allowed unreliability.
- **TTFT (time to first token)** — Latency until the first streamed token.

## Metrics — [`09`](09-llm-metric-catalog.md)

- **Context recall / precision** — Coverage / noise of retrieved context.
- **Hallucination rate** — Fraction of outputs with unsupported claims.
- **MRR / nDCG** — Rank-quality retrieval metrics.
- **Deflection / containment** — Requests resolved without human handoff.

## Security — [`10`](10-security-architecture.md)

- **Prompt injection (direct/indirect)** — Malicious instructions via user input / retrieved content.
- **Excessive agency** — An agent having more capability/authority than needed.
- **Insecure output handling** — Passing model output to a sink unescaped.
- **STRIDE** — Threat-modeling taxonomy (Spoofing, Tampering, Repudiation, Info disclosure, DoS, Elevation).
- **OWASP LLM Top 10** — Authoritative list of top LLM application risks.
- **MITRE ATLAS** — Knowledge base of adversarial ML tactics/techniques.
- **Trust boundary** — Line across which data changes trust level.

## Governance — [`11`](11-governance-and-compliance.md)

- **NIST AI RMF** — Voluntary AI risk framework (Govern, Map, Measure, Manage).
- **GenAI Profile (NIST AI 600-1)** — GenAI-specific companion to the AI RMF.
- **EU AI Act** — EU risk-tiered AI regulation with extraterritorial reach.
- **Model / system card** — Documentation of capabilities, limits, evals, intended use.
- **DPIA** — Data Protection Impact Assessment.
- **ISO/IEC 42001** — Certifiable AI management-system standard.

## Platform & Delivery — [`12`](12-platform-engineering-foundations.md), [`13`](13-cicd-for-llm-apps.md), [`14`](14-progressive-delivery.md)

- **IaC (Infrastructure as Code)** — Managing infra via version-controlled code (e.g. Terraform).
- **Remote state / state locking** — Shared, concurrency-safe Terraform state.
- **Policy as code** — Automated infra guardrails (OPA/Sentinel/checkov).
- **SBOM** — Software Bill of Materials (SPDX/CycloneDX).
- **SLSA** — Supply-chain Levels for Software Artifacts framework.
- **Cosign / Sigstore** — Keyless artifact signing and verification.
- **Attestation / provenance** — Signed statements about how an artifact was built.
- **OIDC federation** — Short-lived, keyless CI-to-cloud authentication.
- **Canary** — Releasing to a small traffic slice, measuring, then expanding.
- **Blue/Green** — Two full environments with an instant switch.
- **Shadow / mirror** — Sending copied traffic to a new version without user impact.
- **Argo Rollouts** — Kubernetes controller for canary/blue-green with analysis.
- **Flagger** — CNCF progressive-delivery operator.
- **Helm** — Kubernetes package manager (charts, releases, revisions).
- **AnalysisTemplate / MetricTemplate** — Metric-based canary gate definitions.
- **Rollout / Canary CR** — Custom resources driving progressive delivery.
- **Rollback decision tree** — Logic for which artifact to revert. → [`14`](14-progressive-delivery.md)

## Operations — [`15`](15-operations-runbook.md)

- **Drift (input/data/model/concept)** — Distribution or behavior change over time.
- **Schedule drift** — Ingestion falling behind source-of-truth freshness.
- **Runbook** — Documented, tested response procedure for a scenario.
- **Game day** — Rehearsed failure-injection exercise.
- **Blameless post-incident review** — Learning-focused incident retrospective.

---

## References

Full source list in [`19-sources-and-references.md`](19-sources-and-references.md).

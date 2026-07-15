"""
Platform / LLMOps / infra Study Lab lessons (hand-authored, repo-grounded).

Covers disciplines from docs/sdd/09-PLATFORM-LLMOPS.md and as-built packages:
evals, observability, CI/CD, Docker, k8s, Terraform, FinOps, security,
integrations, synthetic data, image gen concepts, MLOps/AIOps.
"""

from __future__ import annotations

from study.models import (
    BlankSpec,
    CodeBeat,
    ConceptCard,
    FillBlanks,
    LineAnnotation,
    LineQuizItem,
    QuizItem,
    ReadingRef,
    StudyModule,
)


def _ann(lines: list[tuple[int, str]]) -> list[LineAnnotation]:
    return [LineAnnotation(line=n, note=t) for n, t in lines]


def _lq(items: list[tuple[int, str, str, list[str], str]]) -> list[LineQuizItem]:
    out: list[LineQuizItem] = []
    for line, prompt, answer, choices, why in items:
        ch = choices if answer in choices else [answer, *choices]
        out.append(LineQuizItem(line=line, prompt=prompt, answer=answer, choices=ch[:4], why=why))
    return out


def m10_llmops() -> StudyModule:
    return StudyModule(
        id="10-llmops-disciplines",
        title="10. LLMOps — disciplines map (this repo)",
        description="Deterministic GraphRAG core + optional LLM path; enforce quality outside the model.",
        tags=["llmops", "gateway", "guardrails", "promptops"],
        track="llmops",
        order=100,
        estimated_minutes=25,
        story=(
            "LLMOps is not 'call OpenAI from a script.' It is the operating system around models:\n"
            "versioned prompts, model registry, guardrails, evals, budgets, observability, and CI gates.\n\n"
            "THIS APP (ADR 0001):\n"
            "• Core diagnosis is deterministic GraphRAG + FMEA/Bayes — NOT free-form LLM reasoning.\n"
            "• LLM path is READY-BUT-INACTIVE (llm_enabled=false by default) for wording/gateway.\n"
            "• Security and quality live in code (guardrails/, evals/, finops/), not in 'please be safe' prompts alone.\n\n"
            "Packages: guardrails/, evals/, observability/, gateway/, prompts/, finops/, docs/sdd/09-PLATFORM-LLMOPS.md"
        ),
        one_liner="GraphRAG primary; LLM optional; enforce outside the model; version artifacts; gate with evals.",
        why_it_matters=[
            "Warranty answers must be auditable and reproducible.",
            "Optional LLM still needs budgets, rate limits, and redaction.",
            "Interviews: know discipline map + as-built status ACTIVE vs READY.",
        ],
        say_aloud=[
            "Primary diagnose path does not require an LLM.",
            "LLM_ENABLED defaults to false; gateway and PromptOps are ready-but-inactive.",
            "Guardrails and evals enforce quality outside the model.",
            "Prompts and model aliases are versioned git artifacts.",
        ],
        cheat_sheet=[
            {"term": "ACTIVE", "meaning": "Wired and on by default (obs, guardrails, eval smoke)"},
            {"term": "READY inactive", "meaning": "Code present; off until flag (gateway, PromptOps)"},
            {"term": "PromptOps", "meaning": "Versioned prompts under prompts/ + schema"},
            {"term": "Model registry", "meaning": "models/registry.yaml pinned aliases"},
            {"term": "Guardrails", "meaning": "input/output/action/rate — guardrails/"},
        ],
        beats=[
            CodeBeat(
                id="discipline-map",
                title="Discipline → package (memorize)",
                language="text",
                goal="Map each discipline to a folder.",
                narrative="Interview gold: status + path.",
                code="""Observability   ACTIVE     observability/ + /metrics + OTEL opt-in
Guardrails      ACTIVE     guardrails/
EvalOps         ACTIVE     evals/ + thresholds.yaml
Security docs   ACTIVE     security/ + OWASP LLM mapping
Gateway/ModelOps READY     gateway/ + models/registry.yaml
PromptOps       READY      prompts/ + promptops/
FinOps          READY path finops/budget.py (trips when LLM spends)
RAGOps (graph)  ACTIVE     graph/ GraphRAG (not vector-only RAG)
CI/CD           ACTIVE     .github/workflows/ci.yml + cd.yml
Progressive del WIRED      deploy/rollouts/ + eval-gate
IaC             SCAFFOLD   infra/terraform/""",
                say_after="ACTIVE vs READY is the honesty test.",
                annotations=_ann([(1, "Always-on telemetry path."), (5, "Off until llm_enabled.")]),
                line_quiz=_lq(
                    [
                        (
                            5,
                            "Is the model gateway on by default?",
                            "No — READY but inactive until llm_enabled",
                            ["Always on", "Only in Neo4j", "Only in Redis"],
                            "Defaults protect cost and determinism.",
                        ),
                    ]
                ),
            ),
        ],
        concepts=[
            ConceptCard(
                term="Enforce outside the model",
                definition="Filters, budgets, auth, and evals in software — not prompt-only hope.",
                say_aloud="Never rely on the model alone for safety or budget.",
            ),
        ],
        self_quiz=[
            QuizItem(q="Default llm_enabled?", a="false"),
            QuizItem(q="Where are eval floors?", a="evals/thresholds.yaml"),
            QuizItem(q="Primary diagnosis engine?", a="Neo4j GraphRAG + FMEA/Bayes"),
        ],
        common_mistakes=["Calling this product an LLM chatbot as the core engine."],
        final_boss=["Recite ACTIVE vs READY disciplines with paths."],
        further_reading=[
            ReadingRef(
                title="docs/sdd/09-PLATFORM-LLMOPS.md (code-true map)",
                url="",
                kind="docs",
                takeaway="Use SDD 09 + AS_BUILT, not the whole handbook every session.",
            ),
            ReadingRef(
                title="ADR 0001 adopt LLMOps disciplines",
                url="",
                kind="docs",
                takeaway="Deterministic core + optional LLM + gate non-determinism.",
            ),
        ],
    )


def m11_observability() -> StudyModule:
    return StudyModule(
        id="11-observability-monitoring",
        title="11. Observability & monitoring — logs, metrics, traces",
        description="JSON logs, Prometheus /metrics, OTEL opt-in, Grafana/Prometheus compose.",
        tags=["observability", "prometheus", "otel", "sre"],
        track="observability",
        order=110,
        estimated_minutes=25,
        story=(
            "Observability answers: what is broken, where, and why — from signals the system emits.\n\n"
            "Three pillars (industry):\n"
            "• LOGS — structured JSON events with request_id (observability/logging_setup.py)\n"
            "• METRICS — counters/histograms on /metrics when enable_prometheus_metrics=true\n"
            "• TRACES — OpenTelemetry spans when otel_enabled=true (default false in demo)\n\n"
            "Configs: monitoring/prometheus/, grafana provisioning, docker-compose.observability.yaml, k8s/monitoring/.\n"
            "Claim 'observability is done' only when scrape + dashboard + alerts are real."
        ),
        one_liner="Logs + Prometheus metrics + optional OTEL; prove with scrape targets and alerts.",
        why_it_matters=[
            "Diagnose/promote latency and error rates need numbers.",
            "PII redaction in logs is a security requirement.",
        ],
        say_aloud=[
            "We emit JSON logs with request correlation ids.",
            "Prometheus scrapes /metrics when metrics are enabled.",
            "OTEL is opt-in via otel_enabled.",
            "A metrics endpoint without scrape config is only a stub.",
        ],
        cheat_sheet=[
            {"term": "RED", "meaning": "Rate, Errors, Duration — service metrics"},
            {"term": "USE", "meaning": "Utilization, Saturation, Errors — resources"},
            {"term": "SLI/SLO", "meaning": "Indicator / objective for reliability"},
            {"term": "request_id", "meaning": "Correlation across log lines"},
            {"term": "otlp", "meaning": "OpenTelemetry protocol export"},
        ],
        beats=[
            CodeBeat(
                id="metrics-path",
                title="Metrics endpoint pattern",
                language="python",
                goal="Know where metrics live.",
                narrative="FastAPI exposes /metrics when enabled.",
                code="""# conceptual — api/main.py + observability/metrics.py
@app.get("/metrics")
def metrics():
    if not settings.enable_prometheus_metrics:
        return Response(status_code=404)
    return Response(render_latest_metrics(), media_type=METRICS_CONTENT_TYPE)

# Compose: monitoring/prometheus/prometheus.yml scrapes diagnostics-api:8080
# Alerts: monitoring/prometheus/rules/slo-alerts.yaml""",
                say_after="Enable metrics, scrape them, alert on SLOs.",
                annotations=_ann([(2, "Feature flag."), (7, "Scrape config is the proof.")]),
                line_quiz=_lq(
                    [
                        (
                            3,
                            "What if metrics disabled?",
                            "Return 404 / no metrics",
                            ["Crash Neo4j", "Always 200 empty", "Write Turtle"],
                            "Flag controls export surface.",
                        ),
                    ]
                ),
            ),
        ],
        concepts=[
            ConceptCard(
                term="Three pillars",
                definition="Logs, metrics, traces.",
                say_aloud="Logs for events, metrics for aggregates, traces for request paths.",
            ),
        ],
        self_quiz=[
            QuizItem(q="Default otel_enabled?", a="false (opt-in)"),
            QuizItem(q="Where are alert rules?", a="monitoring/prometheus/rules/ or alerts.yaml"),
        ],
        common_mistakes=["Assuming /metrics alone means production monitoring."],
        final_boss=["Draw log → metrics → trace path for one /diagnose request."],
        further_reading=[
            ReadingRef(
                title="OpenTelemetry docs",
                url="https://opentelemetry.io/docs/",
                kind="docs",
                takeaway="Vendor-neutral traces/metrics/logs.",
            ),
            ReadingRef(
                title="Google SRE Book — Monitoring Distributed Systems",
                url="https://sre.google/sre-book/monitoring-distributed-systems/",
                kind="docs",
                takeaway="Four golden signals / practical monitoring.",
            ),
        ],
    )


def m12_evals() -> StudyModule:
    return StudyModule(
        id="12-evalops-gates",
        title="12. EvalOps — golden sets, safety, thresholds, CI gates",
        description="evals/run_eval.py, thresholds.yaml, smoke vs full, never lower floors to go green.",
        tags=["evals", "evalops", "ci", "quality"],
        track="evals",
        order=120,
        estimated_minutes=25,
        story=(
            "EvalOps is continuous measurement of system quality under fixed cases.\n\n"
            "This repo:\n"
            "• golden/ — expected diagnosis behaviors\n"
            "• safety/injection.jsonl — prompt-injection style cases\n"
            "• thresholds.yaml — floors that CI enforces\n"
            "• smoke suite in PR CI; full suite in eval-nightly.yml\n\n"
            "Rule from SDD: NEVER lower thresholds to make CI green — fix the regression."
        ),
        one_liner="Smoke on every PR; full nightly; safety_pass = 1.0; fix code not floors.",
        why_it_matters=[
            "Non-determinism and ranking regressions need automated gates.",
            "Safety cases catch jailbreak/injection patterns early.",
        ],
        say_aloud=[
            "CI runs python evals/run_eval.py --suite smoke.",
            "Nightly can run the full suite against a live graph.",
            "Safety pass rate must be 1.0 for smoke.",
            "I never lower thresholds to go green.",
        ],
        cheat_sheet=[
            {"term": "Golden set", "meaning": "Labeled cases with expected outcomes"},
            {"term": "Safety suite", "meaning": "Adversarial/injection cases"},
            {"term": "Floor", "meaning": "Minimum metric to pass gate"},
            {"term": "smoke", "meaning": "Fast CI suite"},
            {"term": "full", "meaning": "Stricter nightly/release suite"},
        ],
        beats=[
            CodeBeat(
                id="eval-cmd",
                title="Commands to memorize",
                language="bash",
                goal="Type the two eval commands from memory.",
                narrative="Smoke always; full when graph available.",
                code="""# PR / CI
python evals/run_eval.py --suite smoke

# Nightly / release (graph up)
python evals/run_eval.py --suite full --report eval-report.json

# Floors live in evals/thresholds.yaml
# Workflows: .github/workflows/ci.yml  +  eval-nightly.yml""",
                say_after="Smoke in CI, full at night, floors in yaml.",
                fill_blanks=FillBlanks(
                    template="python evals/run_eval.py --suite {{s}}\n# floors: evals/{{f}}",
                    blanks=[
                        BlankSpec(id="s", answer="smoke"),
                        BlankSpec(id="f", answer="thresholds.yaml"),
                    ],
                ),
                line_quiz=_lq(
                    [
                        (
                            2,
                            "Which suite runs in PR CI?",
                            "smoke",
                            ["full only", "none", "terraform plan"],
                            "ci.yml eval gate uses smoke.",
                        ),
                    ]
                ),
            ),
        ],
        concepts=[
            ConceptCard(
                term="Eval gate",
                definition="Automated quality check that can block merge/deploy.",
                say_aloud="Gates turn metrics into release decisions.",
            ),
        ],
        self_quiz=[
            QuizItem(q="Where are floors defined?", a="evals/thresholds.yaml"),
            QuizItem(q="Safety_pass smoke target?", a="1.0 (all safety cases pass)"),
        ],
        common_mistakes=["Editing thresholds downward to silence a red build."],
        final_boss=["Explain smoke vs full and name both workflow files."],
        further_reading=[
            ReadingRef(
                title="LangSmith / eval practices (industry)",
                url="https://docs.smith.langchain.com/evaluation",
                kind="docs",
                takeaway="Dataset + evaluators + regressions over time.",
            ),
        ],
    )


def m13_cicd() -> StudyModule:
    return StudyModule(
        id="13-cicd-github-actions",
        title="13. CI/CD — GitHub Actions, supply chain, CD gate",
        description="ci.yml tests+scans+eval; cd.yml deploy after gates; secret scan, SBOM mindset.",
        tags=["cicd", "github-actions", "supply-chain"],
        track="cicd",
        order=130,
        estimated_minutes=25,
        story=(
            "CI (Continuous Integration): every push/PR runs automated checks.\n"
            "CD (Continuous Delivery/Deploy): promote artifacts after gates.\n\n"
            "This repo workflows:\n"
            "• ci.yml — gitleaks, ruff, pytest, eval smoke, frontend, images, Trivy/SBOM/sign where configured\n"
            "• cd.yml — eval-gate then deploy strategy\n"
            "• eval-nightly.yml — fuller eval against graph\n\n"
            "Supply chain: don't just test code — scan secrets, deps, container images."
        ),
        one_liner="PR: lint+test+eval smoke; release: stronger gates then deploy.",
        why_it_matters=[
            "Prevents broken GraphRAG or open secrets from shipping.",
            "Eval gate ties ML/quality to delivery.",
        ],
        say_aloud=[
            "CI runs on main and feature branches.",
            "Secret scan runs before trust.",
            "Eval smoke is part of CI.",
            "CD should not skip the eval gate.",
        ],
        cheat_sheet=[
            {"term": "Gitleaks", "meaning": "Secret scanning in CI"},
            {"term": "SBOM", "meaning": "Software Bill of Materials"},
            {"term": "Cosign", "meaning": "Image signing (when wired)"},
            {"term": "Trivy", "meaning": "Container/fs vulnerability scan"},
            {"term": "Branch filters", "meaning": "main + feature/** triggers"},
        ],
        beats=[
            CodeBeat(
                id="ci-jobs",
                title="CI job spine (conceptual)",
                language="yaml",
                goal="Order the mental checklist.",
                narrative="You don't need every YAML line — you need the job story.",
                code="""# .github/workflows/ci.yml (mental model)
on: push/PR → main, feature/**

jobs:
  secret-scan:  gitleaks
  test:
    - setup Python 3.12
    - ruff check + format
    - pytest (multi-source + full)
    - eval smoke
    - frontend build checks
  # image build/scan/sign steps as configured for supply chain""",
                say_after="Secrets first, then quality, then artifacts.",
                line_quiz=_lq(
                    [
                        (
                            6,
                            "Why secret-scan early?",
                            "Fail before wasting CI on leaked credentials",
                            ["Neo4j requires it", "Only for Docker", "Format only"],
                            "Stop the pipeline if secrets appear.",
                        ),
                    ]
                ),
            ),
        ],
        concepts=[
            ConceptCard(
                term="CI vs CD",
                definition="CI verifies every change; CD ships verified artifacts.",
                say_aloud="Integrate continuously; deliver when gates pass.",
            ),
        ],
        self_quiz=[
            QuizItem(q="Name three workflow files.", a="ci.yml, cd.yml, eval-nightly.yml"),
            QuizItem(q="Which eval suite in PR CI?", a="smoke"),
        ],
        common_mistakes=["Deploying from main without eval gate."],
        final_boss=["Whiteboard CI stages for this monorepo."],
        further_reading=[
            ReadingRef(
                title="GitHub Actions documentation",
                url="https://docs.github.com/en/actions",
                kind="docs",
                takeaway="Workflows, jobs, permissions least privilege.",
            ),
            ReadingRef(
                title="SLSA supply chain levels",
                url="https://slsa.dev/",
                kind="standard",
                takeaway="Provenance and integrity of builds.",
            ),
        ],
    )


def m14_docker() -> StudyModule:
    return StudyModule(
        id="14-docker-compose",
        title="14. Docker — images, compose, dual Neo4j, observability stack",
        description="Dockerfiles for api/frontend/etl; compose for infra, redis, observability.",
        tags=["docker", "compose", "containers"],
        track="infra",
        order=140,
        estimated_minutes=20,
        story=(
            "Containers package app + runtime so 'works on my machine' becomes 'works on this image.'\n\n"
            "This repo:\n"
            "• docker/Dockerfile.api, .frontend, .etl, .mock\n"
            "• docker-compose.infra.yaml — Neo4j prod :7687 + staging :7688\n"
            "• docker-compose.redis.yaml — optional shared state\n"
            "• docker-compose.observability.yaml — Prometheus/Grafana/OTEL stack\n\n"
            "Image = layers + entrypoint. Compose = multi-service local (or simple) topology."
        ),
        one_liner="Build images with Dockerfiles; run multi-service stacks with Compose.",
        why_it_matters=["Reproducible demo and CI images.", "Dual graph needs two Neo4j services."],
        say_aloud=[
            "Infra compose starts dual Neo4j for staging and production.",
            "API image is built from docker/Dockerfile.api.",
            "Redis compose is optional for multi-replica shared state.",
        ],
        cheat_sheet=[
            {"term": "Image", "meaning": "Immutable filesystem + metadata"},
            {"term": "Container", "meaning": "Running instance of an image"},
            {"term": "Compose", "meaning": "YAML multi-service definition"},
            {"term": "Volume", "meaning": "Persisted data outside container lifecycle"},
            {"term": "Port map", "meaning": "host:container networking"},
        ],
        beats=[
            CodeBeat(
                id="compose-cmd",
                title="Commands",
                language="bash",
                goal="Start infra from memory.",
                code="""docker compose -f docker/docker-compose.infra.yaml up -d
# optional
docker compose -f docker/docker-compose.redis.yaml up -d
docker compose -f docker/docker-compose.observability.yaml up -d

# build API image (CI/local)
docker build -f docker/Dockerfile.api -t diagnostics-api:local .""",
                say_after="Infra first, then API, then optional obs/redis.",
                fill_blanks=FillBlanks(
                    template="docker compose -f docker/{{f}} up -d",
                    blanks=[BlankSpec(id="f", answer="docker-compose.infra.yaml")],
                ),
            ),
        ],
        concepts=[
            ConceptCard(
                term="Multi-stage build",
                definition="Build in one stage, copy artifacts to slim runtime stage.",
                say_aloud="Smaller final images, better security surface.",
            ),
        ],
        self_quiz=[
            QuizItem(q="Staging Neo4j host port?", a="7688 (prod 7687)"),
            QuizItem(q="Where are Dockerfiles?", a="docker/"),
        ],
        common_mistakes=["One Neo4j for both stage and prod in demos that claim dual graph."],
        final_boss=["Name three compose files and what each starts."],
        further_reading=[
            ReadingRef(
                title="Docker docs — Compose",
                url="https://docs.docker.com/compose/",
                kind="docs",
                takeaway="Services, networks, volumes.",
            ),
        ],
    )


def m15_k8s_helm() -> StudyModule:
    return StudyModule(
        id="15-k8s-helm-rollouts",
        title="15. Kubernetes, Helm concepts, progressive delivery",
        description="k8s/base manifests, overlays, monitoring CRs; Helm as package; Argo/Flagger rollouts.",
        tags=["kubernetes", "helm", "canary", "gitops"],
        track="infra",
        order=150,
        estimated_minutes=30,
        story=(
            "Kubernetes schedules containers on a cluster using declarative YAML (desired state).\n\n"
            "This repo:\n"
            "• k8s/base/ — Deployments, Services for API etc.\n"
            "• k8s/overlays/ — env-specific patches\n"
            "• k8s/monitoring/ — ServiceMonitor / PrometheusRule style wiring\n"
            "• deploy/rollouts/ — Argo Rollouts / Flagger canary skeletons\n"
            "• deploy/policy/verify-images.yaml — image verification policy\n\n"
            "Helm packages K8s YAML as charts with values — reusable templates.\n"
            "This repo leans raw kustomize-style overlays + rollout YAMLs more than a full chart tree,\n"
            "but you must know Helm vocabulary for interviews."
        ),
        one_liner="Declarative k8s manifests + overlays; Helm packages charts; canaries need metrics+eval.",
        why_it_matters=["Production scale ≠ docker compose.", "Canary needs quality signals from evals/metrics."],
        say_aloud=[
            "Pods run containers; Deployments manage replicas; Services expose them.",
            "Overlays patch base manifests per environment.",
            "Helm charts parameterize installs with values.yaml.",
            "Progressive delivery uses canary analysis before full traffic.",
        ],
        cheat_sheet=[
            {"term": "Pod", "meaning": "Smallest deployable unit"},
            {"term": "Deployment", "meaning": "Replica + rolling update controller"},
            {"term": "Service", "meaning": "Stable virtual IP / DNS"},
            {"term": "ConfigMap/Secret", "meaning": "Config vs sensitive config"},
            {"term": "Helm chart", "meaning": "Templated package of manifests"},
            {"term": "values.yaml", "meaning": "Chart parameters"},
            {"term": "Canary", "meaning": "Send small traffic %, analyze, promote/rollback"},
        ],
        beats=[
            CodeBeat(
                id="k8s-objects",
                title="Core objects (text)",
                language="text",
                goal="Define Pod, Deployment, Service in one line each.",
                code="""Pod         = running container(s) + volumes
Deployment  = desired replicas + rolling update of Pod template
Service     = stable network endpoint to Pods
Ingress     = HTTP routing into cluster
ConfigMap   = non-secret config
Secret      = sensitive config (still need external secret mgmt in prod)

Repo paths:
  k8s/base/*.yaml
  k8s/overlays/*
  deploy/rollouts/argo-rollout.yaml
  deploy/rollouts/flagger-canary.yaml""",
                say_after="Base + overlay; rollouts for canary.",
                line_quiz=_lq(
                    [
                        (
                            3,
                            "What does a Service provide?",
                            "Stable network access to Pods",
                            ["Builds Docker images", "Runs pytest", "Stores Neo4j only"],
                            "Pods are ephemeral; Service DNS stays.",
                        ),
                    ]
                ),
            ),
            CodeBeat(
                id="helm-mini",
                title="Helm mental model",
                language="bash",
                goal="Know install/upgrade/rollback verbs.",
                code="""# Helm is the package manager for Kubernetes
helm install diagnostics ./charts/diagnostics -f values-prod.yaml
helm upgrade diagnostics ./charts/diagnostics -f values-prod.yaml
helm rollback diagnostics 1

# Chart layout (typical)
# charts/diagnostics/
#   Chart.yaml
#   values.yaml
#   templates/deployment.yaml
#   templates/service.yaml""",
                say_after="install, upgrade, rollback — values select env.",
                fill_blanks=FillBlanks(
                    template="helm {{a}} myrel ./chart -f values.yaml\nhelm {{b}} myrel 1",
                    blanks=[
                        BlankSpec(id="a", answer="upgrade"),
                        BlankSpec(id="b", answer="rollback"),
                    ],
                ),
            ),
        ],
        concepts=[
            ConceptCard(
                term="Progressive delivery",
                definition="Ship gradually with automated analysis and fast rollback.",
                say_aloud="Canary uses metrics and evals, not hope.",
            ),
        ],
        self_quiz=[
            QuizItem(q="Where are base k8s manifests?", a="k8s/base/"),
            QuizItem(q="Helm values file role?", a="Parameterize chart templates per env."),
        ],
        common_mistakes=["Canary without a success metric or eval gate."],
        final_boss=["Explain base vs overlay vs Helm chart in 45 seconds."],
        further_reading=[
            ReadingRef(
                title="Kubernetes documentation",
                url="https://kubernetes.io/docs/home/",
                kind="docs",
                takeaway="Objects, controllers, desired state.",
            ),
            ReadingRef(
                title="Helm docs",
                url="https://helm.sh/docs/",
                kind="docs",
                takeaway="Charts, values, releases.",
            ),
        ],
    )


def m16_iac_terraform() -> StudyModule:
    return StudyModule(
        id="16-iac-terraform",
        title="16. Infrastructure as Code — Terraform patterns",
        description="infra/terraform scaffold; plan/apply; state; modules; estimate costs separately.",
        tags=["terraform", "iac", "cloud"],
        track="infra",
        order=160,
        estimated_minutes=25,
        story=(
            "IaC means infrastructure is declared in code, reviewed in PRs, and applied by automation.\n\n"
            "Terraform language (HCL): providers, resources, modules, state backend.\n"
            "This repo: infra/terraform/ is a SCAFFOLD — placeholders for cloud landing zones,\n"
            "not a full multi-account production estate. Runtime demo is Docker-first.\n\n"
            "Workflow: write .tf → terraform init → plan → apply (with approval) → destroy carefully."
        ),
        one_liner="Declare cloud resources in HCL; plan before apply; remote state for teams.",
        why_it_matters=["Reproducible environments.", "Audit trail of infra changes."],
        say_aloud=[
            "Terraform plan shows the diff before apply.",
            "State maps resources to real cloud objects.",
            "Modules package reusable infrastructure.",
            "Our terraform tree is scaffold; compose is the local runtime.",
        ],
        cheat_sheet=[
            {"term": "provider", "meaning": "Cloud/API plugin (aws, azurerm, …)"},
            {"term": "resource", "meaning": "One managed object"},
            {"term": "state", "meaning": "Terraform's memory of real resources"},
            {"term": "plan", "meaning": "Dry-run execution plan"},
            {"term": "apply", "meaning": "Execute plan"},
            {"term": "module", "meaning": "Reusable composition of resources"},
        ],
        beats=[
            CodeBeat(
                id="tf-workflow",
                title="Workflow commands",
                language="bash",
                goal="Recite init/plan/apply.",
                code="""cd infra/terraform
terraform init          # providers + modules
terraform fmt -check
terraform validate
terraform plan -out tf.plan
terraform apply tf.plan # only after review

# NEVER commit secrets; use env vars / secret managers
# Cost: use plan + cloud pricing calculator / Infracost — not guesswork""",
                say_after="init, validate, plan, apply — with human review.",
                fill_blanks=FillBlanks(
                    template="terraform {{a}}\nterraform {{b}} -out tf.plan\nterraform {{c}} tf.plan",
                    blanks=[
                        BlankSpec(id="a", answer="init"),
                        BlankSpec(id="b", answer="plan"),
                        BlankSpec(id="c", answer="apply"),
                    ],
                ),
            ),
        ],
        concepts=[
            ConceptCard(
                term="Desired state",
                definition="You declare end state; tool converges reality.",
                say_aloud="IaC converges to the declared configuration.",
            ),
        ],
        self_quiz=[
            QuizItem(q="What does terraform plan do?", a="Shows changes without applying."),
            QuizItem(q="Is this repo's Terraform production-complete?", a="No — scaffold; Docker is demo runtime."),
        ],
        common_mistakes=["Applying from a laptop without remote state locks."],
        final_boss=["Write a 4-line story of init→plan→apply and where state lives."],
        further_reading=[
            ReadingRef(
                title="Terraform documentation",
                url="https://developer.hashicorp.com/terraform/docs",
                kind="docs",
                takeaway="Core workflow and state.",
            ),
            ReadingRef(
                title="Infracost (IaC cost estimate)",
                url="https://www.infracost.io/",
                kind="docs",
                takeaway="Diff cost on terraform plan.",
            ),
        ],
    )


def m17_finops_cost() -> StudyModule:
    return StudyModule(
        id="17-finops-cost",
        title="17. FinOps & cost estimation — LLM budget + infra costing",
        description="DailyCostBudget circuit breaker; estimate infra/service cost; unit economics.",
        tags=["finops", "cost", "budget"],
        track="finops",
        order=170,
        estimated_minutes=25,
        story=(
            "FinOps is the practice of bringing financial accountability to cloud/variable spend.\n\n"
            "In THIS app (LLM path):\n"
            "• finops/budget.py DailyCostBudget with llm_cost_budget_usd_per_day (default $5)\n"
            "• Gateway records spend; BudgetExceeded trips circuit when ceiling hit\n"
            "• Redis shares budget across replicas when configured\n\n"
            "Infra costing (general method):\n"
            "1) Inventory services (API pods, Neo4j, Redis, load balancer, egress, observability).\n"
            "2) Price each with cloud calculator or committed rates.\n"
            "3) Add LLM tokens: cost ≈ (input_tokens·p_in + output_tokens·p_out) / 1e6.\n"
            "4) Unit cost = monthly_spend / successful_diagnoses.\n"
            "5) Alerts on budget burn rate — not only absolute ceiling."
        ),
        one_liner="Budget breaker for LLM $; inventory+price for infra; track cost per diagnosis.",
        why_it_matters=["LLM spend is spiky.", "Graphs and observability clusters are not free."],
        say_aloud=[
            "DailyCostBudget is a circuit breaker on LLM spend.",
            "Default demo ceiling is five dollars per day.",
            "I estimate infra from inventory times unit prices.",
            "Token cost is priced per million tokens in and out.",
        ],
        cheat_sheet=[
            {"term": "Circuit breaker", "meaning": "Stop calls when budget exceeded"},
            {"term": "Unit economics", "meaning": "Cost per successful business action"},
            {"term": "Egress", "meaning": "Data transfer out — often surprising cost"},
            {"term": "Commitment discount", "meaning": "Reserved/savings plans lower unit price"},
            {"term": "Burn rate", "meaning": "Spend per day vs budget"},
        ],
        beats=[
            CodeBeat(
                id="budget-idea",
                title="Budget breaker idea",
                language="python",
                goal="Explain record + trip.",
                code="""# finops/budget.py — conceptual
class DailyCostBudget:
    def __init__(self, ceiling_usd: float):
        self.ceiling_usd = ceiling_usd
        self._spent = 0.0

    def allow(self, estimated_usd: float) -> bool:
        return (self._spent + estimated_usd) <= self.ceiling_usd

    def record(self, actual_usd: float) -> None:
        self._spent += actual_usd
        if self._spent > self.ceiling_usd:
            raise BudgetExceeded("daily LLM budget exceeded")

# settings.llm_cost_budget_usd_per_day = 5.0
# token estimate: (in_tok * price_in + out_tok * price_out) / 1_000_000""",
                say_after="Allow before call; record after; trip when over.",
                line_quiz=_lq(
                    [
                        (
                            10,
                            "What happens when spent exceeds ceiling?",
                            "Raise BudgetExceeded / open circuit",
                            ["Delete Neo4j", "Lower eval floors", "Disable Docker"],
                            "Circuit breaker pattern for cost.",
                        ),
                    ]
                ),
                fill_blanks=FillBlanks(
                    template="cost = (in_tok * p_in + out_tok * p_out) / {{d}}\nif not budget.allow(cost): raise BudgetExceeded",
                    blanks=[BlankSpec(id="d", answer="1_000_000", hint="per million tokens")],
                ),
            ),
            CodeBeat(
                id="infra-estimate",
                title="Infra estimate worksheet (text)",
                language="text",
                goal="List cost lines for this architecture.",
                code="""Monthly rough model (worksheet — fill with real prices):
API compute     = replicas * vCPU_price * hours
Neo4j           = managed graph tier OR VMs + disk + backup
Redis           = managed cache tier
Load balancer   = fixed + LCU/egress
Observability   = metrics samples + log GB + trace spans
LLM (if on)     = tokens * $/1M + image gen units
Data transfer   = egress GB * rate
----------------
Total / diagnoses_per_month = $ per diagnosis

Tools: cloud pricing calculator, Infracost on terraform plan,
provider token price pages, Prometheus cost metrics if exported.""",
                say_after="Inventory, price, divide by business volume.",
            ),
        ],
        concepts=[
            ConceptCard(
                term="FinOps",
                definition="Cloud financial operations — visibility, optimization, accountability.",
                say_aloud="Engineers and finance share ownership of spend.",
            ),
        ],
        self_quiz=[
            QuizItem(q="Which setting caps daily LLM $?", a="llm_cost_budget_usd_per_day"),
            QuizItem(q="Where is budget code?", a="finops/budget.py"),
        ],
        common_mistakes=["Forgetting egress and observability in estimates."],
        final_boss=["Estimate $ per diagnosis with 3 infra lines + tokens (symbolic)."],
        further_reading=[
            ReadingRef(
                title="FinOps Foundation Framework",
                url="https://www.finops.org/",
                kind="standard",
                takeaway="Inform, optimize, operate.",
            ),
        ],
    )


def m18_security() -> StudyModule:
    return StudyModule(
        id="18-security-guardrails",
        title="18. Security — threat model, OWASP LLM, guardrails",
        description="security/threat-model, owasp-llm-mapping, input/output/action guardrails, redaction.",
        tags=["security", "owasp", "guardrails", "pii"],
        track="security",
        order=180,
        estimated_minutes=25,
        story=(
            "Security for this system spans classic web/API threats and LLM-specific threats.\n\n"
            "Repo anchors:\n"
            "• security/threat-model.md\n"
            "• security/owasp-llm-mapping.md\n"
            "• guardrails/input.py, output.py, action.py, rate_limit.py, pipeline.py\n"
            "• observability redaction for PII in logs\n"
            "• evals/safety for injection cases\n\n"
            "Principle: enforce in code and infra; prompts alone are not controls."
        ),
        one_liner="Threat model + OWASP LLM map + guardrails pipeline + safety evals.",
        why_it_matters=["Injection, data leak, over-agent actions, budget abuse."],
        say_aloud=[
            "Guardrails run on the way in and out of the API.",
            "Rate limits reduce abuse.",
            "PII redaction protects logs and telemetry.",
            "Safety eval suite must stay at full pass.",
        ],
        cheat_sheet=[
            {"term": "LLM01", "meaning": "Prompt injection (OWASP LLM Top 10 family)"},
            {"term": "Input guard", "meaning": "Block/transform unsafe user text"},
            {"term": "Output guard", "meaning": "Filter model/app outputs"},
            {"term": "Action guard", "meaning": "Block dangerous side effects"},
            {"term": "ZDR", "meaning": "Zero data retention with providers"},
        ],
        beats=[
            CodeBeat(
                id="guard-pipeline",
                title="Guard pipeline order (conceptual)",
                language="text",
                goal="Order the layers.",
                code="""Request
  → rate_limit (abuse)
  → input guardrails (injection, length, PII patterns)
  → business logic / GraphRAG / optional LLM gateway
  → output guardrails (leakage, length)
  → action guardrails (claims/escalation side effects)
  → response + redacted logs

Artifacts:
  guardrails/*
  security/threat-model.md
  security/owasp-llm-mapping.md
  evals/safety/injection.jsonl""",
                say_after="Rate, input, core, output, action.",
                line_quiz=_lq(
                    [
                        (
                            3,
                            "Why input guards before GraphRAG?",
                            "Stop abusive payloads early",
                            ["Neo4j syntax", "Helm only", "Terraform state"],
                            "Cheap reject before expensive work.",
                        ),
                    ]
                ),
            ),
        ],
        concepts=[
            ConceptCard(
                term="Defense in depth",
                definition="Multiple independent controls.",
                say_aloud="No single control is enough.",
            ),
        ],
        self_quiz=[
            QuizItem(q="Where is OWASP mapping?", a="security/owasp-llm-mapping.md"),
            QuizItem(q="Safety eval path?", a="evals/safety/"),
        ],
        common_mistakes=["Relying only on system prompt for security."],
        final_boss=["Map one OWASP LLM risk to a repo control."],
        further_reading=[
            ReadingRef(
                title="OWASP Top 10 for LLM Applications",
                url="https://owasp.org/www-project-top-10-for-large-language-model-applications/",
                kind="standard",
                takeaway="LLM-specific risk categories.",
            ),
        ],
    )


def m19_integrations() -> StudyModule:
    return StudyModule(
        id="19-integrations",
        title="19. Integrations — CRM, claims, eligibility, mock SoR",
        description="integrations/* anti-corruption; simulation mock apps; never block core graph on mock outage patterns.",
        tags=["integrations", "crm", "claims", "api"],
        track="integrations",
        order=190,
        estimated_minutes=20,
        story=(
            "Enterprise diagnosis sits beside systems of record:\n"
            "CRM assets, claims, warranty eligibility, case management.\n\n"
            "This repo:\n"
            "• integrations/crm_enrichment.py\n"
            "• integrations/claims_workflow.py\n"
            "• integrations/warranty_eligibility.py\n"
            "• integrations/case_management.py\n"
            "• simulation/mock_enterprise_apps.py for local demos\n\n"
            "Pattern: adapters translate foreign models into our domain; graph remains source of diagnostic truth."
        ),
        one_liner="Adapters for CRM/claims/eligibility; mocks for demo; graph owns diagnosis evidence.",
        why_it_matters=[
            "Real orgs will not replace SAP/Salesforce overnight.",
            "Mocks prove UX without prod credentials.",
        ],
        say_aloud=[
            "Integrations are adapters, not the diagnosis brain.",
            "Mock enterprise apps stand in for SoR locally.",
            "Claims and eligibility are side paths around GraphRAG ranking.",
        ],
        cheat_sheet=[
            {"term": "SoR", "meaning": "System of record"},
            {"term": "Adapter", "meaning": "Translate external API ↔ domain"},
            {"term": "Idempotent submit", "meaning": "Safe retries for claims"},
            {"term": "Enrichment", "meaning": "Add CRM context to session"},
        ],
        beats=[
            CodeBeat(
                id="integration-map",
                title="Package map",
                language="text",
                goal="Name four integration modules.",
                code="""integrations/
  crm_enrichment.py        # customer/asset context
  claims_workflow.py       # submit/list/status claims
  warranty_eligibility.py  # policy / coverage checks
  case_management.py       # escalation cases

simulation/mock_enterprise_apps.py  # local HTTP stand-ins
# Live SAP/SFDC connectors = roadmap (fixtures today)""",
                say_after="Four adapters + mock simulator.",
            ),
        ],
        concepts=[
            ConceptCard(
                term="Anti-corruption layer",
                definition="Protect domain model from external schema mess.",
                say_aloud="Adapters translate; domain stays clean.",
            ),
        ],
        self_quiz=[
            QuizItem(q="Where is claims workflow?", a="integrations/claims_workflow.py"),
            QuizItem(q="Are live SAP connectors productized?", a="No — fixtures/mocks pattern."),
        ],
        common_mistakes=["Putting ranking logic inside CRM adapters."],
        final_boss=["Draw CRM → API → GraphRAG → claims sequence."],
        further_reading=[
            ReadingRef(
                title="Enterprise Integration Patterns (Hohpe & Woolf)",
                url="https://www.enterpriseintegrationpatterns.com/",
                kind="book",
                takeaway="Adapters, messaging, canonical data models.",
            ),
        ],
    )


def m20_synthetic_mlops_images() -> StudyModule:
    return StudyModule(
        id="20-synthetic-mlops-images",
        title="20. Synthetic data, MLOps, image generation concepts",
        description="synthetic_data_generator; model registry/finetunes; image gen cost/safety concepts.",
        tags=["synthetic-data", "mlops", "images", "training"],
        track="mlops",
        order=200,
        estimated_minutes=30,
        story=(
            "Synthetic data: generate realistic-but-fake catalogs for demos and tests without customer PII.\n"
            "This repo: graph/synthetic_data_generator.py + data/synthetic_diagnosis_data.json paths.\n\n"
            "MLOps: train/eval/deploy/monitor models as products.\n"
            "Here: models/registry.yaml pins aliases; models/finetunes/ README for future fine-tunes;\n"
            "evals gate quality; LLM path optional.\n\n"
            "Image generation (concept): diffusion/autoregressive models turn prompts into pixels;\n"
            "ops concerns = content safety, cost per image, latency, prompt versioning, abuse rate limits.\n"
            "Not the core warranty engine — but FinOps/security still apply if you add it.\n\n"
            "AIOps: apply ML/automation to ops signals (anomaly detection on metrics, auto-remediation).\n"
            "Pair with Prometheus rules today; smarter detectors later."
        ),
        one_liner="Synthetic ABox for safe demos; MLOps = registry+eval+deploy; images need safety+cost controls.",
        why_it_matters=[
            "Demos must not leak real customer data.",
            "Fine-tunes without eval gates are reckless.",
            "Image/LLM features change cost and abuse surface.",
        ],
        say_aloud=[
            "Synthetic generators build demo catalogs without production PII.",
            "Model aliases are pinned in registry.yaml.",
            "Fine-tunes need baseline evals before promotion.",
            "Image generation needs safety filters and unit cost tracking.",
            "AIOps automates ops using telemetry — start with alerts, then models.",
        ],
        cheat_sheet=[
            {"term": "Synthetic data", "meaning": "Artificially generated training/demo data"},
            {"term": "Data drift", "meaning": "Input distribution shifts over time"},
            {"term": "Model registry", "meaning": "Catalog of model versions/aliases"},
            {"term": "Fine-tune", "meaning": "Adapt base model on domain data"},
            {"term": "Diffusion", "meaning": "Common modern image gen paradigm"},
            {"term": "AIOps", "meaning": "ML-assisted IT operations"},
            {"term": "MLOps", "meaning": "Lifecycle for ML systems"},
        ],
        beats=[
            CodeBeat(
                id="synthetic-role",
                title="Synthetic data role in this monorepo",
                language="text",
                goal="Separate synthetic demo data from production SoR truth.",
                code="""graph/synthetic_data_generator.py
  → builds demo Product/Symptom/FM structures
data/synthetic_diagnosis_data.json (path via settings)
  → offline catalog for local graphs

Rules:
  • Label simulated provenance so analysts know it is not live SAP
  • Never train production models on unreviewed synthetic-only data without validation
  • Prefer multi-source ABox promote path for "real" knowledge growth""",
                say_after="Synthetic is for safe demos; governed ABox for truth.",
            ),
            CodeBeat(
                id="mlops-loop",
                title="MLOps loop (memorize)",
                language="text",
                goal="Recite the lifecycle.",
                code="""Data → Train/Fine-tune → Eval gates → Registry pin → Deploy (flag/alias)
  → Monitor quality/cost/latency → Rollback or retrain

Repo hooks:
  models/registry.yaml     pin alias → provider model id
  models/finetunes/        future fine-tune artifacts + eval_baseline note
  evals/                   quality/safety floors
  gateway/                 runtime routing when llm_enabled
  finops/budget.py         cost circuit breaker""",
                say_after="Eval before pin; monitor after deploy; budget always.",
                line_quiz=_lq(
                    [
                        (
                            1,
                            "What gates promotion of a new model alias?",
                            "Eval floors / quality gates",
                            ["Faster Docker build only", "Higher Redis TTL", "More Turtle files"],
                            "Non-determinism needs measurement.",
                        ),
                    ]
                ),
            ),
            CodeBeat(
                id="image-gen-ops",
                title="Image generation ops checklist",
                language="text",
                goal="List ops controls for image features.",
                code="""If adding image generation to a product:
  1. Content safety filters (NSFW, brand abuse)
  2. Rate limits + authz (who can generate)
  3. Cost per image metric + FinOps budget
  4. Prompt/version logging (PromptOps)
  5. Retention policy for outputs
  6. Latency SLO separate from diagnose p99
  7. Red-team prompts (indirect injection via images/docs if multimodal)

Not required for core warranty GraphRAG path.""",
                say_after="Safety, cost, rate, retention, SLO — then model choice.",
            ),
        ],
        concepts=[
            ConceptCard(
                term="MLOps",
                definition="Engineering culture/tools for production ML lifecycle.",
                say_aloud="Treat models like versioned products with gates.",
            ),
            ConceptCard(
                term="AIOps",
                definition="Automating operations using analytics/ML on telemetry.",
                say_aloud="Alerts first; smarter detection when data matures.",
            ),
        ],
        self_quiz=[
            QuizItem(q="Where is model registry?", a="models/registry.yaml"),
            QuizItem(q="Synthetic generator module?", a="graph/synthetic_data_generator.py"),
            QuizItem(q="Why not train only on synthetic?", a="May not match real distributions; need validation."),
        ],
        common_mistakes=["Shipping fine-tunes without eval baselines."],
        final_boss=["Draw MLOps loop and map each step to a repo path."],
        further_reading=[
            ReadingRef(
                title="Google — Practitioners guide to MLOps",
                url="https://cloud.google.com/resources/mlops-whitepaper",
                kind="docs",
                takeaway="Continuous training, delivery, monitoring.",
            ),
            ReadingRef(
                title="Ho et al., Denoising Diffusion Probabilistic Models (image gen)",
                url="https://arxiv.org/abs/2006.11239",
                kind="paper",
                takeaway="Foundational diffusion training objective.",
            ),
        ],
    )


def platform_modules() -> list[StudyModule]:
    return [
        m10_llmops(),
        m11_observability(),
        m12_evals(),
        m13_cicd(),
        m14_docker(),
        m15_k8s_helm(),
        m16_iac_terraform(),
        m17_finops_cost(),
        m18_security(),
        m19_integrations(),
        m20_synthetic_mlops_images(),
    ]

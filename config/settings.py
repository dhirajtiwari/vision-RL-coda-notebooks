from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    project_root: Path = PROJECT_ROOT

    neo4j_uri: str = "bolt://localhost:7687"  # production diagnose path
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"
    # Staging graph (promote-first target). Default separate port 7688.
    neo4j_staging_uri: str = "bolt://localhost:7688"
    neo4j_staging_password: str | None = None  # falls back to neo4j_password
    neo4j_database: str = "neo4j"
    # Bolt driver pool (enterprise connection pooling). Neo4j Python driver default is 100.
    neo4j_max_connection_pool_size: int = 50
    neo4j_connection_acquisition_timeout: float = 30.0

    # --- Runtime: cache / concurrency / partition (see docs/16-...) ---
    cache_ttl_ontology_seconds: float = 300.0
    cache_ttl_subgraph_seconds: float = 60.0
    cache_maxsize_subgraph: int = 128
    # Diagnose read-path cache (keyed by message+product+asset+catalog version)
    enable_diagnose_cache: bool = True
    cache_ttl_diagnose_seconds: float = 90.0
    cache_maxsize_diagnose: int = 512
    etl_connector_max_workers: int = 4
    etl_product_batch_size: int = 0  # 0 = no product chunking (single transform batch)
    default_tenant_id: str = "default"

    # Shared multi-replica state (empty REDIS_URL = in-process memory fallback).
    redis_url: str = ""  # e.g. redis://localhost:6379/0
    redis_key_prefix: str = "diagnostics:"
    redis_connect_timeout_seconds: float = 1.0
    redis_socket_timeout_seconds: float = 1.0
    max_concurrent_diagnoses: int = 32  # admission control for /diagnose
    diagnose_lease_seconds: int = 120

    data_file: Path = PROJECT_ROOT / "data" / "synthetic_diagnosis_data.json"
    enterprise_catalog_file: Path = PROJECT_ROOT / "data" / "enterprise_knowledge_catalog.json"
    provenance_manifest_file: Path = PROJECT_ROOT / "data" / "provenance_manifest.json"
    database_path: Path = PROJECT_ROOT / "data" / "diagnostics.db"
    escalations_file: Path = PROJECT_ROOT / "data" / "escalations.json"
    cases_file: Path = PROJECT_ROOT / "data" / "simulated_cases.json"
    lineage_dir: Path = PROJECT_ROOT / "data" / "lineage"
    enterprise_sources_dir: Path = PROJECT_ROOT / "data" / "enterprise_sources"

    mock_enterprise_api_url: str = "http://localhost:8090"
    use_mock_enterprise_apis: bool = True

    crm_api_url: str | None = None
    claims_api_url: str | None = None
    pim_api_url: str | None = None
    fsm_api_url: str | None = None

    api_host: str = "0.0.0.0"
    api_port: int = 8080

    # Admin API protection. When set to a non-empty value, all /admin/* routes
    # require a matching `X-Admin-Token` header. Left empty for the local demo
    # (open access); MUST be set for any non-local deployment.
    admin_api_token: str = ""

    escalation_confidence_threshold: float = 0.65
    # Minimum text→catalog symptom score to admit as *observed* evidence.
    # Do not lower this for demos — weak secondaries invent competing FMs.
    symptom_match_min_score: float = 0.35
    # Secondary symptoms must be at least this fraction of the top match score
    # (in addition to clearing symptom_match_min_score). Prevents floor noise.
    symptom_secondary_relative_floor: float = 0.75
    # Minimum gap between the top two failure-mode posteriors for a "clear
    # leader". Below this the diagnosis is treated as ambiguous (competing
    # failure modes) and routed for human confirmation.
    diagnosis_ambiguity_margin: float = 0.15
    # Production accuracy: never silently diagnose when selected product / CRM
    # asset / free-text appliance signals disagree. Fail closed instead.
    strict_context_consistency: bool = True
    # Keyword hits required in the message to assert a product family signal.
    product_message_signal_min_hits: int = 1
    demo_mode: bool = True
    allow_fixture_fallback: bool = True
    use_hybrid_symptom_matching: bool = True
    enable_provenance: bool = True

    @property
    def production_integrations(self) -> bool:
        """True when mock APIs are off and real connector URLs are expected."""
        return not self.use_mock_enterprise_apis and not self.demo_mode

    @property
    def effective_fixture_fallback(self) -> bool:
        """JSON fixture fallback only when demo mode is active."""
        return self.demo_mode and self.allow_fixture_fallback

    @model_validator(mode="after")
    def _guard_default_password(self) -> "Settings":
        """Fail fast if deployed outside demo mode with the insecure default password."""
        if not self.demo_mode and self.neo4j_password == "password":
            raise ValueError(
                "Refusing to start with the default Neo4j password outside demo_mode. "
                "Set NEO4J_PASSWORD to a real secret via environment/.env."
            )
        return self

    xai_api_key: str | None = None
    openai_api_key: str | None = None
    llm_model: str = "grok-2-latest"

    # --- Guardrails (kickoff prompt §E) ---
    rate_limit_per_minute: int = 60
    enable_pii_redaction: bool = True
    max_response_chars: int = 8000
    max_input_length: int = 2000

    # --- Observability (§H) ---
    log_level: str = "INFO"
    log_json: bool = True
    otel_enabled: bool = False
    otel_service_name: str = "diagnostics-api"
    otel_exporter_otlp_endpoint: str = "http://localhost:4317"
    otel_traces_sampler_arg: float = 1.0
    enable_prometheus_metrics: bool = True

    # --- LLM gateway (INACTIVE by default — §B/§G) ---
    llm_enabled: bool = False
    llm_provider: str = "openai"
    llm_model_alias: str = "diagnosis-rewriter"
    azure_openai_api_key: str | None = None
    azure_openai_endpoint: str | None = None
    azure_openai_api_version: str = "2024-10-21"
    # Cheapest model for the optional schema-bound unstructured extractor
    # (graph/enterprise_pipeline/extractors/llm_graph_extract.py). Kept cheap on
    # purpose — extraction is a bulk/offline enrichment, not the diagnose path.
    llm_extract_model: str = "gpt-4o-mini"

    # --- FinOps (§F) ---
    llm_cost_budget_usd_per_day: float = 5.00

    def resolved_crm_url(self) -> str | None:
        if self.crm_api_url:
            return self.crm_api_url
        return f"{self.mock_enterprise_api_url}/api/crm" if self.use_mock_enterprise_apis else None

    def resolved_pim_url(self) -> str | None:
        if self.pim_api_url:
            return self.pim_api_url
        return f"{self.mock_enterprise_api_url}/api/pim" if self.use_mock_enterprise_apis else None

    def resolved_claims_url(self) -> str | None:
        if self.claims_api_url:
            return self.claims_api_url
        return f"{self.mock_enterprise_api_url}/api/claims" if self.use_mock_enterprise_apis else None

    def resolved_fsm_url(self) -> str | None:
        if self.fsm_api_url:
            return self.fsm_api_url
        return f"{self.mock_enterprise_api_url}/api/fsm" if self.use_mock_enterprise_apis else None


settings = Settings()

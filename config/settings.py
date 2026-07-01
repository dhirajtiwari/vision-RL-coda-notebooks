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

    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"
    neo4j_staging_uri: str = "bolt://localhost:7687"
    neo4j_database: str = "neo4j"

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
    symptom_match_min_score: float = 0.30
    # Minimum gap between the top two failure-mode posteriors for a "clear
    # leader". Below this the diagnosis is treated as ambiguous (competing
    # failure modes) and routed for human confirmation.
    diagnosis_ambiguity_margin: float = 0.15
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

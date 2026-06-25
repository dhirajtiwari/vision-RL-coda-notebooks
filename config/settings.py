from pathlib import Path

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

    escalation_confidence_threshold: float = 0.65
    demo_mode: bool = True
    enable_provenance: bool = True

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
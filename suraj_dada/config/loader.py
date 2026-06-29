import os
from pathlib import Path

import yaml
from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    name: str = "Suraj Dada"
    version: str = "0.1.0"
    debug: bool = True
    environment: str = "development"
    host: str = "127.0.0.1"
    port: int = 8000
    log_level: str = "DEBUG"


class DatabaseRdbmsSettings(BaseSettings):
    url: str = "sqlite+aiosqlite:///./data/suraj_dada.db"
    echo: bool = False
    pool_size: int = 5
    max_overflow: int = 10


class DatabaseVectorSettings(BaseSettings):
    index_path: str = "./data/faiss_index.bin"
    dimension: int = 384
    index_type: str = "Flat"
    metric: str = "cosine"


class DatabaseGraphSettings(BaseSettings):
    data_path: str = "./data/concept_graph.json"


class DatabaseSettings(BaseSettings):
    rdbms: DatabaseRdbmsSettings = DatabaseRdbmsSettings()
    vector: DatabaseVectorSettings = DatabaseVectorSettings()
    graph: DatabaseGraphSettings = DatabaseGraphSettings()


class MasterySettings(BaseSettings):
    weakness_threshold: float = 70.0
    prior_score: float = 60.0
    correct_weight: float = 0.3
    time_weight: float = 0.1
    hint_penalty: float = 0.15
    recurrence_penalty: float = 0.2
    decay_factor: float = 0.95
    bayesian_k: float = 5.0


class RetrievalSettings(BaseSettings):
    top_k_before_reranking: int = 20
    top_k_after_reranking: int = 8
    min_questions: int = 5
    max_questions: int = 8
    semantic_weight: float = 0.4
    metadata_weight: float = 0.2
    concept_expansion_weight: float = 0.2
    mistake_match_weight: float = 0.2
    enable_concept_expansion: bool = True
    enable_student_filter: bool = True
    enable_mistake_matching: bool = True
    enable_reranking: bool = True


class LlmSettings(BaseSettings):
    provider: str = "mock"
    model: str = "mock-generator"
    max_context_tokens: int = 4096
    max_output_tokens: int = 2048
    temperature: float = 0.7
    timeout_seconds: int = 30


class AssessmentSettings(BaseSettings):
    passing_score: int = 40
    max_questions_per_assessment: int = 15
    time_limit_minutes: int = 60


class DiagnosisSettings(BaseSettings):
    enabled: bool = True
    min_confidence: float = 0.4


class AnalyticsSettings(BaseSettings):
    trend_window_days: int = 30


class Settings(BaseSettings):
    app: AppSettings = AppSettings()
    database: DatabaseSettings = DatabaseSettings()
    mastery: MasterySettings = MasterySettings()
    retrieval: RetrievalSettings = RetrievalSettings()
    llm: LlmSettings = LlmSettings()
    assessment: AssessmentSettings = AssessmentSettings()
    diagnosis: DiagnosisSettings = DiagnosisSettings()
    analytics: AnalyticsSettings = AnalyticsSettings()

    model_config = {"env_nested_delimiter": "__"}


_config_cache: Settings | None = None


def load_config(path: str | None = None, env_prefix: str = "SURAJ_") -> Settings:
    global _config_cache
    config_dict = {}
    if path and Path(path).exists():
        with open(path) as f:
            yaml_content = yaml.safe_load(f)
            if yaml_content:
                config_dict = yaml_content

    settings = Settings(**config_dict)
    _config_cache = settings
    return settings


def get_config() -> Settings:
    if _config_cache is None:
        env = os.getenv("SURAJ_ENV", "development")
        config_path = os.getenv("SURAJ_CONFIG_PATH", f"configs/{env}/config.yaml")
        return load_config(config_path)
    return _config_cache


def reload_config(path: str | None = None) -> Settings:
    global _config_cache
    _config_cache = None
    return get_config()

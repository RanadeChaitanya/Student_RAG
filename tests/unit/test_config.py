import pytest

from studob.config.loader import get_config


class TestConfig:
    def test_config_loaded(self):
        cfg = get_config()
        assert cfg is not None
        assert cfg.app.name == "Studob"

    def test_app_version(self):
        cfg = get_config()
        assert cfg.app.version == "0.1.0"

    def test_database_path(self):
        cfg = get_config()
        assert "studob.db" in cfg.database.rdbms.url

    def test_mastery_thresholds(self):
        cfg = get_config()
        assert 0 < cfg.mastery.weakness_threshold <= 100

    def test_retrieval_top_k(self):
        cfg = get_config()
        assert cfg.retrieval.top_k_before_reranking >= 1

    def test_vector_dimension(self):
        cfg = get_config()
        assert cfg.database.vector.dimension > 0

    def test_retrieval_settings(self):
        cfg = get_config()
        assert cfg.retrieval.enable_concept_expansion is True
        assert (
            cfg.retrieval.semantic_weight
            + cfg.retrieval.metadata_weight
            + cfg.retrieval.concept_expansion_weight
            + cfg.retrieval.mistake_match_weight
            == pytest.approx(1.0)
        )

import pytest

from studob.retrieval.reranker import CrossEncoderReranker


@pytest.fixture
def reranker(config):
    return CrossEncoderReranker(config)


@pytest.mark.asyncio
async def test_reranker_returns_top_k(reranker):
    candidates = [
        {
            "id": i,
            "topic": "kinematics",
            "subtopic": "motion in 1d",
            "difficulty": 3,
            "relevance_score": 0.5,
        }
        for i in range(10)
    ]
    result = await reranker.rerank("kinematics", candidates, top_k=3)
    assert len(result) == 3


@pytest.mark.asyncio
async def test_reranker_concept_match_boost(reranker):
    candidates = [
        {
            "id": 1,
            "topic": "kinematics",
            "subtopic": "motion in 1d",
            "difficulty": 3,
            "relevance_score": 0.0,
        },
        {
            "id": 2,
            "topic": "electrostatics",
            "subtopic": "coulombs law",
            "difficulty": 3,
            "relevance_score": 0.0,
        },
    ]
    result = await reranker.rerank("kinematics", candidates, top_k=2)
    assert result[0]["id"] == 1


@pytest.mark.asyncio
async def test_reranker_difficulty_target(reranker):
    candidates = [
        {
            "id": 1,
            "topic": "kinematics",
            "subtopic": "motion in 1d",
            "difficulty": 1,
            "relevance_score": 0.0,
        },
        {
            "id": 2,
            "topic": "kinematics",
            "subtopic": "motion in 1d",
            "difficulty": 3,
            "relevance_score": 0.0,
        },
    ]
    result = await reranker.rerank("kinematics", candidates, top_k=2, target_difficulty=3)
    assert result[0]["id"] == 2


@pytest.mark.asyncio
async def test_reranker_recency_penalty(reranker):
    candidates = [
        {
            "id": 1,
            "topic": "kinematics",
            "subtopic": "motion in 1d",
            "difficulty": 3,
            "relevance_score": 0.5,
            "recency_penalty": 0.0,
        },
        {
            "id": 2,
            "topic": "kinematics",
            "subtopic": "motion in 1d",
            "difficulty": 3,
            "relevance_score": 0.5,
            "recency_penalty": 1.0,
        },
    ]
    result = await reranker.rerank("kinematics", candidates, top_k=2)
    assert result[0]["id"] == 1


@pytest.mark.asyncio
async def test_reranker_combined_score_in_result(reranker):
    candidates = [
        {
            "id": 1,
            "topic": "kinematics",
            "subtopic": "motion in 1d",
            "difficulty": 3,
            "relevance_score": 0.5,
        }
    ]
    result = await reranker.rerank("kinematics", candidates, top_k=1)
    assert "combined_score" in result[0]
    assert isinstance(result[0]["combined_score"], float)


@pytest.mark.asyncio
async def test_reranker_empty_candidates(reranker):
    result = await reranker.rerank("kinematics", [], top_k=5)
    assert result == []

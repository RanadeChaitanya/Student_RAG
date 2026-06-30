import pytest

from studob.retrieval.mistake_matcher import MistakePatternMatcher


@pytest.fixture
def matcher():
    return MistakePatternMatcher()


@pytest.mark.asyncio
async def test_matcher_concept_match_in_topic(matcher):
    candidates = [{"id": 1, "topic": "newtons laws", "subtopic": "third law", "tags": []}]
    result = await matcher.match(candidates, error_category="guessing", concept_tag="newtons-laws")
    assert result[0]["relevance_score"] >= 0.5


@pytest.mark.asyncio
async def test_matcher_concept_match_in_subtopic(matcher):
    candidates = [{"id": 1, "topic": "mechanics", "subtopic": "newtons laws", "tags": []}]
    result = await matcher.match(candidates, error_category="guessing", concept_tag="newtons-laws")
    assert result[0]["relevance_score"] >= 0.5


@pytest.mark.asyncio
async def test_matcher_error_category_match(matcher):
    candidates = [{"id": 1, "topic": "guessing", "subtopic": "mcq strategy", "tags": []}]
    result = await matcher.match(candidates, error_category="guessing", concept_tag="newtons-laws")
    assert result[0]["relevance_score"] >= 0.3


@pytest.mark.asyncio
async def test_matcher_tag_match(matcher):
    candidates = [
        {"id": 1, "topic": "mechanics", "subtopic": "forces", "tags": ["newtons-laws", "guessing"]}
    ]
    result = await matcher.match(candidates, error_category="guessing", concept_tag="newtons-laws")
    assert result[0]["relevance_score"] >= 0.4


@pytest.mark.asyncio
async def test_matcher_no_match(matcher):
    candidates = [{"id": 1, "topic": "electrostatics", "subtopic": "coulombs law", "tags": []}]
    result = await matcher.match(candidates, error_category="guessing", concept_tag="newtons-laws")
    assert result[0]["relevance_score"] == 0.0


@pytest.mark.asyncio
async def test_matcher_score_capped_at_1(matcher):
    candidates = [
        {
            "id": 1,
            "topic": "newtons laws",
            "subtopic": "newtons laws",
            "tags": ["newtons-laws", "guessing"],
        }
    ]
    result = await matcher.match(candidates, error_category="guessing", concept_tag="newtons-laws")
    assert result[0]["relevance_score"] <= 1.0


@pytest.mark.asyncio
async def test_matcher_empty_candidates(matcher):
    result = await matcher.match([], error_category="guessing", concept_tag="newtons-laws")
    assert result == []


@pytest.mark.asyncio
async def test_matcher_case_insensitive(matcher):
    candidates = [{"id": 1, "topic": "Newton's Laws", "subtopic": "Third Law", "tags": []}]
    result = await matcher.match(candidates, error_category="Guessing", concept_tag="Newtons-Laws")
    assert result[0]["relevance_score"] >= 0.5

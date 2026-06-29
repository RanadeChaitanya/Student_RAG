import pytest

from suraj_dada.diagnosis import ErrorTypeRegistry
from suraj_dada.diagnosis.classifier import RootCauseClassifier
from suraj_dada.schemas.diagnosis import ErrorCategory, MistakeDiagnosisRequest


class TestErrorTypeRegistry:
    def test_get_patterns(self):
        registry = ErrorTypeRegistry()
        patterns = registry.get_patterns(ErrorCategory.CONCEPT_MISUNDERSTOOD)
        assert len(patterns) > 0

    def test_get_remediation(self):
        registry = ErrorTypeRegistry()
        steps = registry.get_remediation_strategy(ErrorCategory.FORMULA_RECALL_FAILURE)
        assert len(steps) > 0

    def test_all_categories_have_remediation(self):
        registry = ErrorTypeRegistry()
        for cat in ErrorCategory:
            steps = registry.get_remediation_strategy(cat)
            assert len(steps) > 0, f"No remediation for {cat}"


class TestRootCauseClassifier:
    @pytest.mark.asyncio
    async def test_classify_wrong_answer(self, config):
        classifier = RootCauseClassifier(config)
        req = MistakeDiagnosisRequest(
            student_id="s1",
            question_id=1,
            question_type="mcq",
            response_text="B",
            response_time_seconds=60.0,
            hints_used=2,
            session_id="sess1",
        )
        ctx = {
            "mastery_scores": [{"score": 30.0}],
            "recent_mistakes": [],
            "avg_response_time": 30.0,
            "question_data": {
                "correct_answer": "A",
                "question_type": "mcq",
                "topic": "Physics",
                "subtopic": "Test",
                "difficulty": 3,
            },
        }
        result = await classifier.classify(req, ctx)
        assert result.error_category in list(ErrorCategory)

    @pytest.mark.asyncio
    async def test_classify_correct(self, config):
        classifier = RootCauseClassifier(config)
        req = MistakeDiagnosisRequest(
            student_id="s1",
            question_id=1,
            question_type="mcq",
            response_text="A",
            response_time_seconds=15.0,
            hints_used=0,
            session_id="sess1",
        )
        ctx = {
            "mastery_scores": [],
            "recent_mistakes": [],
            "avg_response_time": 30.0,
            "question_data": {
                "correct_answer": "A",
                "question_type": "mcq",
                "topic": "Physics",
                "subtopic": "Test",
                "difficulty": 2,
            },
        }
        result = await classifier.classify(req, ctx)
        assert result.error_category is not None

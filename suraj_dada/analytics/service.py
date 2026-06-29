from typing import Any

from suraj_dada.analytics.mastery_trends import MasteryTrendService
from suraj_dada.analytics.mistake_patterns import MistakePatternService
from suraj_dada.analytics.session_reports import SessionReportService
from suraj_dada.config.loader import get_config
from suraj_dada.exceptions import AnalyticsError
from suraj_dada.logging_setup import get_logger
from suraj_dada.schemas.analytics import (
    MistakePatternSummary,
    StudentAnalyticsResponse,
)
from suraj_dada.student.mastery import MasteryService

logger = get_logger("analytics.service")


class AnalyticsService:
    def __init__(
        self,
        mastery_trends: MasteryTrendService,
        mistake_patterns: MistakePatternService,
        session_reports: SessionReportService,
        mastery_service: MasteryService,
    ):
        self._mastery_trends = mastery_trends
        self._mistake_patterns = mistake_patterns
        self._session_reports = session_reports
        self._mastery_service = mastery_service
        self._config = get_config()
        self._logger = logger

    async def get_student_analytics(self, student_id: str) -> StudentAnalyticsResponse:
        self._logger.info("Getting student analytics", extra={"student_id": student_id})

        try:
            mastery_summary = await self._mastery_service.get_mastery_summary(student_id)
            trend_points = await self._mastery_trends.get_mastery_trend(
                student_id,
                days=self._config.analytics.trend_window_days,
            )
            patterns = await self._mistake_patterns.get_patterns(student_id)
        except Exception as exc:
            raise AnalyticsError(
                f"Failed to fetch analytics for student {student_id}",
                details={"error": str(exc)},
            ) from exc

        weak_topics = [f"{w.subject}/{w.topic}/{w.subtopic}" for w in mastery_summary.weak_topics]
        strengths = [f"{s.subject}/{s.topic}/{s.subtopic}" for s in mastery_summary.strengths]

        recommendation = self._build_recommendation(weak_topics, patterns)

        response = StudentAnalyticsResponse(
            student_id=student_id,
            overall_mastery=mastery_summary.overall_score,
            mastery_trend=trend_points,
            mistake_patterns=patterns,
            weak_topics=weak_topics,
            strengths=strengths,
            practice_recommendation=recommendation,
        )

        self._logger.info("Student analytics compiled", extra={"student_id": student_id})
        return response

    async def get_session_analytics(self, session_id: str) -> dict[str, Any]:
        self._logger.info("Getting session analytics", extra={"session_id": session_id})
        report = await self._session_reports.generate_report(session_id)
        self._logger.info("Session analytics retrieved", extra={"session_id": session_id})
        return report

    def _build_recommendation(
        self,
        weak_topics: list[str],
        patterns: list[MistakePatternSummary],
    ) -> str:
        if not weak_topics:
            return "Great job! Focus on maintaining your strengths with regular revision."

        top_weak = weak_topics[:3]
        top_pattern = patterns[0].error_category if patterns else "general"

        return (
            f"Focus on practicing {', '.join(top_weak)}. "
            f"Your most common error pattern is '{top_pattern}'. "
            "Try targeted practice with concept review and formula revision."
        )

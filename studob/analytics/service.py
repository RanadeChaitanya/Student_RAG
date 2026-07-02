from typing import Any

from studob.analytics.mastery_trends import MasteryTrendService
from studob.analytics.session_reports import SessionReportService
from studob.confidence import ConfidenceAnalytics
from studob.config.loader import get_config
from studob.exceptions import AnalyticsError
from studob.logging_setup import get_logger
from studob.schemas.analytics import (
    StudentAnalyticsResponse,
)
from studob.student.mastery import MasteryService

logger = get_logger("analytics.service")


class AnalyticsService:
    def __init__(
        self,
        mastery_trends: MasteryTrendService,
        session_reports: SessionReportService,
        mastery_service: MasteryService,
        confidence_analytics: ConfidenceAnalytics | None = None,
    ):
        self._mastery_trends = mastery_trends
        self._session_reports = session_reports
        self._mastery_service = mastery_service
        self._confidence_analytics = confidence_analytics or ConfidenceAnalytics()
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
            qconf_stats = await self._mastery_service.get_qconf_stats(student_id)
        except Exception as exc:
            raise AnalyticsError(
                f"Failed to fetch analytics for student {student_id}",
                details={"error": str(exc)},
            ) from exc

        weak_topics = [f"{w.subtopic} ({w.subject})" for w in mastery_summary.weak_topics]
        strengths = [f"{s.subtopic} ({s.subject})" for s in mastery_summary.strengths]

        recommendation = self._build_recommendation(weak_topics)

        response = StudentAnalyticsResponse(
            student_id=student_id,
            overall_mastery=mastery_summary.overall_score,
            mastery_trend=trend_points,
            weak_topics=weak_topics,
            strengths=strengths,
            practice_recommendation=recommendation,
            average_qconf=qconf_stats.get("average_qconf", 0.0),
            qconf_distribution=qconf_stats.get("qconf_distribution", {"high": 0, "medium": 0, "low": 0}),
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
    ) -> str:
        if not weak_topics:
            return "Great job! Keep up the momentum with regular revision and practice tests."

        top_weak = [w.split(" (")[0] for w in weak_topics[:3]]

        return (
            f"Focus on strengthening {', '.join(top_weak)}. "
            "Review the core concepts and practice similar problems to improve."
        )

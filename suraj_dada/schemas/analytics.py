from datetime import datetime

from pydantic import BaseModel, Field


class MasteryTrendPoint(BaseModel):
    date: datetime = Field(..., description="Date of the data point")
    subject: str = Field(..., description="Subject name")
    topic: str = Field(..., description="Topic name")
    subtopic: str = Field(..., description="Subtopic name")
    score: float = Field(..., description="Mastery score at this point")


class MasteryTrendResponse(BaseModel):
    student_id: str = Field(..., description="Student identifier")
    trend_points: list[MasteryTrendPoint] = Field(
        ..., description="List of mastery data points over time"
    )
    period_days: int = Field(..., description="Number of days covered by the trend")


class MistakePatternSummary(BaseModel):
    error_category: str = Field(..., description="Error category name")
    count: int = Field(..., description="Number of occurrences")
    frequency_percent: float = Field(..., description="Frequency as percentage of total mistakes")
    common_concepts: list[str] = Field(..., description="Concepts most associated with this error")


class StudentAnalyticsResponse(BaseModel):
    student_id: str = Field(..., description="Student identifier")
    overall_mastery: float = Field(..., description="Overall weighted mastery score")
    mastery_trend: list[MasteryTrendPoint] = Field(..., description="Recent mastery trend")
    mistake_patterns: list[MistakePatternSummary] = Field(
        ..., description="Pattern analysis of mistakes"
    )
    weak_topics: list[str] = Field(..., description="Topics identified as weak")
    strengths: list[str] = Field(..., description="Topics identified as strengths")
    practice_recommendation: str = Field(
        ..., description="AI-generated practice recommendation text"
    )

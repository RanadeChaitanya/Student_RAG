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


class StudentAnalyticsResponse(BaseModel):
    student_id: str = Field(..., description="Student identifier")
    overall_mastery: float = Field(..., description="Overall weighted mastery score")
    mastery_trend: list[MasteryTrendPoint] = Field(..., description="Recent mastery trend")
    weak_topics: list[str] = Field(..., description="Topics identified as weak")
    strengths: list[str] = Field(..., description="Topics identified as strengths")
    practice_recommendation: str = Field(
        ..., description="AI-generated practice recommendation text"
    )
    average_qconf: float = Field(
        default=0.0, description="Average Question Confidence Score across recent attempts"
    )
    qconf_distribution: dict = Field(
        default_factory=lambda: {"high": 0, "medium": 0, "low": 0},
        description="Distribution of QConf classifications",
    )

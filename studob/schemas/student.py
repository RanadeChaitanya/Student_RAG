from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class StudentCreate(BaseModel):
    name: str = Field(..., description="Full name of the student")
    grade: str = Field(..., description="Current grade or class (e.g. '12', '12 Pass')")
    exam_target: str | None = Field(None, description="Target exam (e.g. 'JEE Advanced 2026')")
    board: str = Field(..., description="Education board (e.g. 'CBSE', 'State Board')")
    language: str = Field("english", description="Preferred language for instruction")


class StudentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Unique student identifier")
    name: str = Field(..., description="Full name of the student")
    grade: str = Field(..., description="Current grade or class")
    exam_target: str | None = Field(None, description="Target exam")
    board: str = Field(..., description="Education board")
    language: str = Field(..., description="Preferred language")
    created_at: datetime = Field(..., description="Account creation timestamp")


class StudentUpdate(BaseModel):
    name: str | None = Field(None, description="Full name of the student")
    grade: str | None = Field(None, description="Current grade or class")
    exam_target: str | None = Field(None, description="Target exam")
    board: str | None = Field(None, description="Education board")
    language: str | None = Field(None, description="Preferred language")


class MasteryScoreResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    student_id: str = Field(..., description="Student identifier")
    subject: str = Field(
        ..., description="Subject name (e.g. 'Physics', 'Chemistry', 'Mathematics')"
    )
    topic: str = Field(..., description="Topic name")
    subtopic: str = Field(..., description="Subtopic name")
    score: float = Field(..., description="Mastery score (0-100)")
    confidence: float = Field(..., description="Confidence in the score estimate (0-1)")
    attempts: int = Field(..., description="Number of attempts recorded")
    last_updated: datetime = Field(..., description="Last update timestamp")


class WeakTopicInfo(BaseModel):
    subject: str = Field(..., description="Subject name")
    topic: str = Field(..., description="Topic name")
    subtopic: str = Field(..., description="Subtopic name")
    score: float = Field(..., description="Current mastery score")
    gap: float = Field(..., description="Gap from passing threshold (positive = below threshold)")


class MasteryUpdateSignals(BaseModel):
    correctness: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Correctness score (0=wrong, 1=correct)",
    )
    response_time_ratio: float = Field(
        default=1.0,
        ge=0.0,
        description="Ratio of actual to expected response time",
    )
    hints_used_count: int = Field(default=0, ge=0, description="Number of hints used")
    retry_count: int = Field(default=0, ge=0, description="Number of retries")
    recurrence_flag: int = Field(
        default=0,
        ge=0,
        le=1,
        description="Whether same error recurred (0 or 1)",
    )
    subject: str = Field(default="", description="Subject for new mastery records")
    topic: str = Field(default="", description="Topic for new mastery records")
    qconf_score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Question Confidence Score from QConf engine",
    )


class MasterySummaryResponse(BaseModel):
    student_id: str = Field(..., description="Student identifier")
    overall_score: float = Field(
        ..., description="Weighted average mastery score across all subjects"
    )
    subject_breakdown: dict = Field(..., description="Per-subject mastery breakdown")
    weak_topics: list[WeakTopicInfo] = Field(..., description="Topics below weakness threshold")
    strengths: list[WeakTopicInfo] = Field(..., description="Topics identified as strengths")

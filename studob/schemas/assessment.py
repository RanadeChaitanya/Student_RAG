from datetime import datetime

from pydantic import BaseModel, Field


class AssessmentCreate(BaseModel):
    student_id: str = Field(..., description="Student identifier")
    subject: str = Field(..., description="Subject for the assessment")
    topic: str | None = Field(
        None, description="Topic filter; if omitted auto-selects from subject"
    )
    question_ids: list[int] | None = Field(
        None, description="Optional explicit question IDs; auto-selected if omitted"
    )
    time_limit_minutes: int = Field(60, ge=1, description="Time limit in minutes")


class AssessmentResponse(BaseModel):
    id: str = Field(..., description="Assessment identifier (session UUID)")
    student_id: str = Field(..., description="Student identifier")
    subject: str = Field(..., description="Subject name")
    status: str = Field(..., description="Assessment status: 'pending', 'in_progress', 'completed'")
    started_at: datetime = Field(..., description="Assessment start timestamp")
    ended_at: datetime | None = Field(None, description="Assessment end timestamp")
    questions: list[dict] = Field(..., description="List of questions in the assessment")
    score: int = Field(..., description="Raw score")
    results: dict = Field(..., description="Detailed results breakdown")


class AssessmentResult(BaseModel):
    assessment_id: str = Field(..., description="Assessment identifier (session UUID)")
    student_id: str = Field(..., description="Student identifier")
    total_questions: int = Field(..., description="Total number of questions")
    attempted: int = Field(..., description="Number of questions attempted")
    correct: int = Field(..., description="Number of correct answers")
    incorrect: int = Field(..., description="Number of incorrect answers")
    score_percentage: float = Field(..., description="Score as percentage")
    topic_breakdown: dict = Field(..., description="Per-topic performance breakdown")
    diagnosis_results: list[dict] = Field(..., description="Diagnosis results per incorrect answer")

from datetime import datetime

from pydantic import BaseModel, Field


class PracticeSessionRequest(BaseModel):
    student_id: str = Field(..., description="Student identifier")
    session_id: str = Field(..., description="Session identifier for tracking")
    target_concept: str = Field(..., description="Concept tag to focus practice on")
    error_category: str = Field(..., description="Error category to address")
    difficulty_band: str = Field(
        "adaptive", description="Difficulty band: 'easy', 'medium', 'hard', or 'adaptive'"
    )
    question_count: int = Field(5, ge=1, le=20, description="Number of questions to generate")


class PracticeQuestion(BaseModel):
    id: int = Field(..., description="Question identifier")
    question_text: str = Field(..., description="The question content")
    options: dict | None = Field(None, description="Answer options if applicable")
    difficulty: int = Field(..., description="Difficulty level (1-5)")
    hint: str | None = Field(None, description="Optional hint for the question")
    concept_reference: str | None = Field(
        None, description="Reference to the concept being practiced"
    )


class PracticeSessionResponse(BaseModel):
    practice_session_id: str = Field(..., description="Practice session identifier")
    student_id: str = Field(..., description="Student identifier")
    target_concept: str = Field(..., description="Target concept for this session")
    questions: list[PracticeQuestion] = Field(..., description="List of practice questions")
    difficulty_progression: str = Field(..., description="Difficulty progression strategy used")
    created_at: datetime = Field(..., description="Session creation timestamp")


class PracticeSessionResult(BaseModel):
    practice_session_id: str = Field(..., description="Practice session identifier")
    student_id: str = Field(..., description="Student identifier")
    attempts: list[dict] = Field(
        ..., description="List of attempt results with correctness and timing"
    )
    mastery_delta: float = Field(..., description="Change in mastery score after this session")
    weak_topics_remaining: list[str] = Field(
        ..., description="Topics still below weakness threshold"
    )

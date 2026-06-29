from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SessionCreate(BaseModel):
    student_id: str = Field(..., description="Student identifier")
    session_type: str = Field(
        ..., description="Type of session (e.g. 'practice', 'assessment', 'revision')"
    )


class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Session identifier")
    student_id: str = Field(..., description="Student identifier")
    session_type: str = Field(..., description="Type of session")
    started_at: datetime = Field(..., description="Session start timestamp")
    ended_at: datetime | None = Field(None, description="Session end timestamp")
    questions_count: int = Field(..., description="Number of questions attempted")
    correct_count: int = Field(..., description="Number of correct answers")
    mastery_delta: float = Field(..., description="Change in mastery during session")


class AttemptCreate(BaseModel):
    question_id: int = Field(..., description="Question identifier")
    question_type: str = Field(..., description="Type of question ('app' or 'test')")
    is_correct: bool = Field(..., description="Whether the answer was correct")
    response_time_seconds: float = Field(..., description="Time taken to respond in seconds")
    hints_used: int = Field(0, description="Number of hints used")
    retry_count: int = Field(0, description="Number of retries")
    session_id: str = Field(..., description="Session identifier")


class AttemptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Attempt identifier")
    question_id: int = Field(..., description="Question identifier")
    is_correct: bool = Field(..., description="Whether the answer was correct")
    response_time_seconds: float = Field(..., description="Response time in seconds")
    hints_used: int = Field(..., description="Number of hints used")
    retry_count: int = Field(..., description="Number of retries")
    answered_at: datetime = Field(..., description="Timestamp of the attempt")
    session_id: str | None = Field(None, description="Session identifier")

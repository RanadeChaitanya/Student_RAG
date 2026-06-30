from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class QuestionBase(BaseModel):
    subject: str = Field(
        ..., description="Subject name (e.g. 'Physics', 'Chemistry', 'Mathematics')"
    )
    topic: str = Field(..., description="Topic name")
    subtopic: str = Field(..., description="Subtopic name")
    difficulty: int = Field(
        ..., ge=1, le=5, description="Difficulty level from 1 (easiest) to 5 (hardest)"
    )
    question_type: str = Field(
        ..., description="Type of question (e.g. 'mcq', 'numerical', 'assertion_reason')"
    )
    question_text: str = Field(..., description="The question content text")
    options: dict | None = Field(None, description="JSON object of answer options if applicable")
    correct_answer: str = Field(..., description="The correct answer string")
    explanation: str = Field(..., description="Explanation for the answer")
    tags: list[str] | None = Field(None, description="List of tags for categorization")


class AppQuestionCreate(QuestionBase):
    source: str = Field("app", description="Source of the question")
    is_active: bool = Field(True, description="Whether the question is active")


class AppQuestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Question identifier")
    subject: str = Field(..., description="Subject name")
    topic: str = Field(..., description="Topic name")
    subtopic: str = Field(..., description="Subtopic name")
    difficulty: int = Field(..., description="Difficulty level")
    question_type: str = Field(..., description="Type of question")
    question_text: str = Field(..., description="The question content text")
    options: dict | None = Field(None, description="Answer options")
    correct_answer: str = Field(..., description="The correct answer")
    explanation: str = Field(..., description="Explanation")
    tags: list[str] | None = Field(None, description="Tags")
    source: str = Field(..., description="Source of the question")
    is_active: bool = Field(..., description="Active status")
    created_at: datetime = Field(..., description="Creation timestamp")


class TestQuestionCreate(QuestionBase):
    year: int = Field(..., description="Exam year")
    exam_type: str = Field(..., description="Type of exam (e.g. 'JEE Main', 'JEE Advanced')")
    is_active: bool = Field(True, description="Whether the question is active")


class TestQuestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Question identifier")
    subject: str = Field(..., description="Subject name")
    topic: str = Field(..., description="Topic name")
    subtopic: str = Field(..., description="Subtopic name")
    difficulty: int = Field(..., description="Difficulty level")
    question_type: str = Field(..., description="Type of question")
    question_text: str = Field(..., description="The question content text")
    options: dict | None = Field(None, description="Answer options")
    correct_answer: str = Field(..., description="The correct answer")
    explanation: str = Field(..., description="Explanation")
    tags: list[str] | None = Field(None, description="Tags")
    year: int = Field(..., description="Exam year")
    exam_type: str = Field(..., description="Exam type")
    is_active: bool = Field(..., description="Active status")
    created_at: datetime = Field(..., description="Creation timestamp")


class QuestionFilter(BaseModel):
    subject: str | None = Field(None, description="Filter by subject")
    topic: str | None = Field(None, description="Filter by topic")
    subtopic: str | None = Field(None, description="Filter by subtopic")
    difficulty_min: int | None = Field(None, ge=1, le=5, description="Minimum difficulty")
    difficulty_max: int | None = Field(None, ge=1, le=5, description="Maximum difficulty")
    question_type: str | None = Field(None, description="Filter by question type")
    tags: list[str] | None = Field(None, description="Filter by tags (intersection)")


class MetadataFilterResult(BaseModel):
    question_ids: list[int] = Field(..., description="List of matching question IDs")
    total_count: int = Field(..., description="Total count of matching questions")
    filter_criteria: QuestionFilter = Field(..., description="The filter criteria used")

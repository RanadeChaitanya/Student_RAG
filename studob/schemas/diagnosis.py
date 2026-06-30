from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class ErrorCategory(StrEnum):
    CONCEPT_MISUNDERSTOOD = "concept_misunderstood"
    FORMULA_RECALL_FAILURE = "formula_recall_failure"
    CALCULATION_ERROR = "calculation_error"
    SIGN_UNIT_ERROR = "sign_unit_error"
    MISREAD_QUESTION = "misread_question"
    GUESSING = "guessing"
    CARELESS_ARITHMETIC = "careless_arithmetic"
    FORMULA_ERROR = "formula_error"
    SIGN_ERROR = "sign_error"
    UNIT_ERROR = "unit_error"
    READING_ERROR = "reading_error"


class MistakeDiagnosisRequest(BaseModel):
    student_id: str = Field(..., description="Student identifier")
    question_id: int = Field(..., description="Question identifier")
    question_type: str = Field(..., description="Type of question ('app' or 'test')")
    response_text: str = Field(..., description="The student's response text")
    response_time_seconds: float = Field(..., description="Time taken to respond")
    hints_used: int = Field(0, description="Number of hints used")
    session_id: str | None = Field(None, description="Session identifier")


class MistakeDiagnosisResponse(BaseModel):
    student_id: str = Field(..., description="Student identifier")
    question_id: int = Field(..., description="Question identifier")
    error_category: ErrorCategory = Field(..., description="Classified error category")
    concept_tag: str = Field(..., description="The concept tag associated with the mistake")
    confidence: float = Field(..., description="Confidence in the diagnosis (0-1)")
    diagnosis_detail: dict = Field(..., description="Additional diagnosis details")
    suggested_remediation: list[str] = Field(..., description="Suggested remediation steps")


class MistakeRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Record identifier")
    student_id: str = Field(..., description="Student identifier")
    question_id: int | None = Field(None, description="Question identifier")
    session_id: str | None = Field(None, description="Session identifier")
    error_category: ErrorCategory = Field(..., description="Classified error category")
    concept_tag: str = Field(..., description="The concept tag")
    confidence: float = Field(..., description="Confidence score")
    created_at: datetime = Field(..., description="Record creation timestamp")

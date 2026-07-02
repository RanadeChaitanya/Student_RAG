from pydantic import BaseModel, Field


class ConfidenceFactors(BaseModel):
    correctness_signal: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Correctness signal (1.0 correct, 0.0 wrong)",
    )
    time_factor: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Normalized response time factor"
    )
    hint_penalty: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Penalty from hint usage"
    )
    retry_penalty: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Penalty from retries"
    )
    difficulty_boost: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Boost for correct answers on hard questions"
    )
    recurrence_penalty: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Penalty if same error recurred"
    )


class QConfResult(BaseModel):
    score: float = Field(
        ..., ge=0.0, le=1.0, description="Question Confidence Score (0-1)"
    )
    factors: ConfidenceFactors = Field(
        ..., description="Detailed breakdown of contributing factors"
    )
    classification: str = Field(
        ..., description="Category: 'high', 'medium', or 'low'"
    )

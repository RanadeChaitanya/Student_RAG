from pydantic import BaseModel, Field


class ConfidenceWeights(BaseModel):
    correctness: float = Field(default=0.55, ge=0, le=1)
    response_time: float = Field(default=0.15, ge=0, le=1)
    hints: float = Field(default=0.10, ge=0, le=1)
    retries: float = Field(default=0.08, ge=0, le=1)
    difficulty: float = Field(default=0.12, ge=0, le=1)
    recurrence: float = Field(default=0.0, ge=0, le=1)


class ConfidenceThresholds(BaseModel):
    high_confidence: float = Field(default=0.65)
    medium_confidence: float = Field(default=0.35)
    low_confidence: float = Field(default=0.0)


class ExpectedTimeParams(BaseModel):
    base_seconds: float = Field(default=15.0)
    per_difficulty: float = Field(default=10.0)


class PenaltyParams(BaseModel):
    max_hints: int = Field(default=3)
    hint_penalty_per_unit: float = Field(default=0.08)
    max_retries: int = Field(default=3)
    retry_penalty_per_unit: float = Field(default=0.05)
    recurrence_penalty: float = Field(default=0.20)


DEFAULT_WEIGHTS = ConfidenceWeights()
DEFAULT_THRESHOLDS = ConfidenceThresholds()
DEFAULT_TIME_PARAMS = ExpectedTimeParams()
DEFAULT_PENALTIES = PenaltyParams()

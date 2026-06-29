from pydantic import BaseModel, Field


class RetrievalRequest(BaseModel):
    student_id: str = Field(..., description="Student identifier")
    concept_tag: str = Field(..., description="Concept tag to retrieve questions for")
    error_category: str = Field(..., description="Error category to target")
    session_id: str = Field(..., description="Current session identifier")
    learning_objective: str | None = Field(
        None, description="Optional learning objective to guide retrieval"
    )


class RetrievedItem(BaseModel):
    question_id: int = Field(..., description="Question identifier")
    subject: str = Field(..., description="Subject name")
    topic: str = Field(..., description="Topic name")
    subtopic: str = Field(..., description="Subtopic name")
    difficulty: int = Field(..., description="Difficulty level (1-5)")
    question_text: str = Field(..., description="The question content")
    options: dict | None = Field(None, description="Answer options")
    explanation: str = Field(..., description="Answer explanation")
    relevance_score: float = Field(..., description="Computed relevance score")
    source: str = Field(..., description="Source of the question")


class ContextPackage(BaseModel):
    student_state: dict = Field(..., description="Current student mastery state snapshot")
    mistake_diagnosis: dict = Field(..., description="Most recent mistake diagnosis context")
    learning_objective: str = Field(..., description="Current learning objective")
    retrieved_questions: list[RetrievedItem] = Field(..., description="Retrieved question items")
    concept_notes: list[str] = Field(..., description="Relevant concept notes")
    formulas: list[str] = Field(..., description="Relevant formulas")
    misconceptions: list[str] = Field(..., description="Common misconceptions to watch for")
    session_memory: dict = Field(..., description="Session-level memory context")

class SurajDadaError(Exception):
    """Base exception for all Suraj Dada errors."""

    def __init__(self, message: str, code: str = "INTERNAL_ERROR", details: dict | None = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


class ConfigurationError(SurajDadaError):
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message, code="CONFIGURATION_ERROR", details=details)


class DatabaseError(SurajDadaError):
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message, code="DATABASE_ERROR", details=details)


class NotFoundError(SurajDadaError):
    def __init__(self, resource_type: str, resource_id: str, details: dict | None = None):
        super().__init__(
            f"{resource_type} not found: {resource_id}",
            code="NOT_FOUND",
            details={"resource_type": resource_type, "resource_id": resource_id, **(details or {})},
        )


class ValidationError(SurajDadaError):
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message, code="VALIDATION_ERROR", details=details)


class MasteryError(SurajDadaError):
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message, code="MASTERY_ERROR", details=details)


class RetrievalError(SurajDadaError):
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message, code="RETRIEVAL_ERROR", details=details)


class LlmError(SurajDadaError):
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message, code="LLM_ERROR", details=details)


class EmbeddingError(SurajDadaError):
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message, code="EMBEDDING_ERROR", details=details)


class AssessmentError(SurajDadaError):
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message, code="ASSESSMENT_ERROR", details=details)


class DiagnosisError(SurajDadaError):
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message, code="DIAGNOSIS_ERROR", details=details)


class AnalyticsError(SurajDadaError):
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message, code="ANALYTICS_ERROR", details=details)

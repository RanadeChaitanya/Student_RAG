class StudobError(Exception):
    """Base exception for all Studob errors."""

    def __init__(self, message: str, code: str = "INTERNAL_ERROR", details: dict | None = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


class ConfigurationError(StudobError):
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message, code="CONFIGURATION_ERROR", details=details)


class DatabaseError(StudobError):
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message, code="DATABASE_ERROR", details=details)


class NotFoundError(StudobError):
    def __init__(self, resource_type: str, resource_id: str, details: dict | None = None):
        super().__init__(
            f"{resource_type} not found: {resource_id}",
            code="NOT_FOUND",
            details={"resource_type": resource_type, "resource_id": resource_id, **(details or {})},
        )


class DomainValidationError(StudobError):
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message, code="VALIDATION_ERROR", details=details)


class MasteryError(StudobError):
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message, code="MASTERY_ERROR", details=details)


class RetrievalError(StudobError):
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message, code="RETRIEVAL_ERROR", details=details)


class ContentError(StudobError):
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message, code="CONTENT_ERROR", details=details)


class EmbeddingError(StudobError):
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message, code="EMBEDDING_ERROR", details=details)


class AssessmentError(StudobError):
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message, code="ASSESSMENT_ERROR", details=details)


class DiagnosisError(StudobError):
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message, code="DIAGNOSIS_ERROR", details=details)


class AnalyticsError(StudobError):
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message, code="ANALYTICS_ERROR", details=details)

from studob.logging_setup import get_logger
from studob.schemas.diagnosis import ErrorCategory

logger = get_logger("diagnosis.error_types")


class ErrorTypeRegistry:
    def __init__(self):
        self._registry = {
            ErrorCategory.CONCEPT_MISUNDERSTOOD: {
                "patterns": [
                    "doesn't understand",
                    "not clear about",
                    "confused between",
                    "misconception",
                    "fundamental gap",
                ],
                "description": (
                    "The student lacks understanding of the core concept "
                    "required to solve the problem."
                ),
                "remediation": [
                    "Review foundational concepts related to this topic",
                    "Watch concept video lessons and attempt guided examples",
                    "Practice basic-level problems before moving to advanced",
                ],
            },
            ErrorCategory.FORMULA_RECALL_FAILURE: {
                "patterns": [
                    "formula",
                    "equation",
                    "theorem",
                    "law",
                    "rule",
                    "forgot the formula",
                    "incorrect formula",
                ],
                "description": (
                    "The student knows the concept but failed to recall "
                    "the correct formula or equation."
                ),
                "remediation": [
                    "Create a formula sheet for quick revision",
                    "Practice formula application in varied contexts",
                    "Use mnemonic techniques to remember key formulas",
                ],
            },
            ErrorCategory.CALCULATION_ERROR: {
                "patterns": [
                    "calculation",
                    "computation",
                    "arithmetic",
                    "numeric",
                    "minor error",
                    "off by",
                ],
                "description": (
                    "The student made an error during numeric computation "
                    "despite understanding the concept."
                ),
                "remediation": [
                    "Practice mental math and approximation techniques",
                    "Double-check calculations step by step",
                    "Use rough work sections effectively",
                ],
            },
            ErrorCategory.SIGN_UNIT_ERROR: {
                "patterns": [
                    "sign",
                    "negative",
                    "positive",
                    "unit",
                    "dimension",
                    "direction",
                    "vector",
                ],
                "description": (
                    "The student misapplied a sign convention or used "
                    "incorrect units in the answer."
                ),
                "remediation": [
                    "Pay attention to sign conventions in the problem context",
                    "Always include units in intermediate steps",
                    "Verify final answer dimensions match expected units",
                ],
            },
            ErrorCategory.MISREAD_QUESTION: {
                "patterns": [
                    "misread",
                    "overlooked",
                    "missed",
                    "misunderstood the question",
                    "read incorrectly",
                ],
                "description": (
                    "The student misinterpreted or missed key details in the question statement."
                ),
                "remediation": [
                    "Practice active reading: underline key terms and numbers",
                    "Rephrase the question in your own words before solving",
                    "Allocate the first minute to understand the problem fully",
                ],
            },
            ErrorCategory.GUESSING: {
                "patterns": [
                    "guess",
                    "random",
                    "not sure",
                    "blindly",
                    "no idea",
                ],
                "description": ("The student answered without sufficient reasoning or knowledge."),
                "remediation": [
                    "Use elimination technique to narrow down options",
                    "Attempt partial solutions to gain partial credit",
                    "Review the topic thoroughly before attempting similar problems",
                ],
            },
            ErrorCategory.CARELESS_ARITHMETIC: {
                "patterns": [
                    "careless",
                    "silly mistake",
                    "stupid error",
                    "oversight",
                    "simple error",
                ],
                "description": (
                    "The student made an avoidable arithmetic slip despite knowing the material."
                ),
                "remediation": [
                    "Slow down and verify each arithmetic step",
                    "Practice timed arithmetic drills for accuracy",
                    "Develop a habit of re-checking answers before submission",
                ],
            },
        }

    def get_patterns(self, category: ErrorCategory) -> list[str]:
        entry = self._registry.get(category)
        if entry is None:
            logger.warning("Unknown error category requested", extra={"category": category.value})
            return []
        return list(entry["patterns"])

    def get_remediation_strategy(self, category: ErrorCategory) -> str:
        entry = self._registry.get(category)
        if entry is None:
            logger.warning("Unknown error category requested", extra={"category": category.value})
            return "Review the topic and practice more problems."
        return "\n".join(f"- {s}" for s in entry["remediation"])

    def get_description(self, category: ErrorCategory) -> str:
        entry = self._registry.get(category)
        if entry is None:
            logger.warning("Unknown error category requested", extra={"category": category.value})
            return ""
        return entry["description"]

    def get_all_categories(self) -> list[dict]:
        return [
            {
                "category": cat.value,
                "description": info["description"],
                "remediation": info["remediation"],
                "patterns": info["patterns"],
            }
            for cat, info in self._registry.items()
        ]

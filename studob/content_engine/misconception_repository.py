

from studob.logging_setup import get_logger

logger = get_logger("content_engine.misconception_repository")

COMMON_MISTAKES: dict[str, list[dict[str, str]]] = {
    "algebra": [
        {"pattern": "sign_error", "description": "Sign error when moving terms across equals", "advice": "Always double-check signs when transposing terms."},
        {"pattern": "distribution_error", "description": "Incorrect distribution of negative signs", "advice": "Remember: -(a + b) = -a - b, not -a + b."},
    ],
    "calculus": [
        {"pattern": "chain_rule", "description": "Forgot to apply chain rule in differentiation", "advice": "When differentiating composite functions, always multiply by the derivative of the inner function."},
        {"pattern": "integration_const", "description": "Forgot the constant of integration", "advice": "Always add + C after indefinite integration."},
    ],
    "trigonometry": [
        {"pattern": "identities", "description": "Applied wrong trigonometric identity", "advice": "Create a quick reference sheet of the most common identities."},
    ],
    "physics_mechanics": [
        {"pattern": "free_body", "description": "Missing forces in free body diagram", "advice": "List all forces: gravity, normal, friction, tension, applied, and air resistance."},
        {"pattern": "direction_sign", "description": "Incorrect sign convention for direction", "advice": "Choose a consistent sign convention and stick with it throughout the problem."},
    ],
    "chemistry": [
        {"pattern": "mole_ratio", "description": "Incorrect mole ratio from balanced equation", "advice": "Always write the balanced equation first, then identify the coefficients."},
        {"pattern": "unit_conversion", "description": "Unit conversion error", "advice": "Track units throughout the calculation — they should cancel out to give the correct result."},
    ],
}


class MisconceptionRepository:
    def __init__(self) -> None:
        self._misconceptions: dict[int, list[dict[str, str]]] = {}

    def get_misconceptions_for_concept(self, concept_tag: str) -> list[dict[str, str]]:
        for key, mistakes in COMMON_MISTAKES.items():
            if key.lower() in concept_tag.lower():
                return mistakes
        pattern_key = self._infer_concept_category(concept_tag)
        return COMMON_MISTAKES.get(pattern_key, [])

    def _infer_concept_category(self, concept_tag: str) -> str:
        tag_lower = concept_tag.lower()
        if any(w in tag_lower for w in ["derivative", "integral", "limit", "calculus", "differentiation", "integration"]):
            return "calculus"
        if any(w in tag_lower for w in ["algebra", "equation", "polynomial", "quadratic", "linear"]):
            return "algebra"
        if any(w in tag_lower for w in ["trig", "sin", "cos", "tan", "angle"]):
            return "trigonometry"
        if any(w in tag_lower for w in ["force", "motion", "mechanics", "newton", "kinematics"]):
            return "physics_mechanics"
        if any(w in tag_lower for w in ["mole", "reaction", "stoichiometry", "chemical", "compound"]):
            return "chemistry"
        return "algebra"

    def store_misconception(self, question_id: int, misconceptions: list[dict[str, str]]) -> None:
        self._misconceptions[question_id] = misconceptions

    def get_misconceptions_for_question(self, question_id: int) -> list[dict[str, str]]:
        return self._misconceptions.get(question_id, [])

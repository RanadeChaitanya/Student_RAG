

from studob.logging_setup import get_logger

logger = get_logger("content_engine.formula_repository")

FORMULA_SHEETS: dict[str, list[dict[str, str]]] = {
    "algebra": [
        {"name": "Quadratic Formula", "formula": "x = (-b ± √(b² - 4ac)) / 2a", "when_to_use": "Solving ax² + bx + c = 0"},
        {"name": "Arithmetic Progression", "formula": "aₙ = a + (n-1)d", "when_to_use": "nth term of arithmetic sequence"},
        {"name": "Geometric Progression", "formula": "aₙ = arⁿ⁻¹", "when_to_use": "nth term of geometric sequence"},
    ],
    "calculus": [
        {"name": "Derivative Power Rule", "formula": "d/dx(xⁿ) = nxⁿ⁻¹", "when_to_use": "Differentiating power functions"},
        {"name": "Chain Rule", "formula": "dy/dx = dy/du · du/dx", "when_to_use": "Differentiating composite functions"},
        {"name": "Integration Power Rule", "formula": "∫xⁿdx = xⁿ⁺¹/(n+1) + C, n ≠ -1", "when_to_use": "Integrating power functions"},
        {"name": "Fundamental Theorem", "formula": "∫ₐᵇ f(x)dx = F(b) - F(a)", "when_to_use": "Evaluating definite integrals"},
    ],
    "trigonometry": [
        {"name": "Pythagorean Identity", "formula": "sin²θ + cos²θ = 1", "when_to_use": "Simplifying trigonometric expressions"},
        {"name": "Sine Rule", "formula": "a/sin A = b/sin B = c/sin C", "when_to_use": "Solving non-right triangles"},
        {"name": "Cosine Rule", "formula": "c² = a² + b² - 2ab cos C", "when_to_use": "Finding sides or angles in non-right triangles"},
    ],
    "physics_mechanics": [
        {"name": "Newton's Second Law", "formula": "F = ma", "when_to_use": "Relating force, mass, and acceleration"},
        {"name": "Kinematic Equation", "formula": "v² = u² + 2as", "when_to_use": "Motion with constant acceleration"},
        {"name": "Work-Energy Theorem", "formula": "W = ΔKE = ½mv² - ½mu²", "when_to_use": "Relating work to kinetic energy change"},
    ],
}


class FormulaRepository:
    def get_formulas_for_concept(self, concept_tag: str) -> list[dict[str, str]]:
        for key, formulas in FORMULA_SHEETS.items():
            if key.lower() in concept_tag.lower():
                return formulas
        inferred = self._infer_concept_category(concept_tag)
        return FORMULA_SHEETS.get(inferred, [])

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
        return "algebra"

    def get_all_formula_categories(self) -> list[str]:
        return list(FORMULA_SHEETS.keys())

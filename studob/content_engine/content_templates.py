HINT_TEMPLATES = {
    1: "Think about the core concept involved: {concept_hint}",
    2: "Break the problem down: {step_hint}",
    3: "Almost there! Remember: {final_hint}",
}

EXPLANATION_TEMPLATES = {
    "quick": "**Quick Explanation:** {content}",
    "detailed": "## Detailed Explanation\n\n{content}",
    "formula_derivation": "## Formula Derivation\n\n{content}",
    "worked_example": "## Worked Example\n\n{content}",
    "revision_summary": "### Revision Summary\n\n{content}",
    "exam_strategy": "### Exam Strategy\n\n{content}",
}

SOLUTION_TEMPLATE = "### Step-by-Step Solution\n\n{steps}"

MISCONCEPTION_TEMPLATE = (
    "### Common Mistake: {mistake}\n\n"
    "**Advice:** {advice}"
)

FORMULA_TEMPLATE = (
    "**{name}**\n\n"
    "{formula}\n\n"
    "*Use when:* {when_to_use}"
)


def render_hint(hint_text: str, level: int) -> str:
    return f"**Hint {level}:** {hint_text}"


def render_explanation(content: str, variant: str) -> str:
    template = EXPLANATION_TEMPLATES.get(variant, EXPLANATION_TEMPLATES["detailed"])
    return template.format(content=content)


def render_solution(steps: list[str]) -> str:
    numbered = "\n".join(f"{i + 1}. {step}" for i, step in enumerate(steps))
    return SOLUTION_TEMPLATE.format(steps=numbered)


def render_misconception(mistake: str, advice: str) -> str:
    return MISCONCEPTION_TEMPLATE.format(mistake=mistake, advice=advice)


def render_formula(name: str, formula: str, when_to_use: str) -> str:
    return FORMULA_TEMPLATE.format(name=name, formula=formula, when_to_use=when_to_use)

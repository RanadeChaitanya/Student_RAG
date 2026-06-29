from dataclasses import dataclass, field


@dataclass
class ConceptNode:
    id: str
    subject: str
    topic: str
    subtopic: str
    display_name: str
    difficulty: int
    prerequisites: list[str] = field(default_factory=list)


@dataclass
class ConceptEdge:
    from_id: str
    to_id: str
    relationship: str  # "prerequisite", "leads_to", "related"

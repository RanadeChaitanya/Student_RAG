from suraj_dada.config.loader import Settings
from suraj_dada.exceptions import NotFoundError
from suraj_dada.graph.store import ConceptGraphStore
from suraj_dada.logging_setup import get_logger

logger = get_logger("graph.service")


class ConceptGraphService:
    def __init__(self, store: ConceptGraphStore, config: Settings):
        self._store = store
        self._config = config

    async def get_concept(self, concept_id: str) -> dict:
        try:
            node = self._store.get_node(concept_id)
        except KeyError as e:
            raise NotFoundError("ConceptNode", concept_id) from e
        return {
            "id": node.id,
            "subject": node.subject,
            "topic": node.topic,
            "subtopic": node.subtopic,
            "display_name": node.display_name,
            "difficulty": node.difficulty,
            "prerequisites": node.prerequisites,
            "dependents": [n.id for n in self._store.get_dependents(concept_id)],
            "siblings": [
                {"id": n.id, "display_name": n.display_name}
                for n in self._store.get_siblings(concept_id)
            ],
        }

    async def get_prerequisite_chain(self, concept_id: str) -> list[dict]:
        try:
            self._store.get_node(concept_id)
        except KeyError as e:
            raise NotFoundError("ConceptNode", concept_id) from e
        chain = self._store.traverse_upstream(concept_id)
        return [
            {
                "id": n.id,
                "display_name": n.display_name,
                "subject": n.subject,
                "topic": n.topic,
                "subtopic": n.subtopic,
                "difficulty": n.difficulty,
            }
            for n in chain
        ]

    async def expand_concepts(self, concept_ids: list[str]) -> list[dict]:
        results = []
        seen: set[str] = set()
        for cid in concept_ids:
            try:
                node = self._store.get_node(cid)
            except KeyError:
                continue
            if cid not in seen:
                seen.add(cid)
                results.append(
                    {
                        "id": node.id,
                        "display_name": node.display_name,
                        "subject": node.subject,
                        "topic": node.topic,
                        "subtopic": node.subtopic,
                        "difficulty": node.difficulty,
                    }
                )
            for related in self._store.get_related_concepts(cid, depth=1):
                if related.id not in seen:
                    seen.add(related.id)
                    results.append(
                        {
                            "id": related.id,
                            "display_name": related.display_name,
                            "subject": related.subject,
                            "topic": related.topic,
                            "subtopic": related.subtopic,
                            "difficulty": related.difficulty,
                        }
                    )
        return results

    async def find_gaps(self, student_id: str, mastery_service) -> list[dict]:
        weak = await mastery_service.identify_weak_topics(student_id)
        gaps = []
        for w in weak:
            try:
                nodes = self._store.search_nodes(w.subtopic)
                for n in nodes:
                    prereqs = self._store.traverse_upstream(n.id)
                    gaps.append(
                        {
                            "student_id": student_id,
                            "weak_concept_id": n.id,
                            "weak_concept_name": n.display_name,
                            "current_score": w.score,
                            "gap": w.gap,
                            "prerequisite_chain": [
                                {"id": p.id, "display_name": p.display_name} for p in prereqs
                            ],
                        }
                    )
            except Exception:
                logger.warning("Could not find concept in graph", extra={"subtopic": w.subtopic})
        return gaps

    async def get_misconceptions(self, concept_id: str) -> list[dict]:
        try:
            self._store.get_node(concept_id)
        except KeyError as e:
            raise NotFoundError("ConceptNode", concept_id) from e

        try:
            from sqlalchemy import select

            from suraj_dada.database.engine import AsyncSession
            from suraj_dada.database.models import Misconception

            async with self._store._session_factory() as session:
                session: AsyncSession
                result = await session.execute(
                    select(Misconception).where(Misconception.concept_id == int(concept_id))
                )
                misconceptions = result.scalars().all()
                return [
                    {
                        "id": m.id,
                        "description": m.description,
                        "error_pattern": m.error_pattern,
                        "related_error_categories": m.related_error_categories or [],
                    }
                    for m in misconceptions
                ]
        except (ImportError, AttributeError):
            logger.warning("Cannot query misconceptions - no DB session available")
            return []

from suraj_dada.logging_setup import get_logger

logger = get_logger("diagnosis.concept_tagger")


class ConceptTagger:
    def __init__(self, question_bank_service):
        self._service = question_bank_service

    async def extract_concept_tags(self, question_id: str) -> list[str]:
        try:
            question = await self._service.get_question(question_id)
        except Exception:
            logger.warning(
                "Failed to fetch question for tagging", extra={"question_id": question_id}
            )
            return []

        tags = []
        if question.tags:
            tags.extend(question.tags)
        if question.subtopic:
            tags.append(question.subtopic)
        if question.topic:
            tags.append(question.topic)
        seen: set[str] = set()
        deduped = []
        for t in tags:
            if t not in seen:
                seen.add(t)
                deduped.append(t)
        return deduped

    async def get_related_concepts(self, concept_tag: str) -> list[str]:
        logger.debug("Looking up related concepts", extra={"concept_tag": concept_tag})
        return [concept_tag]

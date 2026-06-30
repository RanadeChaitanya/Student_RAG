from fastapi import APIRouter, Request


router = APIRouter()


@router.get("/concepts")
async def list_concepts(request: Request):
    svc = request.app.state.context.concept_graph
    store = svc._store
    nodes = store.get_all_nodes()
    return [
        {
            "id": n.id,
            "display_name": n.display_name,
            "subject": n.subject,
            "topic": n.topic,
            "subtopic": n.subtopic,
            "difficulty": n.difficulty,
            "prerequisites": n.prerequisites,
        }
        for n in nodes
    ]


@router.get("/concepts/{concept_id}")
async def get_concept(request: Request, concept_id: str):
    svc = request.app.state.context.concept_graph
    return await svc.get_concept(concept_id)


@router.get("/concepts/{concept_id}/chain")
async def get_prerequisite_chain(request: Request, concept_id: str):
    svc = request.app.state.context.concept_graph
    return await svc.get_prerequisite_chain(concept_id)


@router.get("/concepts/{concept_id}/gaps/{student_id}")
async def find_gaps(request: Request, concept_id: str, student_id: str):
    svc = request.app.state.context.concept_graph
    mastery_svc = request.app.state.context.mastery
    return await svc.find_gaps(student_id, mastery_svc)


@router.get("/full-graph")
async def get_full_graph(request: Request):
    svc = request.app.state.context.concept_graph
    store = svc._store
    nodes = store.get_all_nodes()
    edges = store.get_all_edges()
    return {
        "nodes": [
            {
                "id": n.id,
                "display_name": n.display_name,
                "subject": n.subject,
                "topic": n.topic,
                "difficulty": n.difficulty,
            }
            for n in nodes
        ],
        "edges": [
            {"source": e.from_id, "target": e.to_id, "relationship": e.relationship}
            for e in edges
        ],
    }

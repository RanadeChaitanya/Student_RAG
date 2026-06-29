"""Verify FAISS vector search returns meaningful results."""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from suraj_dada.embeddings.generator import EmbeddingGenerator
from suraj_dada.embeddings.service import EmbeddingService
from suraj_dada.embeddings.storage import VectorStoreService


async def main():
    gen = EmbeddingGenerator(dimension=64)
    store = VectorStoreService(dimension=64, index_path="data/test_faiss.bin")
    svc = EmbeddingService(gen, store)

    items = [
        (
            "1",
            "What is Newton's first law of motion?",
            {"subject": "Physics", "topic": "newtons-laws"},
        ),
        (
            "2",
            "Derive the equation v = u + at for constant acceleration",
            {"subject": "Physics", "topic": "kinematics"},
        ),
        (
            "3",
            "Calculate the work done by a force of 10 N over 5 m",
            {"subject": "Physics", "topic": "work-energy"},
        ),
        (
            "4",
            "What is the mole concept in chemistry?",
            {"subject": "Chemistry", "topic": "mole-concept"},
        ),
        (
            "5",
            "Find the derivative of x^2 + 3x + 5",
            {"subject": "Mathematics", "topic": "differentiation"},
        ),
    ]
    for qid, text, meta in items:
        await svc.embed_and_store(qid, text, meta)
    count = await store.get_item_count()
    print(f"Stored {len(items)} items. Index count: {count}")

    queries = [
        ("Newton force motion inertia", "newtons-laws"),
        ("acceleration velocity kinematics", "kinematics"),
        ("chemistry moles atoms molecule", "mole-concept"),
        ("work energy force displacement", "work-energy"),
        ("derivative calculus differentiation", "differentiation"),
    ]
    passes = 0
    for query, expected_topic in queries:
        results = await svc.search_similar(query, top_k=3)
        topics = [r.get("metadata", {}).get("topic", "") for r in results]
        match = expected_topic in topics
        print(f"  Query: {query:<50} -> {topics[:3]}  {'PASS' if match else 'FAIL'}")
        if match:
            passes += 1

    total = len(queries)
    print(f"\n{passes}/{total} queries matched expected topic")
    return passes == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

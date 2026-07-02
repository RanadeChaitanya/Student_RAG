import asyncio
import csv
import json
import logging
import os
import random
import re

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("seed_jee")

DB_URL = "sqlite+aiosqlite:///./data/studob.db"

ARCHIVE_DIR = r"D:\JEE\truedata\archive"

FILES = {
    2023: os.path.join(ARCHIVE_DIR, "jee_2023.csv"),
    2024: os.path.join(ARCHIVE_DIR, "jee_2024.csv"),
    2025: os.path.join(ARCHIVE_DIR, "jee_2025.csv"),
}

DIFFICULTY_MAP = {"easy": 1, "medium": 3, "hard": 5}

MIN_QUALITY_SCORE = 80

def parse_options(options_text):
    if not options_text or not isinstance(options_text, str) or not options_text.strip():
        return None
    parts = re.split(r'\s*\|\s*', options_text.strip())
    cleaned = []
    for p in parts:
        p = re.sub(r'^\(\d+\)\s*', '', p).strip()
        p = re.sub(r'\s+', ' ', p)
        if p:
            cleaned.append(p)
    if len(cleaned) >= 4:
        return {"A": cleaned[0], "B": cleaned[1], "C": cleaned[2], "D": cleaned[3]}
    return None

def parse_answer(answer_num, answer_type):
    ans_type = str(answer_type).strip().lower() if answer_type else ""
    if ans_type == "numerical":
        try:
            return str(float(answer_num))
        except (ValueError, TypeError):
            return str(answer_num).strip()
    try:
        num = int(answer_num)
        if 1 <= num <= 4:
            return chr(ord('A') + num - 1)
    except (ValueError, TypeError):
        pass
    return str(answer_num).strip().upper()

def quality_score(row):
    score = 100
    text_lower = (row.get("question_text", "") or "").lower()
    options_text = (row.get("options", "") or "").lower()
    combined = text_lower + " " + options_text
    if any(p in combined for p in ["option 1", "option 2", "option 3", "option 4"]):
        score -= 40
    if any(p in text_lower for p in ["most stable structure", "identify structure", "correct structure", "given reaction", "major product", "product a", "product b", "product x", "compound a", "compound b", "correct representation", "representation of", "given sugar", "formed in given reaction", "reaction sequence", "following reaction", "identify x", "identify y", "identify z"]):
        score -= 30
    if any(p in text_lower for p in ["graph shown", "graph representing", "graph below", "curve shown", "plot shown", "following graph", "graph of", "which graph"]):
        score -= 30
    if any(p in text_lower for p in ["figure", "diagram", "shown below", "shown above", "given figure", "following figure", "image shown"]):
        score -= 30
    if len(text_lower.split()) < 5:
        score -= 20
    return score

def read_csv_rows(filepath):
    rows = []
    with open(filepath, encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows

def build_test_question(row, year):
    subject = row.get("subject_name", "").strip()
    topic = row.get("chapter_name", "").strip() or "Unknown"
    subtopic = row.get("topic_name", "").strip() or "General"
    difficulty_str = row.get("difficult_level", "").strip().lower()
    difficulty = DIFFICULTY_MAP.get(difficulty_str, 3)
    answer_type = row.get("answer_type", "").strip()
    answer = parse_answer(row.get("answer_option_number", ""), answer_type)
    options = parse_options(row.get("options", ""))
    question_type = "mcq" if answer_type.lower() == "mcq" else "numerical"
    solution = row.get("solution", "").strip()
    question_text = row.get("question_text", "").strip()
    exam_type = "JEE_Main"
    return {
        "subject": subject.lower(),
        "topic": topic,
        "subtopic": subtopic,
        "difficulty": difficulty,
        "question_type": question_type,
        "question_text": question_text,
        "options": options,
        "correct_answer": answer,
        "explanation": solution or f"JEE Main {year} question - refer to syllabus for {topic}: {subtopic}",
        "tags": [subject.lower(), topic.lower().replace(" ", "_"), subtopic.lower().replace(" ", "_"), exam_type.lower()],
        "year": year,
        "exam_type": exam_type,
        "is_active": True,
    }

def build_app_question(tq):
    return {
        "subject": tq["subject"],
        "topic": tq["topic"],
        "subtopic": tq["subtopic"],
        "difficulty": tq["difficulty"],
        "question_type": tq["question_type"],
        "question_text": tq["question_text"],
        "options": tq["options"],
        "correct_answer": tq["correct_answer"],
        "explanation": tq["explanation"],
        "tags": tq["tags"][:3] if tq["tags"] else None,
        "source": "jee_archive",
        "is_active": True,
    }

async def seed():
    engine = create_async_engine(DB_URL, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    all_questions = []
    seen_texts = set()
    duplicate_count = 0
    quality_removed = 0

    for year, filepath in FILES.items():
        if not os.path.exists(filepath):
            logger.warning(f"File not found: {filepath}")
            continue
        rows = read_csv_rows(filepath)
        logger.info(f"Read {len(rows)} rows from {os.path.basename(filepath)}")
        for row in rows:
            qtext = (row.get("question_text", "") or "").strip().lower()
            if not qtext or len(qtext.split()) < 3:
                continue
            norm_text = re.sub(r'\s+', ' ', qtext)
            if norm_text in seen_texts:
                duplicate_count += 1
                continue
            seen_texts.add(norm_text)
            qs = quality_score(row)
            if qs < MIN_QUALITY_SCORE:
                quality_removed += 1
                continue
            tq = build_test_question(row, year)
            all_questions.append(tq)

    logger.info(f"Total quality-filtered questions: {len(all_questions)}")
    logger.info(f"Duplicates removed: {duplicate_count}")
    logger.info(f"Low quality removed: {quality_removed}")

    if not all_questions:
        logger.error("No questions to seed!")
        await engine.dispose()
        return

    async with session_factory() as session:
        existing = await session.execute(text("SELECT COUNT(*) FROM test_questions"))
        count_before = existing.scalar()
        logger.info(f"Existing test_questions: {count_before}")

        if count_before > 50:
            logger.info("Clearing existing test_questions and app_questions before re-seed")
            await session.execute(text("DELETE FROM test_questions"))
            await session.execute(text("DELETE FROM app_questions"))
            await session.commit()
            logger.info("Existing questions cleared")

    batch_size = 200
    total_inserted = 0
    for i in range(0, len(all_questions), batch_size):
        batch = all_questions[i:i + batch_size]
        async with session_factory() as session:
            for tq in batch:
                await session.execute(
                    text("""INSERT INTO test_questions
                        (subject, topic, subtopic, difficulty, question_type,
                         question_text, options, correct_answer, explanation,
                         tags, year, exam_type, is_active, created_at)
                        VALUES (:subject, :topic, :subtopic, :difficulty, :qtype,
                         :qtext, :opts, :correct, :explanation,
                         :tags, :year, :exam_type, 1, datetime('now'))"""),
                    {
                        "subject": tq["subject"],
                        "topic": tq["topic"],
                        "subtopic": tq["subtopic"],
                        "difficulty": tq["difficulty"],
                        "qtype": tq["question_type"],
                        "qtext": tq["question_text"],
                        "opts": json.dumps(tq["options"]) if tq["options"] else None,
                        "correct": tq["correct_answer"],
                        "explanation": tq["explanation"],
                        "tags": json.dumps(tq["tags"]) if tq["tags"] else None,
                        "year": tq["year"],
                        "exam_type": tq["exam_type"],
                    },
                )
            await session.commit()
            total_inserted += len(batch)
            logger.info(f"Inserted {total_inserted}/{len(all_questions)} test questions")

    async with session_factory() as session:
        result = await session.execute(text("SELECT COUNT(*) FROM test_questions"))
        logger.info(f"Total test_questions now: {result.scalar()}")

    subjects = {}
    for tq in all_questions:
        s = tq["subject"]
        if s not in subjects:
            subjects[s] = []
        subjects[s].append(tq)

    app_questions = []
    questions_per_subject = 70
    rng = random.Random(42)
    for subj, qs in subjects.items():
        rng.shuffle(qs)
        selected = qs[:questions_per_subject]
        for tq in selected:
            app_questions.append(build_app_question(tq))
    app_questions.extend(app_questions[:10])

    logger.info(f"Seeding {len(app_questions)} app questions for practice mode")

    inserted_app = 0
    for i in range(0, len(app_questions), batch_size):
        batch = app_questions[i:i + batch_size]
        async with session_factory() as session:
            for aq in batch:
                await session.execute(
                    text("""INSERT INTO app_questions
                        (subject, topic, subtopic, difficulty, question_type,
                         question_text, options, correct_answer, explanation,
                         tags, source, is_active, created_at)
                        VALUES (:subject, :topic, :subtopic, :difficulty, :qtype,
                         :qtext, :opts, :correct, :explanation,
                         :tags, :source, 1, datetime('now'))"""),
                    {
                        "subject": aq["subject"],
                        "topic": aq["topic"],
                        "subtopic": aq["subtopic"],
                        "difficulty": aq["difficulty"],
                        "qtype": aq["question_type"],
                        "qtext": aq["question_text"],
                        "opts": json.dumps(aq["options"]) if aq["options"] else None,
                        "correct": aq["correct_answer"],
                        "explanation": aq["explanation"],
                        "tags": json.dumps(aq["tags"]) if aq["tags"] else None,
                        "source": aq["source"],
                    },
                )
            await session.commit()
            inserted_app += len(batch)
            logger.info(f"Inserted {inserted_app}/{len(app_questions)} app questions")

    try:
        logger.info("Rebuilding FAISS index...")
        from studob.embeddings.storage import VectorStoreService
        from studob.embeddings.generator import EmbeddingGenerator

        async with session_factory() as session:
            result = await session.execute(
                text("SELECT id, subject, topic, subtopic, difficulty, question_text FROM app_questions WHERE is_active = 1")
            )
            rows = result.fetchall()

        texts = []
        meta_list = []
        for r in rows:
            texts.append(f"{r[1]} {r[2]} {r[3]}: {r[5]}")
            meta_list.append({"id": r[0], "subject": r[1], "topic": r[2], "subtopic": r[3], "difficulty": r[4]})

        if texts:
            gen = EmbeddingGenerator(dimension=384)
            store = VectorStoreService(dimension=384, index_path="./data/faiss_index.bin")
            embeddings = await gen.generate_batch(texts)
            if embeddings and len(embeddings) > 0:
                items = [(str(m["id"]), emb, m) for emb, m in zip(embeddings, meta_list)]
                await store.add_items(items)
                await store.save()
                logger.info(f"FAISS index built with {len(embeddings)} vectors")
    except Exception as e:
        logger.warning(f"Could not rebuild FAISS index: {e}")

    await engine.dispose()
    logger.info("JEE archive seed complete!")

if __name__ == "__main__":
    asyncio.run(seed())

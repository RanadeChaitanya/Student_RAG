import asyncio
import json
import logging
import random
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("seed")

DB_URL = "sqlite+aiosqlite:///./data/studob.db"

STUDENTS = [
    {"name": "Arjun Sharma", "grade": "12", "exam_target": "JEE_Advanced", "board": "CBSE", "language": "english"},
    {"name": "Priya Patel", "grade": "12", "exam_target": "JEE_Main", "board": "CBSE", "language": "english"},
    {"name": "Rahul Verma", "grade": "11", "exam_target": "JEE_Main", "board": "ICSE", "language": "english"},
    {"name": "Sneha Gupta", "grade": "12", "exam_target": "JEE_Advanced", "board": "CBSE", "language": "hindi"},
    {"name": "Amit Kumar", "grade": "12", "exam_target": "JEE_Main", "board": "CBSE", "language": "english"},
    {"name": "Kavya Reddy", "grade": "12", "exam_target": "JEE_Advanced", "board": "TSBIE", "language": "telugu"},
    {"name": "Rohit Singh", "grade": "12", "exam_target": "JEE_Main", "board": "CBSE", "language": "english"},
    {"name": "Ananya Iyer", "grade": "12", "exam_target": "JEE_Advanced", "board": "CBSE", "language": "tamil"},
    {"name": "Vikram Joshi", "grade": "11", "exam_target": "JEE_Main", "board": "CBSE", "language": "english"},
    {"name": "Neha Deshmukh", "grade": "12", "exam_target": "JEE_Advanced", "board": "MSBSHSE", "language": "marathi"},
    {"name": "Aryan Kapoor", "grade": "12", "exam_target": "JEE_Main", "board": "CBSE", "language": "english"},
    {"name": "Ishita Mehta", "grade": "12", "exam_target": "JEE_Advanced", "board": "GSEB", "language": "gujarati"},
    {"name": "Aditya Nair", "grade": "11", "exam_target": "JEE_Main", "board": "CBSE", "language": "malayalam"},
    {"name": "Pooja Sharma", "grade": "12", "exam_target": "JEE_Main", "board": "CBSE", "language": "english"},
    {"name": "Ravi Tiwari", "grade": "12", "exam_target": "JEE_Advanced", "board": "CBSE", "language": "english"},
    {"name": "Divya Kulkarni", "grade": "12", "exam_target": "JEE_Main", "board": "MSBSHSE", "language": "marathi"},
    {"name": "Karan Bansal", "grade": "11", "exam_target": "JEE_Advanced", "board": "CBSE", "language": "english"},
    {"name": "Tanvi Agarwal", "grade": "12", "exam_target": "JEE_Main", "board": "CBSE", "language": "english"},
    {"name": "Siddharth Rao", "grade": "12", "exam_target": "JEE_Advanced", "board": "KSEEB", "language": "kannada"},
    {"name": "Nandini Menon", "grade": "12", "exam_target": "JEE_Main", "board": "CBSE", "language": "english"},
    {"name": "Yash Saxena", "grade": "12", "exam_target": "JEE_Advanced", "board": "CBSE", "language": "english"},
    {"name": "Riya Chatterjee", "grade": "11", "exam_target": "JEE_Main", "board": "WBCHSE", "language": "bengali"},
    {"name": "Harsh Vardhan", "grade": "12", "exam_target": "JEE_Main", "board": "CBSE", "language": "english"},
    {"name": "Sara Khan", "grade": "12", "exam_target": "JEE_Advanced", "board": "CBSE", "language": "urdu"},
    {"name": "Manav Bhatia", "grade": "12", "exam_target": "JEE_Main", "board": "CBSE", "language": "english"},
    {"name": "Aisha Mirza", "grade": "11", "exam_target": "JEE_Advanced", "board": "CBSE", "language": "kashmiri"},
    {"name": "Gaurav Pandey", "grade": "12", "exam_target": "JEE_Main", "board": "CBSE", "language": "english"},
    {"name": "Lakshmi Nair", "grade": "12", "exam_target": "JEE_Advanced", "board": "Kerala", "language": "malayalam"},
    {"name": "Pranav Kulkarni", "grade": "12", "exam_target": "JEE_Main", "board": "MSBSHSE", "language": "marathi"},
    {"name": "Shreya Das", "grade": "12", "exam_target": "JEE_Advanced", "board": "WBCHSE", "language": "bengali"},
    {"name": "Deepak Yadav", "grade": "12", "exam_target": "JEE_Main", "board": "CBSE", "language": "english"},
    {"name": "Kriti Thakur", "grade": "11", "exam_target": "JEE_Main", "board": "CBSE", "language": "english"},
    {"name": "Surya Prakash", "grade": "12", "exam_target": "JEE_Advanced", "board": "CBSE", "language": "telugu"},
    {"name": "Anjali Singh", "grade": "12", "exam_target": "JEE_Main", "board": "CBSE", "language": "english"},
    {"name": "Mohit Agarwal", "grade": "12", "exam_target": "JEE_Advanced", "board": "CBSE", "language": "english"},
    {"name": "Varsha Patil", "grade": "11", "exam_target": "JEE_Main", "board": "MSBSHSE", "language": "marathi"},
    {"name": "Kunal Dutta", "grade": "12", "exam_target": "JEE_Main", "board": "CBSE", "language": "english"},
    {"name": "Tanya Bhat", "grade": "12", "exam_target": "JEE_Advanced", "board": "CBSE", "language": "konkani"},
    {"name": "Aditi Chauhan", "grade": "12", "exam_target": "JEE_Main", "board": "CBSE", "language": "hindi"},
    {"name": "Nikhil Jain", "grade": "12", "exam_target": "JEE_Advanced", "board": "CBSE", "language": "english"},
    {"name": "Pallavi Mishra", "grade": "11", "exam_target": "JEE_Main", "board": "CBSE", "language": "english"},
    {"name": "Rohan Desai", "grade": "12", "exam_target": "JEE_Main", "board": "GSEB", "language": "gujarati"},
    {"name": "Simran Kaur", "grade": "12", "exam_target": "JEE_Advanced", "board": "CBSE", "language": "punjabi"},
    {"name": "Varun Shukla", "grade": "12", "exam_target": "JEE_Main", "board": "CBSE", "language": "english"},
    {"name": "Harini Krishnan", "grade": "12", "exam_target": "JEE_Advanced", "board": "CBSE", "language": "tamil"},
    {"name": "Akash Mishra", "grade": "11", "exam_target": "JEE_Main", "board": "CBSE", "language": "english"},
    {"name": "Sonal Tripathi", "grade": "12", "exam_target": "JEE_Advanced", "board": "CBSE", "language": "english"},
    {"name": "Abhishek Chauhan", "grade": "12", "exam_target": "JEE_Main", "board": "CBSE", "language": "english"},
    {"name": "Ritika Bhardwaj", "grade": "12", "exam_target": "JEE_Advanced", "board": "CBSE", "language": "english"},
    {"name": "Manoj Sahu", "grade": "11", "exam_target": "JEE_Main", "board": "CBSE", "language": "odia"},
]

PHYSICS_TOPICS = [
    ("Physics", "Kinematics", "Motion in 1D"),
    ("Physics", "Kinematics", "Motion in 2D"),
    ("Physics", "Kinematics", "Relative Motion"),
    ("Physics", "Laws of Motion", "Newton's Laws"),
    ("Physics", "Laws of Motion", "Friction"),
    ("Physics", "Laws of Motion", "Circular Motion"),
    ("Physics", "Work Energy Power", "Work-Energy Theorem"),
    ("Physics", "Work Energy Power", "Conservation of Energy"),
    ("Physics", "Work Energy Power", "Power & Efficiency"),
    ("Physics", "Rotational Motion", "Moment of Inertia"),
    ("Physics", "Rotational Motion", "Torque & Angular Momentum"),
    ("Physics", "Rotational Motion", "Rolling Motion"),
    ("Physics", "Gravitation", "Universal Gravitation"),
    ("Physics", "Gravitation", "Kepler's Laws"),
    ("Physics", "Gravitation", "Satellite Motion"),
    ("Physics", "SHM", "Simple Harmonic Motion"),
    ("Physics", "SHM", "Pendulum & Springs"),
    ("Physics", "Waves", "Wave Motion"),
    ("Physics", "Waves", "Sound Waves & Doppler"),
    ("Physics", "Electrostatics", "Coulomb's Law"),
    ("Physics", "Electrostatics", "Electric Field & Potential"),
    ("Physics", "Electrostatics", "Capacitors"),
    ("Physics", "Current Electricity", "Ohm's Law & Circuits"),
    ("Physics", "Current Electricity", "Kirchhoff's Laws"),
    ("Physics", "Current Electricity", "Potentiometer & Meter Bridge"),
    ("Physics", "Magnetism", "Magnetic Effects of Current"),
    ("Physics", "Magnetism", "Force on Moving Charges"),
    ("Physics", "Magnetism", "Magnetic Materials"),
    ("Physics", "EMI & AC", "Electromagnetic Induction"),
    ("Physics", "EMI & AC", "AC Circuits"),
    ("Physics", "Optics", "Ray Optics & Reflection"),
    ("Physics", "Optics", "Refraction & Lenses"),
    ("Physics", "Optics", "Wave Optics & Interference"),
    ("Physics", "Modern Physics", "Photoelectric Effect"),
    ("Physics", "Modern Physics", "Atomic Models"),
    ("Physics", "Modern Physics", "Nuclear Physics"),
    ("Physics", "Thermodynamics", "Laws of Thermodynamics"),
    ("Physics", "Thermodynamics", "Kinetic Theory of Gases"),
    ("Physics", "Fluids", "Fluid Statics & Dynamics"),
    ("Physics", "Fluids", "Viscosity & Surface Tension"),
]

CHEMISTRY_TOPICS = [
    ("Chemistry", "Physical Chemistry", "Mole Concept & Stoichiometry"),
    ("Chemistry", "Physical Chemistry", "Atomic Structure"),
    ("Chemistry", "Physical Chemistry", "Chemical Bonding"),
    ("Chemistry", "Physical Chemistry", "Thermodynamics & Thermochemistry"),
    ("Chemistry", "Physical Chemistry", "Chemical Kinetics"),
    ("Chemistry", "Physical Chemistry", "Equilibrium"),
    ("Chemistry", "Physical Chemistry", "Electrochemistry"),
    ("Chemistry", "Physical Chemistry", "Solutions & Colligative Properties"),
    ("Chemistry", "Organic Chemistry", "Hydrocarbons"),
    ("Chemistry", "Organic Chemistry", "Haloalkanes & Haloarenes"),
    ("Chemistry", "Organic Chemistry", "Alcohols, Phenols & Ethers"),
    ("Chemistry", "Organic Chemistry", "Aldehydes & Ketones"),
    ("Chemistry", "Organic Chemistry", "Carboxylic Acids"),
    ("Chemistry", "Organic Chemistry", "Amines"),
    ("Chemistry", "Organic Chemistry", "Biomolecules"),
    ("Chemistry", "Organic Chemistry", "Polymers & Chemistry in Daily Life"),
    ("Chemistry", "Inorganic Chemistry", "Periodic Table & Periodicity"),
    ("Chemistry", "Inorganic Chemistry", "S-block Elements"),
    ("Chemistry", "Inorganic Chemistry", "P-block Elements"),
    ("Chemistry", "Inorganic Chemistry", "D-block Elements"),
    ("Chemistry", "Inorganic Chemistry", "Coordination Compounds"),
    ("Chemistry", "Inorganic Chemistry", "Metallurgy"),
    ("Chemistry", "Inorganic Chemistry", "Environmental Chemistry"),
]

MATH_TOPICS = [
    ("Mathematics", "Algebra", "Sets, Relations & Functions"),
    ("Mathematics", "Algebra", "Complex Numbers"),
    ("Mathematics", "Algebra", "Quadratic Equations"),
    ("Mathematics", "Algebra", "Permutations & Combinations"),
    ("Mathematics", "Algebra", "Binomial Theorem"),
    ("Mathematics", "Algebra", "Sequences & Series"),
    ("Mathematics", "Algebra", "Matrices & Determinants"),
    ("Mathematics", "Algebra", "Probability"),
    ("Mathematics", "Algebra", "Statistics"),
    ("Mathematics", "Calculus", "Limits & Continuity"),
    ("Mathematics", "Calculus", "Differentiation"),
    ("Mathematics", "Calculus", "Application of Derivatives"),
    ("Mathematics", "Calculus", "Indefinite Integration"),
    ("Mathematics", "Calculus", "Definite Integration"),
    ("Mathematics", "Calculus", "Area under Curves"),
    ("Mathematics", "Calculus", "Differential Equations"),
    ("Mathematics", "Coordinate Geometry", "Straight Lines"),
    ("Mathematics", "Coordinate Geometry", "Circles"),
    ("Mathematics", "Coordinate Geometry", "Parabola & Hyperbola"),
    ("Mathematics", "Coordinate Geometry", "Ellipse"),
    ("Mathematics", "Vectors & 3D", "Vector Algebra"),
    ("Mathematics", "Vectors & 3D", "3D Geometry"),
    ("Mathematics", "Trigonometry", "Trigonometric Ratios & Identities"),
    ("Mathematics", "Trigonometry", "Inverse Trigonometry"),
    ("Mathematics", "Trigonometry", "Trigonometric Equations"),
]

ERROR_CATEGORIES = [
    "concept_misunderstood", "calculation_error", "formula_error",
    "sign_error", "unit_error", "reading_error",
]

PHYSICS_QS = [
    lambda: {"text": "A particle starts from rest and accelerates uniformly at 2 m/s². What is its velocity after 5 seconds?", "opts": {"A": "5 m/s", "B": "10 m/s", "C": "15 m/s", "D": "20 m/s"}, "ans": "B", "expl": "Using v = u + at = 0 + 2×5 = 10 m/s."},
    lambda: {"text": "What is the work done by a force of 10 N moving an object 5 m in the direction of the force?", "opts": {"A": "2 J", "B": "15 J", "C": "50 J", "D": "100 J"}, "ans": "C", "expl": "Work = F × d × cosθ = 10 × 5 × 1 = 50 J."},
    lambda: {"text": "The SI unit of electric potential is:", "opts": {"A": "Ampere", "B": "Volt", "C": "Ohm", "D": "Coulomb"}, "ans": "B", "expl": "Electric potential is measured in Volts (J/C)."},
    lambda: {"text": "What is the focal length of a lens with power +2 D?", "opts": {"A": "0.5 m", "B": "2 m", "C": "0.2 m", "D": "5 m"}, "ans": "A", "expl": "f = 1/P = 1/2 = 0.5 m."},
    lambda: {"text": "A ball is dropped from a height of 20 m. How long does it take to reach the ground? (g = 10 m/s²)", "opts": {"A": "1 s", "B": "2 s", "C": "4 s", "D": "√2 s"}, "ans": "B", "expl": "Using s = ½gt², t = √(2s/g) = √(40/10) = 2 s."},
    lambda: {"text": "Which of the following is a scalar quantity?", "opts": {"A": "Velocity", "B": "Force", "C": "Energy", "D": "Acceleration"}, "ans": "C", "expl": "Energy has magnitude only, no direction — it is a scalar."},
]

CHEM_QS = [
    lambda: {"text": "What is the molar mass of H₂SO₄?", "opts": {"A": "49 g/mol", "B": "98 g/mol", "C": "196 g/mol", "D": "32 g/mol"}, "ans": "B", "expl": "H₂SO₄: 2×1 + 32 + 4×16 = 98 g/mol."},
    lambda: {"text": "Which of the following is an example of a covalent bond?", "opts": {"A": "NaCl", "B": "H₂O", "C": "KBr", "D": "MgO"}, "ans": "B", "expl": "H₂O has covalent bonds between hydrogen and oxygen atoms."},
    lambda: {"text": "What is the pH of a 0.001 M HCl solution?", "opts": {"A": "1", "B": "3", "C": "7", "D": "11"}, "ans": "B", "expl": "pH = -log[H⁺] = -log(10⁻³) = 3."},
    lambda: {"text": "The IUPAC name of CH₃CH₂OH is:", "opts": {"A": "Methanol", "B": "Ethanol", "C": "Propanol", "D": "Butanol"}, "ans": "B", "expl": "CH₃CH₂OH is ethanol (ethyl alcohol)."},
    lambda: {"text": "Which element has the electronic configuration 1s² 2s² 2p⁶ 3s¹?", "opts": {"A": "Lithium", "B": "Sodium", "C": "Potassium", "D": "Magnesium"}, "ans": "B", "expl": "Atomic number 11 = Sodium (Na)."},
    lambda: {"text": "In a redox reaction, oxidation involves:", "opts": {"A": "Gain of electrons", "B": "Loss of electrons", "C": "Gain of protons", "D": "Loss of oxygen"}, "ans": "B", "expl": "Oxidation is the loss of electrons."},
]

MATH_QS = [
    lambda: {"text": "What is the derivative of x³?", "opts": {"A": "2x²", "B": "3x²", "C": "x²", "D": "3x"}, "ans": "B", "expl": "d/dx(x³) = 3x²."},
    lambda: {"text": "If A = {1,2,3} and B = {2,3,4}, what is A ∩ B?", "opts": {"A": "{1,2,3,4}", "B": "{1,4}", "C": "{2,3}", "D": "{1,2,3}"}, "ans": "C", "expl": "Intersection of A and B is {2,3}."},
    lambda: {"text": "What is the value of sin(90°)?", "opts": {"A": "0", "B": "0.5", "C": "1", "D": "√3/2"}, "ans": "C", "expl": "sin(90°) = 1."},
    lambda: {"text": "How many ways can 3 books be arranged on a shelf?", "opts": {"A": "3", "B": "6", "C": "9", "D": "27"}, "ans": "B", "expl": "3! = 6 arrangements."},
    lambda: {"text": "What is the determinant of [[1,2],[3,4]]?", "opts": {"A": "2", "B": "-2", "C": "10", "D": "-10"}, "ans": "B", "expl": "det = 1×4 - 2×3 = 4 - 6 = -2."},
    lambda: {"text": "The sum of the first 10 natural numbers is:", "opts": {"A": "45", "B": "50", "C": "55", "D": "100"}, "ans": "C", "expl": "Sum = n(n+1)/2 = 10×11/2 = 55."},
]

def build_question(subject, topic, subtopic, difficulty, qid, template_pool):
    tmpl = random.choice(template_pool)()
    return {
        "id": qid,
        "subject": subject.lower(),
        "topic": topic,
        "subtopic": subtopic,
        "difficulty": difficulty,
        "question_type": "mcq",
        "question_text": tmpl["text"],
        "options": tmpl["opts"],
        "correct_answer": tmpl["ans"],
        "explanation": tmpl["expl"],
        "tags": [subject.lower(), topic.lower().replace(" ", "_"), subtopic.lower().replace(" ", "_")],
        "source": "app",
        "is_active": True,
    }

def build_test_question(subject, topic, subtopic, difficulty, qid, template_pool):
    tmpl = random.choice(template_pool)()
    year = random.choice([2022, 2023, 2024])
    exam_type = random.choice(["JEE_Main", "JEE_Advanced"])
    return {
        "id": qid,
        "subject": subject.lower(),
        "topic": topic,
        "subtopic": subtopic,
        "difficulty": difficulty,
        "question_type": "mcq",
        "question_text": f"{tmpl['text']} (JEE {exam_type.split('_')[1]} {year})",
        "options": tmpl["opts"],
        "correct_answer": tmpl["ans"],
        "explanation": tmpl["expl"],
        "tags": [subject.lower(), topic.lower().replace(" ", "_"), subtopic.lower().replace(" ", "_"), exam_type.lower()],
        "year": year,
        "exam_type": exam_type,
        "is_active": True,
    }

async def seed():
    engine = create_async_engine(DB_URL, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        await session.execute(text("DELETE FROM mistake_records"))
        await session.execute(text("DELETE FROM attempts"))
        await session.execute(text("DELETE FROM sessions"))
        await session.execute(text("DELETE FROM mastery_scores"))
        await session.execute(text("DELETE FROM app_questions"))
        await session.execute(text("DELETE FROM test_questions"))
        await session.execute(text("DELETE FROM students"))
        await session.commit()

    student_ids = []
    async with session_factory() as session:
        for s in STUDENTS:
            sid = str(uuid.uuid4())
            now = datetime.now(UTC)
            await session.execute(
                text("INSERT INTO students (id, name, grade, exam_target, board, language, created_at, updated_at) VALUES (:id, :name, :grade, :exam, :board, :lang, :now, :now)"),
                {"id": sid, "name": s["name"], "grade": s["grade"], "exam": s["exam_target"], "board": s["board"], "lang": s["language"], "now": now},
            )
            student_ids.append(sid)
        await session.commit()
    logger.info(f"Created {len(student_ids)} students")

    all_topics = PHYSICS_TOPICS + CHEMISTRY_TOPICS + MATH_TOPICS

    from studob.database.models import AppQuestion
    app_qids = []
    qid = 1
    async with session_factory() as session:
        for subject, topic, subtopic in all_topics:
            pool = PHYSICS_QS if subject == "Physics" else CHEM_QS if subject == "Chemistry" else MATH_QS
            difficulty = random.choices([1, 2, 3, 4, 5], weights=[15, 25, 30, 20, 10])[0]
            q = build_question(subject, topic, subtopic, difficulty, qid, pool)
            aq = AppQuestion(
                subject=q["subject"], topic=q["topic"], subtopic=q["subtopic"],
                difficulty=q["difficulty"], question_type=q["question_type"],
                question_text=q["question_text"], options=q["options"],
                correct_answer=q["correct_answer"], explanation=q["explanation"],
                tags=q["tags"], source=q["source"], is_active=True,
            )
            session.add(aq)
            await session.flush()
            app_qids.append(aq.id)
            qid += 1
        await session.commit()
    logger.info(f"Created {len(app_qids)} app questions")

    from studob.database.models import TestQuestion
    test_qids = []
    async with session_factory() as session:
        for _ in range(50):
            subject, topic, subtopic = random.choice(all_topics)
            pool = PHYSICS_QS if subject == "Physics" else CHEM_QS if subject == "Chemistry" else MATH_QS
            difficulty = random.choices([1, 2, 3, 4, 5], weights=[10, 20, 30, 25, 15])[0]
            q = build_test_question(subject, topic, subtopic, difficulty, qid, pool)
            tq = TestQuestion(
                subject=q["subject"], topic=q["topic"], subtopic=q["subtopic"],
                difficulty=q["difficulty"], question_type=q["question_type"],
                question_text=q["question_text"], options=q["options"],
                correct_answer=q["correct_answer"], explanation=q["explanation"],
                tags=q["tags"], year=q["year"], exam_type=q["exam_type"], is_active=True,
            )
            session.add(tq)
            qid += 1
        await session.commit()
        result = await session.execute(text("SELECT id FROM test_questions"))
        test_qids = [r[0] for r in result.fetchall()]
    logger.info(f"Created {len(test_qids)} test questions")

    all_qids_pool = app_qids + test_qids

    from studob.database.models import MasteryScore, Session, Attempt, MistakeRecord

    for idx, sid in enumerate(student_ids):
        student_name = STUDENTS[idx]["name"]
        slug = student_name.lower().replace(" ", "-")

        num_topics = random.randint(6, 12)
        chosen_topics = random.sample(all_topics, min(num_topics, len(all_topics)))

        async with session_factory() as session:
            for subject, topic, subtopic in chosen_topics:
                base_score = random.choices(
                    [random.uniform(15, 40), random.uniform(40, 65), random.uniform(65, 85), random.uniform(85, 98)],
                    weights=[25, 30, 25, 20],
                )[0]
                confidence = random.uniform(0.3, 0.95)
                attempts = random.randint(2, 15)
                now = datetime.now(UTC) - timedelta(days=random.randint(0, 10))
                session.add(MasteryScore(
                    student_id=sid, subject=subject, topic=topic, subtopic=subtopic,
                    score=round(base_score, 1), confidence=round(confidence, 2),
                    attempts=attempts, last_updated=now,
                ))
            await session.commit()

        num_sessions = random.randint(6, 14)
        for si in range(num_sessions):
            sess_type = random.choices(["practice", "assessment"], weights=[60, 40])[0]
            days_ago = random.randint(1, 30)
            sess_start = datetime.now(UTC) - timedelta(days=days_ago)
            sess_end = sess_start + timedelta(minutes=random.randint(10, 90))
            sess_id = f"past-{slug}-{idx}-{si}"

            num_questions = random.randint(3, 8)
            qs_for_session = random.sample(all_qids_pool, min(num_questions, len(all_qids_pool)))
            correct_count = 0
            mastery_delta = random.uniform(-3.0, 8.0)

            async with session_factory() as session:
                session.add(Session(
                    id=sess_id, student_id=sid, session_type=sess_type,
                    started_at=sess_start, ended_at=sess_end,
                    questions_count=len(qs_for_session), correct_count=0,
                    mastery_delta=mastery_delta,
                ))
                await session.commit()

            for qi, qid_q in enumerate(qs_for_session):
                is_correct = random.random() > 0.4
                if is_correct:
                    correct_count += 1
                response_time = random.uniform(10, 120)
                hints = random.randint(0, 2)
                retries = random.randint(0, 1) if not is_correct else 0
                answered_at = sess_start + timedelta(minutes=qi * 3 + 1)

                async with session_factory() as session:
                    session.add(Attempt(
                        student_id=sid, question_id=qid_q,
                        question_type=sess_type, is_correct=is_correct,
                        response_time_seconds=round(response_time, 1),
                        hints_used=hints, retry_count=retries,
                        answered_at=answered_at, session_id=sess_id,
                    ))
                    await session.commit()

                if not is_correct:
                    err_cat = random.choice(ERROR_CATEGORIES)
                    concept_tag = chosen_topics[qi % len(chosen_topics)][2]
                    async with session_factory() as session:
                        session.add(MistakeRecord(
                            student_id=sid, question_id=qid_q, session_id=sess_id,
                            error_category=err_cat, concept_tag=concept_tag,
                            confidence=round(random.uniform(0.3, 0.9), 2),
                            diagnosis_detail={"suggested_review": f"Review {concept_tag} fundamentals"},
                        ))
                        await session.commit()

            async with session_factory() as session:
                await session.execute(
                    text("UPDATE sessions SET correct_count = :ccount WHERE id = :id"),
                    {"ccount": correct_count, "id": sess_id},
                )
                await session.commit()

        if (idx + 1) % 10 == 0:
            logger.info(f"Seeded student {idx + 1}/{len(student_ids)}")

    logger.info("Seeded all students with sessions, attempts, mistakes")

    try:
        from studob.embeddings.storage import VectorStoreService
        from studob.embeddings.generator import EmbeddingGenerator
        from studob.question_bank.app_questions import AppQuestionService

        logger.info("Building FAISS vector index...")
        app_q_svc = AppQuestionService(session_factory)
        all_qs = await app_q_svc.get_all_questions()
        if all_qs:
            texts = []
            meta_list = []
            for q in all_qs:
                texts.append(f"{q.subject} {q.topic} {q.subtopic}: {q.question_text}")
                meta_list.append({"id": q.id, "subject": q.subject, "topic": q.topic, "subtopic": q.subtopic, "difficulty": q.difficulty})
            gen = EmbeddingGenerator(dimension=384)
            store = VectorStoreService(dimension=384, index_path="./data/faiss_index.bin")
            embeddings = await gen.generate_batch(texts)
            if embeddings and len(embeddings) > 0:
                items = [(str(m["id"]), emb, m) for emb, m in zip(embeddings, meta_list)]
                await store.add_items(items)
                await store.save()
                logger.info(f"FAISS index built with {len(embeddings)} vectors")
    except Exception as e:
        logger.warning(f"Could not build FAISS index: {e}")

    await engine.dispose()
    logger.info("Seed complete!")

if __name__ == "__main__":
    asyncio.run(seed())

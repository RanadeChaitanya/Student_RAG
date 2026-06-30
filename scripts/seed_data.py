# ruff: noqa: E501
import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import func, select

from studob.config.loader import get_config
from studob.database.engine import DatabaseEngine
from studob.database.models import (
    AppQuestion,
    MasteryScore,
    TestQuestion,
)
from studob.embeddings.generator import EmbeddingGenerator
from studob.embeddings.service import EmbeddingService
from studob.embeddings.storage import VectorStoreService
from studob.logging_setup import get_logger, setup_logging
from studob.question_bank.app_questions import AppQuestionService
from studob.question_bank.test_questions import TestQuestionService
from studob.schemas.question import AppQuestionCreate, TestQuestionCreate
from studob.student.profile import StudentProfileService

logger = get_logger("seed")

SAMPLE_STUDENTS = [
    {
        "name": "Arjun Sharma",
        "grade": "12",
        "exam_target": "JEE_Advanced",
        "board": "CBSE",
        "language": "english",
    },
    {
        "name": "Priya Patel",
        "grade": "12",
        "exam_target": "JEE_Main",
        "board": "CBSE",
        "language": "english",
    },
    {
        "name": "Rahul Verma",
        "grade": "11",
        "exam_target": "JEE_Main",
        "board": "ICSE",
        "language": "english",
    },
    {
        "name": "Sneha Gupta",
        "grade": "12",
        "exam_target": "JEE_Advanced",
        "board": "CBSE",
        "language": "hindi",
    },
    {
        "name": "Amit Kumar",
        "grade": "12",
        "exam_target": "JEE_Main",
        "board": "CBSE",
        "language": "english",
    },
]

SAMPLE_APP_QUESTIONS = [
    {
        "subject": "physics",
        "topic": "mechanics",
        "subtopic": "kinematics",
        "difficulty": 2,
        "question_type": "mcq",
        "question_text": "A particle moves with uniform acceleration along a straight line. If its velocities at t=0 and t=t are v0 and v respectively, the average velocity over the time interval is:",
        "options": {"A": "(v0 + v)/2", "B": "(v - v0)/2", "C": "(v0 + v)/t", "D": "(v - v0)/t"},
        "correct_answer": "(v0 + v)/2",
        "explanation": "For uniform acceleration, average velocity = (initial + final velocity)/2 = (v0 + v)/2",
        "tags": ["kinematics", "uniform_acceleration", "average_velocity"],
        "source": "curated",
    },
    {
        "subject": "physics",
        "topic": "mechanics",
        "subtopic": "newtons_laws",
        "difficulty": 3,
        "question_type": "mcq",
        "question_text": "A block of mass m is placed on a rough horizontal surface (coefficient of friction = mu). A horizontal force F is applied. The acceleration of the block is:",
        "options": {"A": "F/m", "B": "(F - mu*mg)/m", "C": "mu*g", "D": "F/m - mu*g"},
        "correct_answer": "(F - mu*mg)/m",
        "explanation": "Net force = Applied force - Friction = F - mu*mg. Acceleration = net_force/mass = (F - mu*mg)/m",
        "tags": ["newtons_laws", "friction", "force_analysis"],
        "source": "curated",
    },
    {
        "subject": "physics",
        "topic": "mechanics",
        "subtopic": "work_energy",
        "difficulty": 3,
        "question_type": "mcq",
        "question_text": "A body of mass m is projected vertically upward with speed u. The work done by gravity during the ascent to the highest point is:",
        "options": {"A": "mu^2/2", "B": "-mu^2/2", "C": "mu^2", "D": "0"},
        "correct_answer": "-mu^2/2",
        "explanation": "At the highest point, v=0. Using work-energy theorem: W_gravity = Delta_KE = 0 - mu^2/2 = -mu^2/2",
        "tags": ["work_energy", "gravitation", "conservation_of_energy"],
        "source": "curated",
    },
    {
        "subject": "physics",
        "topic": "mechanics",
        "subtopic": "rotational_motion",
        "difficulty": 4,
        "question_type": "mcq",
        "question_text": "A uniform disc of mass M and radius R has moment of inertia about its central axis:",
        "options": {"A": "MR^2/2", "B": "MR^2", "C": "2MR^2/5", "D": "MR^2/3"},
        "correct_answer": "MR^2/2",
        "explanation": "For a uniform disc rotating about its central axis, I = MR^2/2",
        "tags": ["rotational_motion", "moment_of_inertia", "rigid_body_dynamics"],
        "source": "curated",
    },
    {
        "subject": "physics",
        "topic": "electrostatics",
        "subtopic": "electrostatics",
        "difficulty": 3,
        "question_type": "mcq",
        "question_text": "Two point charges +q and +4q are placed at a distance r apart. The point on the line joining them where the electric field is zero is:",
        "options": {
            "A": "r/3 from +q",
            "B": "2r/3 from +q",
            "C": "r/4 from +q",
            "D": "r/2 from +q",
        },
        "correct_answer": "r/3 from +q",
        "explanation": "Let the point be at distance x from +q. E1 = kq/x^2 = E2 = k(4q)/(r-x)^2. Solving: 1/x^2 = 4/(r-x)^2, (r-x)^2 = 4x^2, r-x = 2x, x = r/3",
        "tags": ["electrostatics", "electric_field", "coulombs_law"],
        "source": "curated",
    },
    {
        "subject": "physics",
        "topic": "electrostatics",
        "subtopic": "capacitance",
        "difficulty": 4,
        "question_type": "mcq",
        "question_text": "Two capacitors of capacitance C and 2C are connected in series. The equivalent capacitance is:",
        "options": {"A": "3C/2", "B": "2C/3", "C": "3C", "D": "C/3"},
        "correct_answer": "2C/3",
        "explanation": "For series: 1/C_eq = 1/C + 1/(2C) = 3/(2C), so C_eq = 2C/3",
        "tags": ["capacitance", "series_combination", "circuits"],
        "source": "curated",
    },
    {
        "subject": "physics",
        "topic": "magnetism",
        "subtopic": "electromagnetic_induction",
        "difficulty": 4,
        "question_type": "mcq",
        "question_text": "The induced emf in a coil of N turns due to change in magnetic flux phi is given by:",
        "options": {
            "A": "-N d(phi)/dt",
            "B": "N d(phi)/dt",
            "C": "-d(phi)/(N dt)",
            "D": "d(phi)/(N dt)",
        },
        "correct_answer": "-N d(phi)/dt",
        "explanation": "Faraday's law: induced emf = -N(d(phi)/dt). The negative sign indicates Lenz's law.",
        "tags": ["emi", "faradays_law", "magnetic_flux"],
        "source": "curated",
    },
    {
        "subject": "physics",
        "topic": "optics",
        "subtopic": "ray_optics",
        "difficulty": 3,
        "question_type": "mcq",
        "question_text": "A convex lens of focal length f forms a real image at a distance v from the lens. If the object distance is u, the lens formula is:",
        "options": {
            "A": "1/f = 1/v - 1/u",
            "B": "1/f = 1/u + 1/v",
            "C": "1/f = 1/v + 1/u",
            "D": "f = uv/(u+v)",
        },
        "correct_answer": "1/f = 1/v - 1/u",
        "explanation": "Lens formula: 1/f = 1/v - 1/u for real images (using sign convention where u is negative).",
        "tags": ["ray_optics", "lens_formula", "convex_lens"],
        "source": "curated",
    },
    {
        "subject": "chemistry",
        "topic": "physical_chemistry",
        "subtopic": "atomic_structure",
        "difficulty": 2,
        "question_type": "mcq",
        "question_text": "The maximum number of electrons that can be accommodated in a subshell with azimuthal quantum number l = 2 is:",
        "options": {"A": "6", "B": "10", "C": "2", "D": "14"},
        "correct_answer": "10",
        "explanation": "For l = 2 (d subshell), magnetic quantum number m = -2, -1, 0, +1, +2 (5 orbitals). Each orbital holds 2 electrons, so 5 x 2 = 10 electrons.",
        "tags": ["atomic_structure", "quantum_numbers", "electronic_configuration"],
        "source": "curated",
    },
    {
        "subject": "chemistry",
        "topic": "physical_chemistry",
        "subtopic": "chemical_bonding",
        "difficulty": 3,
        "question_type": "mcq",
        "question_text": "The hybridization of carbon in CH4 molecule is:",
        "options": {"A": "sp^3", "B": "sp^2", "C": "sp", "D": "sp^3d"},
        "correct_answer": "sp^3",
        "explanation": "Carbon in CH4 has 4 sigma bonds and no lone pairs, so steric number = 4, hybridization = sp^3",
        "tags": ["chemical_bonding", "hybridization", "vsepr"],
        "source": "curated",
    },
    {
        "subject": "chemistry",
        "topic": "organic_chemistry",
        "subtopic": "basic_organic",
        "difficulty": 2,
        "question_type": "mcq",
        "question_text": "The IUPAC name of CH3-CH2-CH2-OH is:",
        "options": {"A": "Propan-1-ol", "B": "Propan-2-ol", "C": "Propanol", "D": "Propyl alcohol"},
        "correct_answer": "Propan-1-ol",
        "explanation": "The longest chain has 3 carbons (propane). The -OH group is on carbon 1. So: Propan-1-ol",
        "tags": ["organic_chemistry", "iupac_nomenclature", "alcohols"],
        "source": "curated",
    },
    {
        "subject": "chemistry",
        "topic": "organic_chemistry",
        "subtopic": "hydrocarbons",
        "difficulty": 3,
        "question_type": "mcq",
        "question_text": "Which of the following is an aromatic hydrocarbon?",
        "options": {"A": "Benzene", "B": "Cyclohexane", "C": "Hex-1-ene", "D": "Hex-1-yne"},
        "correct_answer": "Benzene",
        "explanation": "Benzene (C6H6) is aromatic because it follows Hueckel's rule with 4n+2=6 pi electrons and has a planar cyclic conjugated structure.",
        "tags": ["hydrocarbons", "aromaticity", "benzene"],
        "source": "curated",
    },
    {
        "subject": "chemistry",
        "topic": "inorganic_chemistry",
        "subtopic": "periodic_table",
        "difficulty": 2,
        "question_type": "mcq",
        "question_text": "Which element has the highest electronegativity?",
        "options": {"A": "Fluorine", "B": "Chlorine", "C": "Oxygen", "D": "Nitrogen"},
        "correct_answer": "Fluorine",
        "explanation": "Fluorine has the highest electronegativity (approx 4.0 on Pauling scale) due to its small size and high nuclear charge.",
        "tags": ["periodic_table", "electronegativity", "periodic_trends"],
        "source": "curated",
    },
    {
        "subject": "mathematics",
        "topic": "algebra",
        "subtopic": "quadratic_equations",
        "difficulty": 2,
        "question_type": "mcq",
        "question_text": "The roots of the equation x^2 - 5x + 6 = 0 are:",
        "options": {"A": "2, 3", "B": "-2, -3", "C": "2, -3", "D": "-2, 3"},
        "correct_answer": "2, 3",
        "explanation": "x^2 - 5x + 6 = 0, (x-2)(x-3) = 0, x = 2 or x = 3",
        "tags": ["quadratic_equations", "roots", "factorization"],
        "source": "curated",
    },
    {
        "subject": "mathematics",
        "topic": "calculus",
        "subtopic": "differentiation",
        "difficulty": 3,
        "question_type": "mcq",
        "question_text": "The derivative of f(x) = sin(x^2) with respect to x is:",
        "options": {"A": "2x*cos(x^2)", "B": "cos(x^2)", "C": "2*cos(x^2)", "D": "x*cos(x^2)"},
        "correct_answer": "2x*cos(x^2)",
        "explanation": "Using chain rule: d/dx[sin(x^2)] = cos(x^2) * d/dx[x^2] = cos(x^2) * 2x = 2x*cos(x^2)",
        "tags": ["differentiation", "chain_rule", "trigonometric_functions"],
        "source": "curated",
    },
    {
        "subject": "mathematics",
        "topic": "calculus",
        "subtopic": "integration",
        "difficulty": 4,
        "question_type": "mcq",
        "question_text": "Integral of e^x * sin(x) dx equals:",
        "options": {
            "A": "e^x(sin x - cos x)/2 + C",
            "B": "e^x*sin x + C",
            "C": "e^x*cos x + C",
            "D": "e^x(sin x + cos x)/2 + C",
        },
        "correct_answer": "e^x(sin x - cos x)/2 + C",
        "explanation": "Using integration by parts twice: integral of e^x*sin(x) dx = e^x(sin x - cos x)/2 + C",
        "tags": ["integration", "integration_by_parts", "exponential_functions"],
        "source": "curated",
    },
    {
        "subject": "mathematics",
        "topic": "coordinate_geometry",
        "subtopic": "straight_lines",
        "difficulty": 2,
        "question_type": "mcq",
        "question_text": "The slope of a line passing through points (1, 2) and (3, 6) is:",
        "options": {"A": "2", "B": "4", "C": "1", "D": "3"},
        "correct_answer": "2",
        "explanation": "Slope = (y2-y1)/(x2-x1) = (6-2)/(3-1) = 4/2 = 2",
        "tags": ["straight_lines", "slope", "coordinate_geometry"],
        "source": "curated",
    },
    {
        "subject": "mathematics",
        "topic": "trigonometry",
        "subtopic": "basic_trig",
        "difficulty": 2,
        "question_type": "mcq",
        "question_text": "The value of sin^2(theta) + cos^2(theta) is:",
        "options": {"A": "1", "B": "0", "C": "sin(2theta)", "D": "cos(2theta)"},
        "correct_answer": "1",
        "explanation": "This is the fundamental Pythagorean trigonometric identity: sin^2(theta) + cos^2(theta) = 1",
        "tags": ["trigonometry", "identities", "pythagorean_identity"],
        "source": "curated",
    },
    {
        "subject": "physics",
        "topic": "mechanics",
        "subtopic": "friction",
        "difficulty": 3,
        "question_type": "mcq",
        "question_text": "A block of mass 5 kg is placed on a horizontal surface with coefficient of friction 0.4. What minimum force (in N) is required to start moving the block? (g = 10 m/s^2)",
        "options": {"A": "20 N", "B": "15 N", "C": "10 N", "D": "25 N"},
        "correct_answer": "20 N",
        "explanation": "Limiting friction = mu*N = mu*mg = 0.4 * 5 * 10 = 20 N. The applied force must exceed this to start motion.",
        "tags": ["friction", "limiting_friction", "force_calculation"],
        "source": "curated",
    },
    {
        "subject": "chemistry",
        "topic": "physical_chemistry",
        "subtopic": "equilibrium",
        "difficulty": 3,
        "question_type": "mcq",
        "question_text": "For a reaction A + B = C + D, the equilibrium constant Kc = 4.0. If we start with 1 mol each of A and B in a 1 L container, the equilibrium concentration of C is:",
        "options": {"A": "2/3 M", "B": "1/2 M", "C": "4/3 M", "D": "1 M"},
        "correct_answer": "2/3 M",
        "explanation": "Let x = concentration of C at equilibrium. Kc = [C][D]/([A][B]) = x^2/((1-x)(1-x)) = 4. Taking square root: x/(1-x) = 2, x = 2-2x, 3x = 2, x = 2/3",
        "tags": ["equilibrium", "equilibrium_constant", "chemical_equilibrium"],
        "source": "curated",
    },
]

SAMPLE_TEST_QUESTIONS = [
    {
        "subject": "physics",
        "topic": "mechanics",
        "subtopic": "kinematics",
        "difficulty": 3,
        "question_type": "mcq",
        "question_text": "A body starts from rest and accelerates uniformly at 2 m/s^2 for 5 seconds. The distance covered in the last 1 second is:",
        "options": {"A": "9 m", "B": "10 m", "C": "5 m", "D": "7 m"},
        "correct_answer": "9 m",
        "explanation": "Distance in 5s: s5 = 1/2(2)(25) = 25m. Distance in 4s: s4 = 1/2(2)(16) = 16m. Distance in last 1s = 25 - 16 = 9m",
        "tags": ["kinematics", "uniform_acceleration", "jee_main"],
        "year": 2023,
        "exam_type": "JEE_Main",
    },
    {
        "subject": "physics",
        "topic": "electrostatics",
        "subtopic": "electrostatics",
        "difficulty": 4,
        "question_type": "mcq",
        "question_text": "Two identical conducting spheres carrying charges +6 uC and -2 uC are brought in contact and then separated. The charge on each sphere is:",
        "options": {"A": "+2 uC", "B": "+4 uC", "C": "-2 uC", "D": "+6 uC"},
        "correct_answer": "+2 uC",
        "explanation": "Total charge = +6 + (-2) = +4 uC. By symmetry, each sphere gets half: +4/2 = +2 uC each.",
        "tags": ["electrostatics", "charge_distribution", "jee_advanced"],
        "year": 2022,
        "exam_type": "JEE_Advanced",
    },
    {
        "subject": "chemistry",
        "topic": "physical_chemistry",
        "subtopic": "chemical_kinetics",
        "difficulty": 3,
        "question_type": "mcq",
        "question_text": "For a first-order reaction, the half-life is 100 seconds. The rate constant k is:",
        "options": {
            "A": "6.93 * 10^-3 s^-1",
            "B": "0.693 s^-1",
            "C": "6.93 s^-1",
            "D": "0.0693 s^-1",
        },
        "correct_answer": "6.93 * 10^-3 s^-1",
        "explanation": "For first-order: t_half = 0.693/k. So k = 0.693/100 = 6.93 * 10^-3 s^-1",
        "tags": ["chemical_kinetics", "half_life", "rate_constant", "jee_main"],
        "year": 2023,
        "exam_type": "JEE_Main",
    },
    {
        "subject": "mathematics",
        "topic": "calculus",
        "subtopic": "application_of_derivatives",
        "difficulty": 4,
        "question_type": "mcq",
        "question_text": "The maximum value of f(x) = x^3 - 3x^2 + 2 in the interval [0, 3] is:",
        "options": {"A": "2", "B": "0", "C": "4", "D": "3"},
        "correct_answer": "2",
        "explanation": "f'(x) = 3x^2 - 6x = 3x(x-2) = 0 at x=0,2. f(0)=2, f(2)=-2, f(3)=2. Maximum = 2",
        "tags": ["application_of_derivatives", "maxima_minima", "jee_advanced"],
        "year": 2022,
        "exam_type": "JEE_Advanced",
    },
    {
        "subject": "mathematics",
        "topic": "algebra",
        "subtopic": "matrices",
        "difficulty": 3,
        "question_type": "mcq",
        "question_text": "If A is a 3x3 matrix with |A| = 2, then |2A| equals:",
        "options": {"A": "16", "B": "8", "C": "4", "D": "2"},
        "correct_answer": "16",
        "explanation": "For an nxn matrix, |kA| = k^n|A|. Here n=3, k=2, so |2A| = 8 * 2 = 16",
        "tags": ["matrices", "determinants", "jee_main"],
        "year": 2023,
        "exam_type": "JEE_Main",
    },
    {
        "subject": "chemistry",
        "topic": "organic_chemistry",
        "subtopic": "haloalkanes",
        "difficulty": 3,
        "question_type": "mcq",
        "question_text": "The product formed when CH3CH2Br is treated with aqueous KOH is:",
        "options": {"A": "CH3CH2OH", "B": "CH2=CH2", "C": "CH3CHO", "D": "CH3COOH"},
        "correct_answer": "CH3CH2OH",
        "explanation": "Aqueous KOH gives nucleophilic substitution (SN2), replacing Br with OH to form ethanol.",
        "tags": ["haloalkanes", "nucleophilic_substitution", "sn2", "jee_main"],
        "year": 2022,
        "exam_type": "JEE_Main",
    },
    {
        "subject": "physics",
        "topic": "optics",
        "subtopic": "wave_optics",
        "difficulty": 4,
        "question_type": "mcq",
        "question_text": "In Young's double-slit experiment, the fringe width beta is given by:",
        "options": {"A": "lambda*D/d", "B": "lambda*d/D", "C": "d*D/lambda", "D": "lambda/(d*D)"},
        "correct_answer": "lambda*D/d",
        "explanation": "Fringe width beta = lambda*D/d, where lambda = wavelength, D = distance to screen, d = slit separation.",
        "tags": ["wave_optics", "youngs_experiment", "interference", "jee_advanced"],
        "year": 2023,
        "exam_type": "JEE_Advanced",
    },
    {
        "subject": "mathematics",
        "topic": "vector_3d",
        "subtopic": "vectors",
        "difficulty": 3,
        "question_type": "mcq",
        "question_text": "The dot product of two perpendicular vectors is:",
        "options": {"A": "0", "B": "1", "C": "-1", "D": "product of magnitudes"},
        "correct_answer": "0",
        "explanation": "For perpendicular vectors, theta = 90 degrees, cos(90) = 0, so a.b = |a||b|cos(90) = 0",
        "tags": ["vectors", "dot_product", "perpendicular_vectors", "jee_main"],
        "year": 2023,
        "exam_type": "JEE_Main",
    },
]

WEAK_STUDENT_TOPICS = [
    ("Arjun Sharma", "physics", "mechanics", "rotational_motion", 49),
    ("Arjun Sharma", "physics", "mechanics", "friction", 61),
    ("Priya Patel", "physics", "electrostatics", "electrostatics", 55),
    ("Priya Patel", "chemistry", "physical_chemistry", "chemical_bonding", 58),
    ("Rahul Verma", "mathematics", "calculus", "differentiation", 45),
    ("Rahul Verma", "physics", "mechanics", "kinematics", 52),
    ("Sneha Gupta", "chemistry", "organic_chemistry", "hydrocarbons", 50),
    ("Sneha Gupta", "chemistry", "physical_chemistry", "equilibrium", 48),
    ("Amit Kumar", "mathematics", "algebra", "quadratic_equations", 60),
    ("Amit Kumar", "mathematics", "calculus", "integration", 42),
]


async def seed():
    settings = get_config()
    setup_logging(settings.app.log_level)

    logger.info("=" * 60)
    logger.info("Studob MVP - Seed Data Script")
    logger.info("=" * 60)

    logger.info("Initializing database...")
    db_engine = DatabaseEngine(url=settings.database.rdbms.url, echo=False)
    await db_engine.init_db()
    session_factory = db_engine.get_session_factory()

    # Seed students
    logger.info("Seeding students...")
    student_service = StudentProfileService(session_factory)
    created_students = {}
    for s in SAMPLE_STUDENTS:
        existing = await student_service.get_student_by_name(s["name"])
        if existing:
            student = existing
            logger.info(f"  Student exists: {s['name']} (id={student.id})")
        else:
            from studob.schemas.student import StudentCreate

            data = StudentCreate(**s)
            student = await student_service.create_student(data)
            logger.info(f"  Created student: {s['name']} (id={student.id})")
        created_students[s["name"]] = student

    # Seed mastery scores
    logger.info("Seeding initial mastery scores...")
    async with session_factory() as session:
        for name, subject, topic, subtopic, score in WEAK_STUDENT_TOPICS:
            student = created_students.get(name)
            if not student:
                continue
            result = await session.execute(
                select(MasteryScore).where(
                    MasteryScore.student_id == student.id, MasteryScore.subtopic == subtopic
                )
            )
            existing = result.scalar_one_or_none()
            if not existing:
                ms = MasteryScore(
                    student_id=student.id,
                    subject=subject,
                    topic=topic,
                    subtopic=subtopic,
                    score=float(score),
                    confidence=0.7,
                    attempts=5,
                )
                session.add(ms)
        await session.commit()
        logger.info(f"  Seeded {len(WEAK_STUDENT_TOPICS)} mastery scores")

    # Seed app questions
    logger.info("Seeding app questions (practice bank)...")
    async with session_factory() as session:
        count = (await session.execute(select(func.count()).select_from(AppQuestion))).scalar()
    app_q_service = AppQuestionService(session_factory)
    created_app_questions = []
    if count == 0:
        for q_data in SAMPLE_APP_QUESTIONS:
            q = await app_q_service.create_question(AppQuestionCreate(**q_data))
            created_app_questions.append(q)
        logger.info(f"  Created {len(created_app_questions)} app questions")
    else:
        logger.info(f"  {count} app questions exist, skipping")
        async with session_factory() as session:
            result = await session.execute(select(AppQuestion))
            created_app_questions = result.scalars().all()

    # Seed test questions
    logger.info("Seeding test questions (assessment bank)...")
    async with session_factory() as session:
        count = (await session.execute(select(func.count()).select_from(TestQuestion))).scalar()
    if count == 0:
        test_q_service = TestQuestionService(session_factory)
        for q_data in SAMPLE_TEST_QUESTIONS:
            await test_q_service.create_question(TestQuestionCreate(**q_data))
        logger.info(f"  Created {len(SAMPLE_TEST_QUESTIONS)} test questions")
    else:
        logger.info(f"  {count} test questions exist, skipping")

    # Build FAISS vector index
    logger.info("Building vector index for app questions...")
    generator = EmbeddingGenerator(settings.database.vector.dimension)
    vector_store = VectorStoreService(
        dimension=settings.database.vector.dimension,
        index_path=settings.database.vector.index_path,
    )
    embedding_service = EmbeddingService(generator, vector_store, get_logger("embeddings"))

    if os.path.exists(settings.database.vector.index_path):
        try:
            await vector_store.load()
            logger.info("  Loaded existing vector index")
        except Exception as e:
            logger.warning(f"  Could not load vector index: {e}")

    item_count = await vector_store.get_item_count()
    if item_count == 0 and created_app_questions:
        items = []
        for q in created_app_questions:
            text = f"{q.subject} {q.topic} {q.subtopic}: {q.question_text}"
            items.append(
                (
                    str(q.id),
                    text,
                    {
                        "subject": q.subject,
                        "topic": q.topic,
                        "subtopic": q.subtopic,
                        "difficulty": q.difficulty,
                        "question_type": q.question_type,
                    },
                )
            )
        await embedding_service.embed_and_store_batch(items)
        await vector_store.save()
        logger.info(f"  Indexed {len(items)} questions into FAISS")
    else:
        logger.info(f"  Vector index has {item_count} items, skipping")

    # Verify concept graph data
    graph_path = settings.database.graph.data_path
    if os.path.exists(graph_path):
        with open(graph_path) as f:
            graph_data = json.load(f)
        logger.info(
            f"  Concept graph: {len(graph_data['nodes'])} nodes, {len(graph_data['edges'])} edges"
        )

    # Seed past session history (5-6 sessions per student with attempts)
    logger.info("Seeding past session history...")
    from datetime import UTC, datetime, timedelta

    from studob.database.models import Attempt, MistakeRecord, Session
    from studob.student.session_memory import SessionMemoryService

    _ = SessionMemoryService(session_factory)

    past_session_templates = [
        {
            "type": "practice",
            "concept": "Motion in 1D",
            "subject": "physics",
            "topic": "mechanics",
            "q_ids": [1],
            "correct": True,
            "hints": 1,
            "time": 45.0,
            "days_ago": 14,
        },
        {
            "type": "practice",
            "concept": "Newton's Laws",
            "subject": "physics",
            "topic": "mechanics",
            "q_ids": [2],
            "correct": False,
            "hints": 2,
            "time": 120.0,
            "days_ago": 13,
        },
        {
            "type": "assessment",
            "concept": "physics",
            "subject": "physics",
            "topic": "mechanics",
            "q_ids": [1, 2, 4, 7, 8],
            "correct": True,
            "hints": 0,
            "time": 30.0,
            "days_ago": 10,
        },
        {
            "type": "practice",
            "concept": "Electrostatics",
            "subject": "physics",
            "topic": "electrostatics",
            "q_ids": [5],
            "correct": False,
            "hints": 3,
            "time": 180.0,
            "days_ago": 8,
        },
        {
            "type": "practice",
            "concept": "Chemical Bonding",
            "subject": "chemistry",
            "topic": "physical_chemistry",
            "q_ids": [9],
            "correct": True,
            "hints": 0,
            "time": 25.0,
            "days_ago": 7,
        },
        {
            "type": "assessment",
            "concept": "chemistry",
            "subject": "chemistry",
            "topic": "physical_chemistry",
            "q_ids": [9, 10, 11, 12, 13],
            "correct": False,
            "hints": 0,
            "time": 60.0,
            "days_ago": 5,
        },
        {
            "type": "practice",
            "concept": "Differentiation",
            "subject": "mathematics",
            "topic": "calculus",
            "q_ids": [15],
            "correct": True,
            "hints": 1,
            "time": 55.0,
            "days_ago": 4,
        },
        {
            "type": "assessment",
            "concept": "mathematics",
            "subject": "mathematics",
            "topic": "calculus",
            "q_ids": [15, 16, 14, 17, 18],
            "correct": False,
            "hints": 0,
            "time": 90.0,
            "days_ago": 3,
        },
    ]

    async with session_factory() as db_sess:
        for student_name, student_rec in created_students.items():
            student_id = student_rec.id
            for i, tmpl in enumerate(past_session_templates):
                sess_id = f"past-{student_name.lower().replace(' ', '-')}-{i}"
                started = datetime.now(UTC) - timedelta(days=tmpl["days_ago"], hours=i * 2)
                ended = started + timedelta(
                    seconds=tmpl["time"] * 2 if tmpl["type"] == "assessment" else 300
                )

                existing = await db_sess.execute(select(Session).where(Session.id == sess_id))
                if existing.scalar_one_or_none():
                    continue

                q_count = len(tmpl["q_ids"])
                correct_count = q_count if tmpl["correct"] else max(0, q_count - 2)

                sess = Session(
                    id=sess_id,
                    student_id=student_id,
                    session_type=tmpl["type"],
                    started_at=started,
                    ended_at=ended,
                    questions_count=q_count,
                    correct_count=correct_count,
                    mastery_delta=5.0 if tmpl["correct"] else -8.0,
                )
                db_sess.add(sess)

                for qi, qid in enumerate(tmpl["q_ids"]):
                    is_correct = (
                        tmpl["correct"] if tmpl["type"] == "practice" else (qi < correct_count)
                    )
                    ans_time = (
                        tmpl["time"] if tmpl["type"] == "practice" else (tmpl["time"] / q_count)
                    )
                    attempt = Attempt(
                        student_id=student_id,
                        question_id=qid,
                        question_type=tmpl["type"],
                        is_correct=is_correct,
                        response_time_seconds=ans_time + qi * 5,
                        hints_used=tmpl["hints"] if qi == 0 else 0,
                        retry_count=0 if is_correct else 1,
                        answered_at=started + timedelta(seconds=(qi + 1) * (ans_time + 10)),
                        session_id=sess_id,
                    )
                    db_sess.add(attempt)

                    if not is_correct:
                        mr = MistakeRecord(
                            student_id=student_id,
                            question_id=qid,
                            session_id=sess_id,
                            error_category="concept_misunderstood"
                            if qi % 2 == 0
                            else "calculation_error",
                            concept_tag=tmpl["concept"],
                            confidence=0.7,
                            diagnosis_detail={},
                            created_at=started + timedelta(seconds=(qi + 1) * ans_time),
                        )
                        db_sess.add(mr)

                ms_result = await db_sess.execute(
                    select(MasteryScore).where(
                        MasteryScore.student_id == student_id,
                        MasteryScore.subtopic == tmpl["concept"],
                    )
                )
                existing_ms = ms_result.scalar_one_or_none()
                if existing_ms and tmpl["correct"]:
                    existing_ms.score = min(100.0, existing_ms.score + 3.0)
                    existing_ms.attempts += q_count
                elif existing_ms and not tmpl["correct"]:
                    existing_ms.score = max(0.0, existing_ms.score - 5.0)
                    existing_ms.attempts += q_count
                elif tmpl["correct"]:
                    ms = MasteryScore(
                        student_id=student_id,
                        subject=tmpl["subject"],
                        topic=tmpl["topic"],
                        subtopic=tmpl["concept"],
                        score=65.0,
                        confidence=0.6,
                        attempts=q_count,
                        last_updated=datetime.now(UTC),
                    )
                    db_sess.add(ms)

        await db_sess.commit()
    logger.info("  Past session history seeded (8 sessions per student)")

    logger.info("=" * 60)
    logger.info("Seed complete! Database, vector index, and sample data ready.")
    logger.info("=" * 60)

    await db_engine.close_db()


if __name__ == "__main__":
    asyncio.run(seed())

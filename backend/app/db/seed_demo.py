"""Campus Intelligence Demonstration Database Seeder.

Creates a coherent, multi-table relational schema with authentic synthetic academic
records, foreign key constraints, composite/primary keys, indices, and referential integrity.
All records are deterministic and strictly synthetic.
"""

import os
import sqlite3
from pathlib import Path
from typing import Optional
from app.core.logging import get_logger

logger = get_logger("seed_demo")


DEMO_DB_ID = "campus_intelligence"
DEMO_DB_NAME = "Campus Intelligence"
DEMO_DB_FILENAME = "campus_intelligence.db"
DEMO_DB_DESCRIPTION = (
    "Academic demonstration database covering students, faculty, departments, "
    "courses, enrollments, attendance, and assessments with strict relational constraints."
)


def seed_campus_intelligence_db(db_path: Path, force: bool = False) -> bool:
    """Create and seed the Campus Intelligence SQLite database.

    Args:
        db_path: Filesystem path where the SQLite database should reside.
        force: If True, recreates the schema and repopulates all tables.

    Returns:
        bool: True if created or verified successfully.
    """
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    if db_path.exists() and not force:
        try:
            conn = sqlite3.connect(str(db_path))
            conn.execute("PRAGMA foreign_keys = ON;")
            cursor = conn.cursor()
            cursor.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='students';")
            count = cursor.fetchone()[0]
            conn.close()
            if count > 0:
                logger.info(f"Campus Intelligence database already exists and is valid at {db_path}")
                return True
        except Exception as e:
            logger.warning(f"Existing demo database check failed ({e}); recreating: {db_path}")

    # Remove existing if force recreate
    if db_path.exists() and force:
        try:
            os.remove(db_path)
        except OSError:
            pass

    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute("PRAGMA foreign_keys = ON;")
        cursor = conn.cursor()

        # 1. Departments
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS departments (
                department_id VARCHAR(10) PRIMARY KEY,
                department_name VARCHAR(100) NOT NULL UNIQUE,
                building VARCHAR(50) NOT NULL,
                budget REAL NOT NULL
            );
        """)

        # 2. Faculty
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS faculty (
                faculty_id VARCHAR(10) PRIMARY KEY,
                first_name VARCHAR(50) NOT NULL,
                last_name VARCHAR(50) NOT NULL,
                email VARCHAR(100) NOT NULL UNIQUE,
                department_id VARCHAR(10) NOT NULL,
                hire_date DATE NOT NULL,
                salary REAL NOT NULL,
                FOREIGN KEY (department_id) REFERENCES departments(department_id) ON UPDATE CASCADE ON DELETE RESTRICT
            );
        """)

        # 3. Students
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                student_id VARCHAR(10) PRIMARY KEY,
                first_name VARCHAR(50) NOT NULL,
                last_name VARCHAR(50) NOT NULL,
                email VARCHAR(100) NOT NULL UNIQUE,
                department_id VARCHAR(10) NOT NULL,
                enrollment_year INTEGER NOT NULL,
                gpa REAL NOT NULL CHECK(gpa >= 0.0 AND gpa <= 4.0),
                FOREIGN KEY (department_id) REFERENCES departments(department_id) ON UPDATE CASCADE ON DELETE RESTRICT
            );
        """)

        # 4. Courses
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS courses (
                course_id VARCHAR(10) PRIMARY KEY,
                course_title VARCHAR(100) NOT NULL,
                credits INTEGER NOT NULL CHECK(credits >= 1 AND credits <= 6),
                department_id VARCHAR(10) NOT NULL,
                faculty_id VARCHAR(10),
                FOREIGN KEY (department_id) REFERENCES departments(department_id) ON UPDATE CASCADE ON DELETE RESTRICT,
                FOREIGN KEY (faculty_id) REFERENCES faculty(faculty_id) ON UPDATE CASCADE ON DELETE SET NULL
            );
        """)

        # 5. Enrollments
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS enrollments (
                enrollment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id VARCHAR(10) NOT NULL,
                course_id VARCHAR(10) NOT NULL,
                semester VARCHAR(20) NOT NULL,
                grade VARCHAR(2),
                grade_points REAL,
                FOREIGN KEY (student_id) REFERENCES students(student_id) ON UPDATE CASCADE ON DELETE CASCADE,
                FOREIGN KEY (course_id) REFERENCES courses(course_id) ON UPDATE CASCADE ON DELETE CASCADE,
                UNIQUE(student_id, course_id, semester)
            );
        """)

        # 6. Attendance
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id VARCHAR(10) NOT NULL,
                course_id VARCHAR(10) NOT NULL,
                classes_held INTEGER NOT NULL CHECK(classes_held > 0),
                classes_attended INTEGER NOT NULL CHECK(classes_attended >= 0),
                attendance_percentage REAL NOT NULL,
                FOREIGN KEY (student_id) REFERENCES students(student_id) ON UPDATE CASCADE ON DELETE CASCADE,
                FOREIGN KEY (course_id) REFERENCES courses(course_id) ON UPDATE CASCADE ON DELETE CASCADE,
                CHECK(classes_attended <= classes_held)
            );
        """)

        # 7. Assessments
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS assessments (
                assessment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id VARCHAR(10) NOT NULL,
                assessment_name VARCHAR(50) NOT NULL,
                max_score REAL NOT NULL CHECK(max_score > 0),
                weight_percentage REAL NOT NULL CHECK(weight_percentage > 0),
                FOREIGN KEY (course_id) REFERENCES courses(course_id) ON UPDATE CASCADE ON DELETE CASCADE
            );
        """)

        # Create Indices for join performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_faculty_dept ON faculty(department_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_students_dept ON students(department_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_courses_dept ON courses(department_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_courses_faculty ON courses(faculty_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_enrollments_student ON enrollments(student_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_enrollments_course ON enrollments(course_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_attendance_student_course ON attendance(student_id, course_id);")

        # Populate Departments (5)
        departments_data = [
            ("DEP-CS", "Computer Science", "Turing Hall", 850000.0),
            ("DEP-DS", "Data Science & AI", "Lovelace Center", 720000.0),
            ("DEP-EE", "Electrical Engineering", "Maxwell Building", 680000.0),
            ("DEP-MATH", "Mathematics & Statistics", "Euler Hall", 450000.0),
            ("DEP-PHYS", "Physics & Quantum", "Feynman Lab", 510000.0),
        ]
        cursor.executemany(
            "INSERT INTO departments (department_id, department_name, building, budget) VALUES (?, ?, ?, ?);",
            departments_data,
        )

        # Populate Faculty (10)
        faculty_data = [
            ("FAC-101", "Alan", "Mitchell", "a.mitchell@campus.edu", "DEP-CS", "2018-08-15", 115000.0),
            ("FAC-102", "Elena", "Rostova", "e.rostova@campus.edu", "DEP-CS", "2020-01-10", 98000.0),
            ("FAC-103", "Marcus", "Chen", "m.chen@campus.edu", "DEP-DS", "2019-07-01", 125000.0),
            ("FAC-104", "Priya", "Sharma", "p.sharma@campus.edu", "DEP-DS", "2021-09-01", 102000.0),
            ("FAC-105", "David", "Kowalski", "d.kowalski@campus.edu", "DEP-EE", "2015-03-20", 110000.0),
            ("FAC-106", "Sarah", "Jenkins", "s.jenkins@campus.edu", "DEP-EE", "2022-01-15", 92000.0),
            ("FAC-107", "Leon", "Vanderbilt", "l.vanderbilt@campus.edu", "DEP-MATH", "2012-09-01", 118000.0),
            ("FAC-108", "Amara", "Okonkwo", "a.okonkwo@campus.edu", "DEP-MATH", "2021-03-15", 95000.0),
            ("FAC-109", "Niels", "Bohr-Svensson", "n.svensson@campus.edu", "DEP-PHYS", "2016-11-01", 105000.0),
            ("FAC-110", "Chloe", "Dubois", "c.dubois@campus.edu", "DEP-PHYS", "2023-02-01", 88000.0),
        ]
        cursor.executemany(
            "INSERT INTO faculty (faculty_id, first_name, last_name, email, department_id, hire_date, salary) VALUES (?, ?, ?, ?, ?, ?, ?);",
            faculty_data,
        )

        # Populate Students (25)
        students_data = [
            ("STU-1001", "Lucas", "Bennett", "lucas.b@student.campus.edu", "DEP-CS", 2022, 3.85),
            ("STU-1002", "Aria", "Patel", "aria.p@student.campus.edu", "DEP-CS", 2022, 3.92),
            ("STU-1003", "Mateo", "Silva", "mateo.s@student.campus.edu", "DEP-CS", 2023, 3.45),
            ("STU-1004", "Zoe", "Kaufman", "zoe.k@student.campus.edu", "DEP-CS", 2021, 3.70),
            ("STU-1005", "Ethan", "Nakamura", "ethan.n@student.campus.edu", "DEP-CS", 2023, 2.95),
            ("STU-1006", "Maya", "Al-Mansoor", "maya.a@student.campus.edu", "DEP-DS", 2022, 3.88),
            ("STU-1007", "Liam", "O'Connor", "liam.o@student.campus.edu", "DEP-DS", 2023, 3.65),
            ("STU-1008", "Sofia", "Ramirez", "sofia.r@student.campus.edu", "DEP-DS", 2021, 3.95),
            ("STU-1009", "Noah", "Kim", "noah.k@student.campus.edu", "DEP-DS", 2022, 3.20),
            ("STU-1010", "Hannah", "Larsson", "hannah.l@student.campus.edu", "DEP-DS", 2023, 3.55),
            ("STU-1011", "Gabriel", "Costa", "gabriel.c@student.campus.edu", "DEP-EE", 2021, 3.40),
            ("STU-1012", "Chloe", "Zhang", "chloe.z@student.campus.edu", "DEP-EE", 2022, 3.78),
            ("STU-1013", "Benjamin", "Fischer", "benjamin.f@student.campus.edu", "DEP-EE", 2023, 3.10),
            ("STU-1014", "Ananya", "Deshmukh", "ananya.d@student.campus.edu", "DEP-EE", 2022, 3.90),
            ("STU-1015", "Oliver", "Wong", "oliver.w@student.campus.edu", "DEP-EE", 2021, 2.85),
            ("STU-1016", "Emma", "Goldberg", "emma.g@student.campus.edu", "DEP-MATH", 2022, 3.96),
            ("STU-1017", "Leo", "Takahashi", "leo.t@student.campus.edu", "DEP-MATH", 2023, 3.72),
            ("STU-1018", "Isabella", "Morales", "isabella.m@student.campus.edu", "DEP-MATH", 2021, 3.60),
            ("STU-1019", "Alexander", "Ivanov", "alexander.i@student.campus.edu", "DEP-MATH", 2022, 3.35),
            ("STU-1020", "Grace", "Adeyemi", "grace.a@student.campus.edu", "DEP-MATH", 2023, 3.82),
            ("STU-1021", "Julian", "Richter", "julian.r@student.campus.edu", "DEP-PHYS", 2022, 3.68),
            ("STU-1022", "Layla", "Hassan", "layla.h@student.campus.edu", "DEP-PHYS", 2021, 3.89),
            ("STU-1023", "Daniel", "Kowalski Jr", "daniel.k@student.campus.edu", "DEP-PHYS", 2023, 3.25),
            ("STU-1024", "Mia", "Fontaine", "mia.f@student.campus.edu", "DEP-PHYS", 2022, 3.75),
            ("STU-1025", "Samir", "Gupte", "samir.g@student.campus.edu", "DEP-PHYS", 2023, 3.50),
        ]
        cursor.executemany(
            "INSERT INTO students (student_id, first_name, last_name, email, department_id, enrollment_year, gpa) VALUES (?, ?, ?, ?, ?, ?, ?);",
            students_data,
        )

        # Populate Courses (10)
        courses_data = [
            ("CS-101", "Introduction to Algorithms", 4, "DEP-CS", "FAC-101"),
            ("CS-202", "Relational Database Systems", 4, "DEP-CS", "FAC-102"),
            ("DS-301", "Machine Learning & Neural Networks", 4, "DEP-DS", "FAC-103"),
            ("DS-302", "Big Data Analytics & Pipeline Engineering", 3, "DEP-DS", "FAC-104"),
            ("EE-201", "Digital Circuit Design & FPGA", 4, "DEP-EE", "FAC-105"),
            ("EE-305", "Embedded Microcontrollers & IoT", 3, "DEP-EE", "FAC-106"),
            ("MATH-210", "Linear Algebra for Computing", 3, "DEP-MATH", "FAC-107"),
            ("MATH-320", "Probability Theory & Stochastic Processes", 4, "DEP-MATH", "FAC-108"),
            ("PHYS-150", "Classical Mechanics & Thermodynamics", 4, "DEP-PHYS", "FAC-109"),
            ("PHYS-301", "Quantum Mechanics & Semiconductor Physics", 4, "DEP-PHYS", "FAC-110"),
        ]
        cursor.executemany(
            "INSERT INTO courses (course_id, course_title, credits, department_id, faculty_id) VALUES (?, ?, ?, ?, ?);",
            courses_data,
        )

        # Populate Enrollments (40 records)
        enrollments_data = [
            ("STU-1001", "CS-101", "Fall 2023", "A", 4.0),
            ("STU-1001", "CS-202", "Spring 2024", "A", 4.0),
            ("STU-1001", "MATH-210", "Fall 2023", "B+", 3.3),
            ("STU-1002", "CS-101", "Fall 2023", "A", 4.0),
            ("STU-1002", "CS-202", "Spring 2024", "A-", 3.7),
            ("STU-1002", "DS-301", "Spring 2024", "A", 4.0),
            ("STU-1003", "CS-101", "Fall 2023", "B", 3.0),
            ("STU-1003", "CS-202", "Spring 2024", "B+", 3.3),
            ("STU-1004", "CS-202", "Spring 2024", "A", 4.0),
            ("STU-1004", "DS-301", "Fall 2023", "B+", 3.3),
            ("STU-1005", "CS-101", "Fall 2023", "C+", 2.3),
            ("STU-1005", "MATH-210", "Spring 2024", "C", 2.0),
            ("STU-1006", "DS-301", "Fall 2023", "A", 4.0),
            ("STU-1006", "DS-302", "Spring 2024", "A-", 3.7),
            ("STU-1006", "MATH-210", "Fall 2023", "A", 4.0),
            ("STU-1007", "DS-301", "Fall 2023", "B+", 3.3),
            ("STU-1007", "DS-302", "Spring 2024", "B", 3.0),
            ("STU-1008", "DS-301", "Fall 2023", "A", 4.0),
            ("STU-1008", "DS-302", "Spring 2024", "A", 4.0),
            ("STU-1008", "MATH-320", "Fall 2023", "A", 4.0),
            ("STU-1009", "DS-301", "Fall 2023", "B-", 2.7),
            ("STU-1010", "DS-302", "Spring 2024", "B+", 3.3),
            ("STU-1011", "EE-201", "Fall 2023", "B", 3.0),
            ("STU-1011", "EE-305", "Spring 2024", "B+", 3.3),
            ("STU-1012", "EE-201", "Fall 2023", "A-", 3.7),
            ("STU-1012", "EE-305", "Spring 2024", "A", 4.0),
            ("STU-1013", "EE-201", "Fall 2023", "B-", 2.7),
            ("STU-1014", "EE-201", "Fall 2023", "A", 4.0),
            ("STU-1014", "EE-305", "Spring 2024", "A", 4.0),
            ("STU-1015", "EE-201", "Fall 2023", "C+", 2.3),
            ("STU-1016", "MATH-210", "Fall 2023", "A", 4.0),
            ("STU-1016", "MATH-320", "Spring 2024", "A", 4.0),
            ("STU-1017", "MATH-210", "Fall 2023", "A-", 3.7),
            ("STU-1018", "MATH-320", "Spring 2024", "B+", 3.3),
            ("STU-1019", "MATH-210", "Fall 2023", "B", 3.0),
            ("STU-1020", "MATH-210", "Fall 2023", "A", 4.0),
            ("STU-1021", "PHYS-150", "Fall 2023", "B+", 3.3),
            ("STU-1021", "PHYS-301", "Spring 2024", "A-", 3.7),
            ("STU-1022", "PHYS-150", "Fall 2023", "A", 4.0),
            ("STU-1022", "PHYS-301", "Spring 2024", "A", 4.0),
        ]
        cursor.executemany(
            "INSERT INTO enrollments (student_id, course_id, semester, grade, grade_points) VALUES (?, ?, ?, ?, ?);",
            enrollments_data,
        )

        # Populate Attendance (30 records)
        attendance_data = [
            ("STU-1001", "CS-101", 32, 31, 96.88),
            ("STU-1001", "CS-202", 30, 29, 96.67),
            ("STU-1002", "CS-101", 32, 32, 100.0),
            ("STU-1002", "CS-202", 30, 28, 93.33),
            ("STU-1003", "CS-101", 32, 26, 81.25),
            ("STU-1003", "CS-202", 30, 25, 83.33),
            ("STU-1004", "CS-202", 30, 29, 96.67),
            ("STU-1005", "CS-101", 32, 22, 68.75),
            ("STU-1006", "DS-301", 28, 27, 96.43),
            ("STU-1006", "DS-302", 24, 23, 95.83),
            ("STU-1007", "DS-301", 28, 25, 89.29),
            ("STU-1007", "DS-302", 24, 22, 91.67),
            ("STU-1008", "DS-301", 28, 28, 100.0),
            ("STU-1008", "DS-302", 24, 24, 100.0),
            ("STU-1009", "DS-301", 28, 21, 75.0),
            ("STU-1010", "DS-302", 24, 21, 87.5),
            ("STU-1011", "EE-201", 30, 27, 90.0),
            ("STU-1011", "EE-305", 26, 24, 92.31),
            ("STU-1012", "EE-201", 30, 29, 96.67),
            ("STU-1012", "EE-305", 26, 26, 100.0),
            ("STU-1013", "EE-201", 30, 23, 76.67),
            ("STU-1014", "EE-201", 30, 30, 100.0),
            ("STU-1014", "EE-305", 26, 25, 96.15),
            ("STU-1015", "EE-201", 30, 21, 70.0),
            ("STU-1016", "MATH-210", 28, 28, 100.0),
            ("STU-1016", "MATH-320", 30, 29, 96.67),
            ("STU-1017", "MATH-210", 28, 26, 92.86),
            ("STU-1018", "MATH-320", 30, 27, 90.0),
            ("STU-1021", "PHYS-150", 32, 29, 90.62),
            ("STU-1022", "PHYS-150", 32, 32, 100.0),
        ]
        cursor.executemany(
            "INSERT INTO attendance (student_id, course_id, classes_held, classes_attended, attendance_percentage) VALUES (?, ?, ?, ?, ?);",
            attendance_data,
        )

        # Populate Assessments (15)
        assessments_data = [
            ("CS-101", "Midterm Exam", 100.0, 30.0),
            ("CS-101", "Programming Assignments", 100.0, 30.0),
            ("CS-101", "Final Examination", 100.0, 40.0),
            ("CS-202", "SQL Schema Design Project", 50.0, 25.0),
            ("CS-202", "Query Optimization Lab", 50.0, 25.0),
            ("CS-202", "Comprehensive Final", 100.0, 50.0),
            ("DS-301", "Model Training Benchmark", 100.0, 40.0),
            ("DS-301", "Deep Learning Project", 100.0, 60.0),
            ("DS-302", "ETL Pipeline Deployment", 100.0, 50.0),
            ("DS-302", "Streaming Analytics Exam", 100.0, 50.0),
            ("EE-201", "FPGA Hardware Lab", 100.0, 50.0),
            ("EE-305", "Sensor Mesh Prototype", 100.0, 50.0),
            ("MATH-210", "Matrix Algebra Midterm", 100.0, 40.0),
            ("MATH-320", "Stochastic Modeling Paper", 100.0, 50.0),
            ("PHYS-150", "Mechanics Laboratory Portfolio", 100.0, 50.0),
        ]
        cursor.executemany(
            "INSERT INTO assessments (course_id, assessment_name, max_score, weight_percentage) VALUES (?, ?, ?, ?);",
            assessments_data,
        )

        # Verify foreign key integrity
        cursor.execute("PRAGMA foreign_key_check;")
        fk_violations = cursor.fetchall()
        if fk_violations:
            raise RuntimeError(f"Foreign key integrity violations detected during seeding: {fk_violations}")

        conn.commit()
        logger.info(f"Successfully seeded Campus Intelligence database at {db_path} with 7 tables.")
        return True

    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to seed Campus Intelligence database: {e}")
        raise
    finally:
        conn.close()

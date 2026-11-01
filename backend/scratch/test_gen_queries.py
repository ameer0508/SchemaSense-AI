import sqlite3
from pathlib import Path

db_path = Path('data/databases/campus_intelligence.db')
conn = sqlite3.connect(f'file:{db_path.resolve()}?mode=ro', uri=True)
cur = conn.cursor()

gen_queries = [
    ('GEN-01', "SELECT * FROM faculty WHERE department_id = 'DEP-MATH';"),
    ('GEN-02', "SELECT first_name, last_name, salary FROM faculty ORDER BY salary DESC LIMIT 3;"),
    ('GEN-03', "SELECT SUM(budget) AS total_budget FROM departments;"),
    ('GEN-04', "SELECT department_id, COUNT(*) AS course_count FROM courses GROUP BY department_id ORDER BY department_id;"),
    ('GEN-05', "SELECT department_id, COUNT(*) AS course_count FROM courses GROUP BY department_id HAVING COUNT(*) > 2;"),
    ('GEN-06', "SELECT c.course_title, f.first_name, f.last_name FROM courses c JOIN faculty f ON c.faculty_id = f.faculty_id;"),
    ('GEN-07', "SELECT first_name, last_name, salary FROM faculty WHERE salary > (SELECT AVG(salary) FROM faculty);"),
    ('GEN-08', "SELECT DISTINCT s.first_name, s.last_name FROM students s JOIN attendance a ON s.student_id = a.student_id WHERE a.attendance_percentage > 85.0;"),
    ('GEN-09', "SELECT s.department_id, AVG(a.attendance_percentage) AS avg_attendance FROM attendance a JOIN students s ON a.student_id = s.student_id GROUP BY s.department_id;"),
]

for qid, sql in gen_queries:
    cur.execute(sql)
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    print(f"[{qid}] PASSED -> {len(rows)} rows, cols: {cols}")

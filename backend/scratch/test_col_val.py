import sqlglot
from sqlglot import exp

schema = {
    'students': ['student_id', 'first_name', 'last_name', 'email', 'department_id', 'enrollment_year', 'gpa'],
    'departments': ['department_id', 'department_name', 'building'],
    'courses': ['course_id', 'course_name', 'department_id', 'credits'],
    'enrollments': ['enrollment_id', 'student_id', 'course_id', 'semester', 'grade_points'],
    'faculty': ['faculty_id', 'first_name', 'last_name', 'email', 'department_id', 'salary'],
    'attendance': ['attendance_id', 'student_id', 'course_id', 'attendance_percentage']
}

def check_cols(sql):
    ast = sqlglot.parse_one(sql, read='sqlite')
    aliases = {a.alias.lower() for a in ast.find_all(exp.Alias) if a.alias}
    table_map = {}
    for tbl in ast.find_all(exp.Table):
        alias_name = tbl.alias.lower() if tbl.alias else tbl.name.lower()
        table_map[alias_name] = tbl.name.lower()
    
    all_known = {c.lower() for cols in schema.values() for c in cols}
    unknown = []
    for col in ast.find_all(exp.Column):
        cname = col.name.lower()
        if cname in aliases or cname == '*':
            continue
        tbl = col.table.lower() if col.table else None
        if tbl and tbl in table_map:
            actual_tbl = table_map[tbl]
            if actual_tbl in schema and cname not in schema[actual_tbl]:
                unknown.append(f"{tbl}.{col.name}")
        elif cname not in all_known:
            unknown.append(col.name)
    return unknown

print("EVAL-13:", check_cols("SELECT * FROM students ORDER BY age;"))
print("EVAL-01:", check_cols("SELECT * FROM students WHERE department_id = 'DEP-CS';"))
print("EVAL-07:", check_cols("SELECT s.first_name, d.department_name FROM students s JOIN departments d ON s.department_id = d.department_id;"))
print("Invalid col on table:", check_cols("SELECT s.nonexistent FROM students s;"))
print("EVAL-05 having:", check_cols("SELECT department_id, AVG(gpa) AS avg_gpa FROM students GROUP BY department_id HAVING avg_gpa > 3.5;"))
print("Function check:", check_cols("SELECT strftime('%Y', 'now') FROM students;"))
print("Subquery check:", check_cols("SELECT first_name, last_name FROM students WHERE gpa > (SELECT AVG(gpa) FROM students);"))
print("EVAL-16 check:", check_cols("SELECT c.department_id, AVG(e.grade_points) AS avg_grade FROM enrollments e JOIN courses c ON e.course_id = c.course_id GROUP BY c.department_id;"))


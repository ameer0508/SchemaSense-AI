import sqlite3

conn = sqlite3.connect('backend/data/databases/campus_intelligence.db')
c = conn.cursor()
c.execute("SELECT name, sql FROM sqlite_master WHERE type='table';")
for name, sql in c.fetchall():
    print(f"Table: {name}\nSQL: {sql}\n")

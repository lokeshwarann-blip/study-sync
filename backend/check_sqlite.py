import sqlite3

conn = sqlite3.connect("study_group.db")
c = conn.cursor()

c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in c.fetchall()]
print("================ SQLITE DATABASE STATUS ================")
print("Database File: study_group.db")
print("Tables Found :", tables)

for t in ["users", "topics", "user_topics", "availability", "groups", "group_members", "messages"]:
    if t in tables:
        c.execute(f"SELECT COUNT(1) FROM {t}")
        cnt = c.fetchone()[0]
        print(f"  • Table '{t}': {cnt} records")

conn.close()

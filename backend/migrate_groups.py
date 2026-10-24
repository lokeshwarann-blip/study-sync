from app.database import engine
from sqlalchemy import text

new_cols = [
    ("description", "VARCHAR(300) DEFAULT ''"),
    ("mode", "VARCHAR(10) DEFAULT 'hybrid'"),
    ("venue", "VARCHAR(120) DEFAULT ''"),
    ("meeting_link", "VARCHAR(300) DEFAULT ''"),
    ("pace", "VARCHAR(30) DEFAULT 'Exam prep'"),
    ("study_days", "JSON DEFAULT '[]'"),
    ("start_hour", "INTEGER DEFAULT 14"),
    ("end_hour", "INTEGER DEFAULT 17"),
    ("topic_ids", "JSON DEFAULT '[]'"),
    ("created_by", "INTEGER REFERENCES users(id)"),
]

with engine.connect() as conn:
    for col_name, col_type in new_cols:
        try:
            conn.execute(text(f"ALTER TABLE groups ADD COLUMN {col_name} {col_type}"))
            print(f"Added column {col_name} to groups table")
        except Exception as e:
            print(f"Column {col_name} already exists or error: {e}")
    conn.commit()

print("Group migration finished successfully!")

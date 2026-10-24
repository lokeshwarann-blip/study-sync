from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE users ADD COLUMN bio VARCHAR DEFAULT 'CS Senior interested in Algorithms, Systems, and Machine Learning.'"))
        print("Added bio column")
    except Exception as e:
        print("bio column might already exist:", e)

    try:
        conn.execute(text("ALTER TABLE users ADD COLUMN study_style VARCHAR DEFAULT 'Collaborative problem-solving & sprint sessions'"))
        print("Added study_style column")
    except Exception as e:
        print("study_style column might already exist:", e)

    conn.commit()
print("Migration completed!")

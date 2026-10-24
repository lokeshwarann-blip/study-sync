from app.database import get_db, Base, engine
from app import models
from app.seed import seed_all

Base.metadata.create_all(bind=engine)
db = next(get_db())
try:
    user_count = db.query(models.User).count()
    if user_count == 0:
        print("Empty database detected. Seeding initial data...")
        seed_all(db)
        print("Database seeded successfully!")
    else:
        print(f"Database already contains {user_count} users. Skipping seed.")
finally:
    db.close()

from app import auth
from app.database import SessionLocal

token = auth.create_access_token({"sub": 1})
print("Generated token:", token)

db = SessionLocal()
try:
    user = auth.get_current_user(token, db)
    print("Direct auth succeeded! User:", user.name, user.email)
except Exception as e:
    print("Direct auth failed with error:", repr(e))
finally:
    db.close()

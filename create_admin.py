from app.database import SessionLocal
from app.crud.user import create_user,get_user_by_email
from app.schemas.user import UserCreate

db = SessionLocal()

admin = UserCreate(
    full_name="Admin User",
    email="admin@example.com",
    phone=None,
    fields=None,
    role="admin",
    password="adminpass",
    confirm_password="adminpass"
)
if get_user_by_email(db, "admin@example.com"):
    print("Admin already exists")
else:
    create_user(db, admin)
#create_user(db, admin)

db.close()

print("Admin created")

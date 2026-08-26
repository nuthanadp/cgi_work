# rebuild_db.py
import os
from app import app, db
from models import User

# --- Configuration ---
DB_FILE = "users.db"
USERS_TO_CREATE = [
    {
        "email": "john.smith@cgi.com",
        "password": "Password!123",
        "is_admin": True  # This user will be an admin
    },
    {
        "email": "alokbedwal@cgi.com",
        "password": "Password!123",
        "is_admin": False # This user will be a normal user
    }
]

def rebuild():
    # Must run within the app context
    with app.app_context():
        
        # 1. Delete the old database file if it exists
        if os.path.exists(DB_FILE):
            try:
                os.remove(DB_FILE)
                print(f"🗑️ Deleted old database: {DB_FILE}")
            except Exception as e:
                print(f"❌ Error deleting old database (it might be in use): {e}")
                print("Please make sure your app.py server is stopped.")
                return

        # 2. Create all new tables (based on your models.py)
        try:
            print("Creating new tables...")
            db.create_all()
            print("✅ New tables created.")
        except Exception as e:
            print(f"❌ Error creating tables: {e}")
            return

        # 3. Add the new users
        try:
            print("Adding users...")
            for user_data in USERS_TO_CREATE:
                new_user = User(
                    email=user_data["email"],
                    is_admin=user_data["is_admin"] # Set admin flag on creation
                )
                new_user.set_password(user_data["password"]) # Set hashed password
                db.session.add(new_user)
                print(f"  + Added user: {user_data['email']} (Admin: {user_data['is_admin']})")
            
            # 4. Commit all changes
            db.session.commit()
            print("✅ Successfully added all users and committed to database.")
            print("\n🎉 Your database is ready! You can now run 'python app.py'.")

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error adding users: {e}")

if __name__ == "__main__":
    rebuild()
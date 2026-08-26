# update_db.py
from app import app, db # Import your Flask app and db object
from sqlalchemy import text

def update_schema():
    with app.app_context():
        # 1. Add upload_date column
        try:
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE document ADD COLUMN upload_date DATETIME"))
                conn.commit()
            print("✅ Added 'upload_date' column.")
        except Exception as e:
            print(f"⚠️ 'upload_date' might already exist: {e}")

        # 2. Add content column
        try:
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE document ADD COLUMN content TEXT"))
                conn.commit()
            print("✅ Added 'content' column.")
        except Exception as e:
            print(f"⚠️ 'content' might already exist: {e}")

        # 3. Add user_id column
        try:
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE document ADD COLUMN user_id INTEGER REFERENCES user(id)"))
                conn.commit()
            print("✅ Added 'user_id' column.")
        except Exception as e:
            print(f"⚠️ 'user_id' might already exist: {e}")

if __name__ == "__main__":
    update_schema()
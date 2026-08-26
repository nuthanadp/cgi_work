from app import app, db
from sqlalchemy import text

with app.app_context():
    try:
        db.session.execute(text('ALTER TABLE ai_model_config ADD COLUMN api_base VARCHAR(500)'))
        db.session.commit()
        print('✅ Database updated: api_base column added to ai_model_config table')
    except Exception as e:
        print(f'Error: {e}')
        print('Note: If column already exists, you can ignore this error')

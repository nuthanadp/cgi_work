# app.py
from flask import Flask
from flask_cors import CORS
from models import db
from routes.auth import auth_bp
from routes.extract import extract_bp
from routes.analyze import analyze_bp
from routes.download import download_bp
from routes.transcript import transcript_bp
from routes.agent_executor import agent_executor_bp 
from routes.projects import projects_bp
from routes.admin import admin_bp # --- IMPORT NEW BLUEPRINT ---

app = Flask(__name__, static_folder='static')
CORS(app)

# Configure SQLite database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize DB
db.init_app(app)

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(extract_bp)
app.register_blueprint(analyze_bp)
app.register_blueprint(download_bp)
app.register_blueprint(transcript_bp) 
app.register_blueprint(agent_executor_bp)
app.register_blueprint(projects_bp)
app.register_blueprint(admin_bp, url_prefix='/api') # --- REGISTER NEW BLUEPRINT ---
# Note: I added a /api prefix to the admin routes to avoid conflicts
# You can remove 'url_prefix' if you prefer

# Create tables if they don’t exist
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
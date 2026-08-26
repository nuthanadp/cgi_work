# backend/config.py
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class Config:
    # Existing configs...
    SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///project_management.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    
    # --- NEW CONFIGS FOR PDF SERVING ---
    # The absolute path where PDFs will be saved on disk
    PDF_STATIC_FOLDER = os.path.join(BASE_DIR, 'static', 'pdfs')
    # The URL prefix for accessing static files (usually /static by default in Quart/Flask)
    STATIC_URL_PATH = '/static'

# Ensure directories exist
os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
os.makedirs(Config.PDF_STATIC_FOLDER, exist_ok=True) # Ensure the static/pdfs folder exists
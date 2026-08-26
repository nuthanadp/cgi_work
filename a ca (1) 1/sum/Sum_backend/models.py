from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import json
import datetime
from datetime import timezone

db = SQLAlchemy()

project_members = db.Table(
    'project_members',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('project_id', db.Integer, db.ForeignKey('project.id'), primary_key=True)
)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=True)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "username": self.username,
            "is_admin": self.is_admin,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)

    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    owner = db.relationship('User', backref='owned_projects')

    documents = db.relationship('Document', backref='project', lazy=True, cascade="all, delete-orphan")
    transcripts = db.relationship('Transcript', backref='project', lazy=True, cascade="all, delete-orphan")
    versions = db.relationship('DocumentVersion', backref='project', lazy=True, cascade="all, delete-orphan")

    members = db.relationship(
        'User', secondary=project_members, lazy='subquery',
        backref=db.backref('projects', lazy=True)
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "owner_id": self.owner_id,
            "documents": [doc.to_dict() for doc in self.documents],
            "transcripts": [trans.to_dict() for trans in self.transcripts],
            "members": [{"id": m.id, "email": m.email} for m in self.members],
            "owner_email": self.owner.email
        }


class DocumentVersion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    change_description = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.datetime.now(timezone.utc))

    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='versions')

    def to_dict(self):
        return {
            "id": self.id,
            "content": self.content,
            "change_description": self.change_description,
            "timestamp": self.timestamp.isoformat(),
            "user_email": self.user.email
        }


class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    file_name = db.Column(db.String(200), nullable=False)
    
    # Analysis is optional now, as we might upload just for reference logic
    analysis = db.Column(db.Text, nullable=True)  
    
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.datetime.now(timezone.utc))

    # --- NEW FIELDS FOR SMART WORKFLOW ---
    content = db.Column(db.Text, nullable=True) # Stores raw extracted text for RAG/Diffing
    upload_date = db.Column(db.DateTime, default=lambda: datetime.datetime.now(timezone.utc))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    # -------------------------------------

    pdf_preview_url = db.Column(db.String(500), nullable=True)

    def to_dict(self):
        # Handle cases where analysis might be None or empty string
        try:
            data = json.loads(self.analysis) if self.analysis else {}
        except:
            data = {}
            
        return {
            "id": self.id,
            "fileName": self.file_name,
            "analysis": data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "pdf_preview_url": self.pdf_preview_url,
            "content": self.content  # Include raw content for citation viewing
        }


class Transcript(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    file_name = db.Column(db.String(200), nullable=False)
    analysis = db.Column(db.Text, nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.datetime.now(timezone.utc))

    def to_dict(self):
        data = json.loads(self.analysis) if self.analysis else {}
        return {
            "id": self.id,
            "fileName": self.file_name,
            "analysis": data,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class TokenUsageLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=True)

    input_tokens = db.Column(db.Integer, nullable=False, default=0)
    output_tokens = db.Column(db.Integer, nullable=False, default=0)

    timestamp = db.Column(db.DateTime, default=lambda: datetime.datetime.now(timezone.utc))

    user = db.relationship('User', backref=db.backref('token_logs', lazy=True))
    project = db.relationship('Project', backref=db.backref('token_logs', lazy=True))


class AIModelConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    provider = db.Column(db.String(100), nullable=False)
    model_name = db.Column(db.String(150), nullable=False, unique=True)
    encrypted_api_key = db.Column(db.String(500), nullable=False)
    api_base = db.Column(db.String(500), nullable=True)  # For Azure endpoint or custom base URLs
    is_active = db.Column(db.Boolean, nullable=False, default=False)

    timestamp = db.Column(db.DateTime, default=lambda: datetime.datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "provider": self.provider,
            "model_name": self.model_name,
            "api_base": self.api_base,
            "is_active": self.is_active,
            "api_key_hint": "Key Set" if self.encrypted_api_key else "None"
        }
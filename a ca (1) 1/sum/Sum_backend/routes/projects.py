from flask import Blueprint, request, jsonify, g
from models import db, Project, Document, Transcript, User 
from .utils import token_required
import json

projects_bp = Blueprint("projects", __name__)

def is_project_member(project, user):
    """Checks if a user is the owner or a member of a project."""
    return project.owner_id == user.id or user in project.members

@projects_bp.route("/projects/<int:project_id>/search_users", methods=["GET"])
@token_required
def search_users(project_id):
    # --- FIX: Use db.session.get instead of Project.query.get_or_404 ---
    project = db.session.get(Project, project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
        
    if not is_project_member(project, g.user):
        return jsonify({"error": "Unauthorized"}), 403

    query = request.args.get("q", "")
    if len(query) < 2: 
        return jsonify([])

    existing_member_ids = [m.id for m in project.members]
    existing_member_ids.append(project.owner_id)

    users = User.query.filter(
        User.email.ilike(f'%{query}%'),
        User.id.notin_(existing_member_ids)
    ).limit(10).all()

    return jsonify([{"id": user.id, "email": user.email} for user in users])


@projects_bp.route("/projects", methods=["GET"])
@token_required
def get_projects():
    user_projects = Project.query.filter(
        (Project.owner_id == g.user.id) | (Project.members.any(id=g.user.id))
    ).all()
    return jsonify([p.to_dict() for p in user_projects])

@projects_bp.route("/projects", methods=["POST"])
@token_required
def create_project():
    data = request.json
    project_name = data.get("name")
    if not project_name:
        return jsonify({"error": "Project name is required"}), 400

    new_project = Project(name=project_name, owner_id=g.user.id)
    db.session.add(new_project)
    db.session.commit()
    
    return jsonify(new_project.to_dict()), 201

@projects_bp.route("/projects/<int:project_id>", methods=["DELETE"])
@token_required
def delete_project(project_id):
    # --- FIX: Use db.session.get ---
    project = db.session.get(Project, project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404

    if project.owner_id != g.user.id:
        return jsonify({"error": "Only the project owner can delete the project"}), 403

    db.session.delete(project)
    db.session.commit()
    return jsonify({"message": "Project deleted successfully"}), 200

@projects_bp.route("/projects/<int:project_id>/documents", methods=["POST"])
@token_required
def add_document_to_project(project_id):
    project = db.session.get(Project, project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404

    if not is_project_member(project, g.user):
        return jsonify({"error": "Unauthorized"}), 403

    data = request.json

    pdf_url = data.get("pdf_preview_url")   # <-- IMPORTANT

    new_doc = Document(
        file_name=data.get("fileName"),
        analysis=json.dumps(data.get("analysis")),
        pdf_preview_url=pdf_url,
        project_id=project.id
    )

    db.session.add(new_doc)
    db.session.commit()
    return jsonify(new_doc.to_dict()), 201


@projects_bp.route("/projects/<int:project_id>/transcripts", methods=["POST"])
@token_required
def add_transcript_to_project(project_id):
    # --- FIX: Use db.session.get ---
    project = db.session.get(Project, project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404

    if not is_project_member(project, g.user):
        return jsonify({"error": "Unauthorized"}), 403

    data = request.json
    new_transcript = Transcript(
        file_name=data.get("fileName"),
        analysis=json.dumps(data.get("analysis")),
        project_id=project.id
    )
    db.session.add(new_transcript)
    db.session.commit()
    return jsonify(new_transcript.to_dict()), 201

@projects_bp.route("/projects/<int:project_id>/documents/<int:doc_id>", methods=["DELETE"])
@token_required
def delete_document_from_project(project_id, doc_id):
    # --- FIX: Use db.session.get ---
    project = db.session.get(Project, project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404

    if not is_project_member(project, g.user):
        return jsonify({"error": "Unauthorized"}), 403

    # --- FIX: Use db.session.get ---
    doc_to_delete = db.session.get(Document, doc_id)
    if not doc_to_delete:
        return jsonify({"error": "Document not found"}), 404

    if doc_to_delete.project_id != project.id:
        return jsonify({"error": "Document not found in this project"}), 404

    db.session.delete(doc_to_delete)
    db.session.commit()
    return jsonify({"message": "Document deleted successfully"}), 200

@projects_bp.route("/projects/<int:project_id>/transcripts/<int:transcript_id>", methods=["DELETE"])
@token_required
def delete_transcript_from_project(project_id, transcript_id):
    # --- FIX: Use db.session.get ---
    project = db.session.get(Project, project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404

    if not is_project_member(project, g.user):
        return jsonify({"error": "Unauthorized"}), 403

    # --- FIX: Use db.session.get ---
    transcript_to_delete = db.session.get(Transcript, transcript_id)
    if not transcript_to_delete:
        return jsonify({"error": "Transcript not found"}), 404

    if transcript_to_delete.project_id != project.id:
        return jsonify({"error": "Transcript not found in this project"}), 404

    db.session.delete(transcript_to_delete)
    db.session.commit()
    return jsonify({"message": "Transcript deleted successfully"}), 200

@projects_bp.route("/projects/<int:project_id>/members", methods=["POST"])
@token_required
def add_project_member(project_id):
    # --- FIX: Use db.session.get ---
    project = db.session.get(Project, project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404

    if project.owner_id != g.user.id:
        return jsonify({"error": "Only the project owner can add members"}), 403
    
    data = request.json
    email = data.get("email")
    if not email:
        return jsonify({"error": "Email is required"}), 400

    user_to_add = User.query.filter_by(email=email).first()
    if not user_to_add:
        return jsonify({"error": f"User with email '{email}' not found"}), 404
        
    if is_project_member(project, user_to_add):
        return jsonify({"error": "User is already a member of this project"}), 409
        
    project.members.append(user_to_add)
    db.session.commit()
    
    return jsonify({"message": f"User {email} added to project."}), 200

@projects_bp.route("/projects/<int:project_id>/members/<int:user_id>", methods=["DELETE"])
@token_required
def remove_project_member(project_id, user_id):
    # --- FIX: Use db.session.get ---
    project = db.session.get(Project, project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404

    if project.owner_id != g.user.id:
        return jsonify({"error": "Only the project owner can remove members"}), 403
        
    if project.owner_id == user_id:
        return jsonify({"error": "Project owner cannot be removed"}), 400

    # --- FIX: Use db.session.get ---
    user_to_remove = db.session.get(User, user_id)
    if not user_to_remove or user_to_remove not in project.members:
        return jsonify({"error": "User is not a member of this project"}), 404
        
    project.members.remove(user_to_remove)
    db.session.commit()
    
    return jsonify({"message": f"User {user_to_remove.email} removed from project."}), 200


@projects_bp.route("/projects/<int:project_id>/documents/<int:doc_id>/content", methods=["GET"])
@token_required
def get_document_content(project_id, doc_id):
    """Get the raw content of a document for citation viewing."""
    project = db.session.get(Project, project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404

    if not is_project_member(project, g.user):
        return jsonify({"error": "Unauthorized"}), 403

    document = db.session.get(Document, doc_id)
    if not document or document.project_id != project_id:
        return jsonify({"error": "Document not found"}), 404

    return jsonify({
        "id": document.id,
        "fileName": document.file_name,
        "content": document.content or ""
    }), 200
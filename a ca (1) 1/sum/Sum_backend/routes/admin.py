# routes/admin.py

from flask import Blueprint, request, jsonify, g
from models import db, AIModelConfig
from .utils import admin_required
from services.security import encrypt_key, decrypt_key # Import our helpers

admin_bp = Blueprint("admin", __name__)

# GET all configured models
@admin_bp.route("/admin/models", methods=["GET"])
@admin_required
def get_models():
    try:
        models = AIModelConfig.query.order_by(AIModelConfig.provider, AIModelConfig.model_name).all()
        # to_dict() safely returns only the key hint
        return jsonify([m.to_dict() for m in models]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ADD a new model
@admin_bp.route("/admin/models", methods=["POST"])
@admin_required
def add_model():
    data = request.json
    provider = data.get("provider")
    model_name = data.get("model_name")
    api_key = data.get("api_key")
    api_base = data.get("api_base")  # Optional: Azure endpoint or custom base URL

    if not all([provider, model_name, api_key]):
        return jsonify({"error": "Provider, Model Name, and API Key are required"}), 400

    try:
        # Check if model name already exists
        existing = AIModelConfig.query.filter_by(model_name=model_name).first()
        if existing:
            return jsonify({"error": f"Model name '{model_name}' already exists."}), 409

        # Encrypt the key before saving
        encrypted_key = encrypt_key(api_key)
        
        new_model = AIModelConfig(
            provider=provider,
            model_name=model_name,
            encrypted_api_key=encrypted_key,
            api_base=api_base,  # Store Azure endpoint if provided
            is_active=False # Default to inactive
        )
        db.session.add(new_model)
        db.session.commit()
        return jsonify(new_model.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to add model: {str(e)}"}), 500

# UPDATE a model (e.g., set active, change key)
@admin_bp.route("/admin/models/<int:model_id>", methods=["PUT"])
@admin_required
def update_model(model_id):
    model = AIModelConfig.query.get_or_404(model_id)
    data = request.json
    
    try:
        if "api_key" in data and data["api_key"]:
            # User is providing a new key
            model.encrypted_api_key = encrypt_key(data["api_key"])
            
        if "is_active" in data:
            is_active = data["is_active"]
            # This logic makes sure only ONE model is active at a time
            if is_active:
                AIModelConfig.query.filter(AIModelConfig.id != model_id).update({AIModelConfig.is_active: False})
                model.is_active = True
            else:
                # Prevent deactivating the last active model
                active_count = AIModelConfig.query.filter_by(is_active=True).count()
                if active_count <= 1 and model.is_active:
                    return jsonify({"error": "Cannot deactivate the last active model."}), 400
                model.is_active = False

        if "provider" in data: model.provider = data["provider"]
        if "model_name" in data: model.model_name = data["model_name"]
        if "api_base" in data: model.api_base = data["api_base"]  # Update Azure endpoint
            
        db.session.commit()
        return jsonify(model.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to update model: {str(e)}"}), 500

# DELETE a model
@admin_bp.route("/admin/models/<int:model_id>", methods=["DELETE"])
@admin_required
def delete_model(model_id):
    model = AIModelConfig.query.get_or_404(model_id)
    try:
        if model.is_active:
            return jsonify({"error": "Cannot delete an active model. Please activate another model first."}), 400
            
        db.session.delete(model)
        db.session.commit()
        return jsonify({"message": "Model deleted"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to delete model: {str(e)}"}), 500
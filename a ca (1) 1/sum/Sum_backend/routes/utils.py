# routes/utils.py

from functools import wraps
from flask import request, jsonify, g # Import 'g'
import jwt
import os
from models import User # Import User model

SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if "Authorization" in request.headers:
            auth_header = request.headers["Authorization"]
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]

        if not token:
            return jsonify({"error": "Token is missing!"}), 401

        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            # THIS IS THE KEY CHANGE
            # Find the user based on the email in the token
            current_user = User.query.filter_by(email=data["email"]).first()
            if not current_user:
                return jsonify({"error": "User not found!"}), 401
            # Attach the user object to Flask's global 'g' object
            g.user = current_user
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired!"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token!"}), 401

        return f(*args, **kwargs)

    return decorated

# --- NEW: Admin Decorator ---
def admin_required(f):
    @wraps(f)
    @token_required # Ensures they are logged in first
    def decorated(*args, **kwargs):
        if not g.user or not g.user.is_admin:
            return jsonify({"error": "Administrator access required"}), 403
        return f(*args, **kwargs)
    return decorated


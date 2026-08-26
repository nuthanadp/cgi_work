from flask import Blueprint, request, jsonify, g 
from models import db, User, Project, TokenUsageLog
from sqlalchemy import func, extract, desc
import jwt
import datetime
import os
from .utils import token_required 

auth_bp = Blueprint("auth", __name__)
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "User already exists"}), 400

    # New users should default to not admin
    new_user = User(email=email, is_admin=False) # Ensure default is set
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User registered successfully"}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    user = User.query.filter_by(email=email).first()
    if user and user.check_password(password):
        # --- FIX 1: Use timezone-aware UTC for JWT ---
        expiration = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=12)
        
        token = jwt.encode(
            {"email": email, "exp": expiration},
            SECRET_KEY,
            algorithm="HS256"
        )
        return jsonify({"message": "Login successful", "token": token})

    return jsonify({"error": "Invalid email or password"}), 401

# --- ENDPOINT: GET USER PROFILE ---
@auth_bp.route("/profile", methods=["GET"])
@token_required
def get_profile():
    """Returns the current logged-in user's details."""
    if not g.user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(g.user.to_dict()), 200

# --- ENDPOINT: UPDATE USER PROFILE (FIXED USERNAME CHECK) ---
@auth_bp.route("/profile", methods=["PUT"])
@token_required
def update_profile():
    """Updates the current logged-in user's username and/or password."""
    user = g.user
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.json
    updated = False

    # Update username if provided and different
    new_username = data.get("username")
    if new_username is not None and new_username != user.username:
        # Check if the new username is already taken by someone else
        if new_username:
             existing_user = User.query.filter(
                 func.lower(User.username) == func.lower(new_username), 
                 User.id != user.id
             ).first()
             if existing_user:
                 return jsonify({"error": "Username already taken"}), 409
        
        user.username = new_username if new_username else None
        updated = True

    # Update password if current and new passwords are provided
    current_password = data.get("current_password")
    new_password = data.get("new_password")

    if new_password:
        if not current_password:
            return jsonify({"error": "Current password is required to set a new password"}), 400
        if not user.check_password(current_password):
            return jsonify({"error": "Incorrect current password"}), 401
        if len(new_password) < 6:
             return jsonify({"error": "New password must be at least 6 characters long"}), 400

        user.set_password(new_password)
        updated = True

    if updated:
        try:
            db.session.commit()
            return jsonify({"message": "Profile updated successfully", "user": user.to_dict()}), 200
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error updating profile for user {user.id}: {e}")
            return jsonify({"error": "Failed to update profile due to a database error."}), 500
    else:
        return jsonify({"message": "No changes detected"}), 200

# --- ENDPOINT: DELETE ACCOUNT ---
@auth_bp.route("/profile", methods=["DELETE"])
@token_required
def delete_account():
    """Deletes the current logged-in user and all their associated data."""
    user = g.user
    if not user:
        return jsonify({"error": "User not found"}), 404

    try:
        # 1. Remove user from any projects they are members of
        for project in list(user.projects):
            project.members.remove(user)
        
        # 2. Delete all projects owned by the user
        Project.query.filter_by(owner_id=user.id).delete()
        
        # 3. Delete all token logs for the user
        TokenUsageLog.query.filter_by(user_id=user.id).delete()

        # 4. Delete the user object itself
        db.session.delete(user)
        
        # 5. Commit all changes
        db.session.commit()
        
        return jsonify({"message": "Account deleted successfully"}), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error deleting account for user {user.id}: {e}")
        return jsonify({"error": "Failed to delete account due to a database error."}), 500

# --- ENDPOINT: GET USAGE STATISTICS ---
@auth_bp.route("/profile/usage", methods=["GET"])
@token_required
def get_usage_stats():
    """Returns the current user's total token usage and time-based stats."""
    user_id = g.user.id
    
    # --- FIX 2: Use timezone-aware UTC, then strip tzinfo for DB compatibility ---
    # This prevents the DeprecationWarning while keeping logic compatible with Naive DB timestamps
    now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    
    try:
        # --- 1. CORE STATS ---
        
        # ALL-TIME TOTAL
        total_tokens_query = db.session.query(
            func.sum(TokenUsageLog.input_tokens + TokenUsageLog.output_tokens)
        ).filter(TokenUsageLog.user_id == user_id).scalar() or 0
        
        # TOKENS USED TODAY
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        daily_tokens_query = db.session.query(
            func.sum(TokenUsageLog.input_tokens + TokenUsageLog.output_tokens)
        ).filter(
            TokenUsageLog.user_id == user_id,
            TokenUsageLog.timestamp >= start_of_day
        ).scalar() or 0

        # TOKENS USED THIS MONTH
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_tokens_query = db.session.query(
            func.sum(TokenUsageLog.input_tokens + TokenUsageLog.output_tokens)
        ).filter(
            TokenUsageLog.user_id == user_id,
            TokenUsageLog.timestamp >= start_of_month
        ).scalar() or 0
        
        # TOKENS USED LAST MONTH
        if now.month == 1:
            start_of_last_month = now.replace(year=now.year - 1, month=12, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            start_of_last_month = now.replace(month=now.month - 1, day=1, hour=0, minute=0, second=0, microsecond=0)
            
        end_of_last_month = start_of_month 

        last_month_tokens_query = db.session.query(
            func.sum(TokenUsageLog.input_tokens + TokenUsageLog.output_tokens)
        ).filter(
            TokenUsageLog.user_id == user_id,
            TokenUsageLog.timestamp >= start_of_last_month,
            TokenUsageLog.timestamp < end_of_last_month
        ).scalar() or 0
        
        # --- 2. DAILY TREND DATA (Last 30 days) ---
        thirty_days_ago = now - datetime.timedelta(days=30)
        
        daily_trend_results = db.session.query(
            func.date(TokenUsageLog.timestamp).label('date'),
            func.sum(TokenUsageLog.input_tokens + TokenUsageLog.output_tokens).label('tokens')
        ).filter(
            TokenUsageLog.user_id == user_id,
            TokenUsageLog.timestamp >= thirty_days_ago
        ).group_by(func.date(TokenUsageLog.timestamp)).order_by('date').all()
        
        # Format and fill missing days
        daily_trend_map = {r.date: r.tokens for r in daily_trend_results}
        daily_trend_data = []
        for i in range(30):
            date_i = now - datetime.timedelta(days=29 - i)
            date_str = date_i.strftime('%Y-%m-%d')
            daily_trend_data.append({
                "date": date_str,
                "tokens": daily_trend_map.get(date_str, 0)
            })

        # --- 3. HOURLY TREND DATA (Today) ---
        
        hourly_trend_results = db.session.query(
            extract('hour', TokenUsageLog.timestamp).label('hour'),
            func.sum(TokenUsageLog.input_tokens + TokenUsageLog.output_tokens).label('tokens')
        ).filter(
            TokenUsageLog.user_id == user_id,
            TokenUsageLog.timestamp >= start_of_day # Filter for today only
        ).group_by('hour').order_by('hour').all()
        
        hourly_trend_data = [{"hour": int(r.hour), "tokens": int(r.tokens)} for r in hourly_trend_results]

        return jsonify({
            "total_tokens": int(total_tokens_query),
            "daily_tokens": int(daily_tokens_query),
            "monthly_tokens": int(monthly_tokens_query),
            "last_month_tokens": int(last_month_tokens_query),
            "daily_trend_data": daily_trend_data,
            "hourly_trend_data": hourly_trend_data
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error fetching usage stats for user {user_id}: {e}")
        return jsonify({"error": "Failed to fetch usage statistics."}), 500
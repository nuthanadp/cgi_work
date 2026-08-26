from flask import Blueprint, request, jsonify, g
from services.ai_agent import run_agent
import json
import re
from routes.utils import token_required
import ast
from google.api_core.exceptions import ResourceExhausted, InvalidArgument
from models import db, TokenUsageLog # Import db and TokenUsageLog

transcript_bp = Blueprint("transcript", __name__)

def clean_ai_json(ai_output: str):
    """
    Attempts to extract valid JSON from AI output, even if there is extra text or minor formatting issues.
    """
    try:
        return json.loads(ai_output)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", ai_output, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                try:
                    return ast.literal_eval(match.group(0))
                except:
                    return {}
        return {}

@transcript_bp.route("/analyze_transcript", methods=["POST"])
@token_required
def analyze_transcript():
    data = request.json
    transcript = data.get("transcript")
    if not transcript:
        return jsonify({"error": "No transcript provided"}), 400

    # Convert transcript to string for AI prompts
    if isinstance(transcript, list):
        transcript_text = "\n".join([f"{t.get('speaker','Unknown')}: {t.get('text','')}" for t in transcript])
    else:
        transcript_text = transcript

    try:
        # Step 1: Summarize
        summary_prompt = f"""
        Summarize this project discussion transcript in a few sentences, highlighting the main purpose and discussed topics:

        Transcript:
        {transcript_text}
        """
        summary_response = run_agent(summary_prompt)
        summary = summary_response["content"]
        usage1 = summary_response["usage"]

        # Step 2: Extract requirements with speaker attribution
        requirements_prompt = f"""
        Extract all requirements from the following transcript and categorize them strictly as:
        - Functional
        - NonFunctional
        - Constraints

        Include the speaker for each requirement.

        Return ONLY JSON in this exact format:
        {{
            "Functional": [
                {{"requirement": "...", "speaker": "..."}}
            ],
            "NonFunctional": [
                {{"requirement": "...", "speaker": "..."}}
            ],
            "Constraints": [
                {{"requirement": "...", "speaker": "..."}}
            ]
        }}

        Transcript:
        {transcript_text}
        """

        extracted_response = run_agent(requirements_prompt)
        extracted_json = extracted_response["content"]
        usage2 = extracted_response["usage"]
        
        requirements = clean_ai_json(extracted_json)

        # --- UPDATED: Removed faulty 'if' check ---
        try:
            total_input = (usage1.get("input_tokens", 0) if usage1 else 0) + (usage2.get("input_tokens", 0) if usage2 else 0)
            total_output = (usage1.get("output_tokens", 0) if usage1 else 0) + (usage2.get("output_tokens", 0) if usage2 else 0)

            new_log = TokenUsageLog(
                user_id=g.user.id,
                project_id=None, # Not associated with a project yet
                input_tokens=total_input,
                output_tokens=total_output
            )
            db.session.add(new_log)
            db.session.commit() # Commit the log
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error logging tokens for analyze_transcript: {e}")
        # --- END OF UPDATE ---

        # Ensure all keys exist
        for key in ["Functional", "NonFunctional", "Constraints"]:
            if key not in requirements:
                requirements[key] = []

        # Convert each requirement object to a readable string
        for key in ["Functional", "NonFunctional", "Constraints"]:
            readable_list = []
            for item in requirements[key]:
                req_text = item.get("requirement") if isinstance(item, dict) else str(item)
                speaker = item.get("speaker") if isinstance(item, dict) else "Unknown"
                readable_list.append(f"{req_text} ({speaker})")
            requirements[key] = readable_list

        return jsonify({
            "summary": summary,
            "requirements": requirements
        })

    except ResourceExhausted:
        db.session.rollback() # Add rollback
        return jsonify({
            "error": "Gemini API quota exceeded. Please wait for quota reset or upgrade your plan."
        }), 429

    except InvalidArgument:
        db.session.rollback() # Add rollback
        return jsonify({
            "error": "Invalid API key for Gemini API. Please check your credentials."
        }), 401

    except Exception as e:
        db.session.rollback() # Add rollback
        # Generic fallback for other errors
        return jsonify({
            "error": f"An error occurred while analyzing transcript: {str(e)}"
        }), 500
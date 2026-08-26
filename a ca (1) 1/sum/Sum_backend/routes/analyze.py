from flask import Blueprint, request, jsonify, g
from services.ai_agent import run_agent
import json
import re
import datetime
import traceback
from routes.utils import token_required
from models import db, TokenUsageLog, Document

analyze_bp = Blueprint("analyze", __name__)

def extract_json(text):
    """Extract the first valid JSON object from text."""
    if not text: return {}
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            return {}
    return {}

@analyze_bp.route("/analyze_document", methods=["POST"])
@token_required 
def analyze_document():
    print("🚀 Starting /analyze_document...")
    try:
        data = request.json
        text = data.get("text")
        project_id = data.get("project_id")
        filename = data.get("filename", "Analyzed_Document.txt")

        if not text:
            print("❌ No text provided in request.")
            return jsonify({"error": "No text provided"}), 400

        # --- 1. SAVE TO DB ---
        doc_id = None
        if project_id:
            try:
                print(f"💾 Saving document '{filename}' to Project {project_id}...")
                new_doc = Document(
                    file_name=filename,
                    content=text,
                    project_id=project_id,
                    # Ensure we handle the case where g.user might not have an ID (rare but possible)
                    user_id=g.user.id if hasattr(g.user, 'id') else None, 
                    upload_date=datetime.datetime.utcnow(),
                    analysis=json.dumps({"status": "processing"})
                )
                db.session.add(new_doc)
                db.session.commit()
                doc_id = new_doc.id
                print(f"✅ Document saved with ID: {doc_id}")
            except Exception as e:
                db.session.rollback()
                print(f"⚠️ DB Save Failed (continuing analysis anyway): {str(e)}")
                # traceback.print_exc() 

        # --- 2. AI ANALYSIS (ENHANCED FOR JIRA STORIES) ---
        # Detect if this is a JIRA story based on content
        # The content may already be enhanced/cleaned from extract.py
        is_jira_story = any(indicator in text[:2000] for indicator in [
            "Story Metadata", "Sub-Tasks", "Acceptance Criteria", "JIRA-", "Story Points",
            "Type:", "Epic Link", "Sprint"
        ])
        
        if is_jira_story:
            print("🎫 Detected JIRA story (enhanced content) - using specialized analysis...")
            summary_prompt = f"""
Analyze this JIRA story and extract a concise summary focusing on:
1. What change is being requested (business requirement)
2. Which system/component is affected
3. Key technical changes (data types, message formats, validation rules, API changes)
4. Impact scope (what sections of the BSOL/SR document might need updates)
5. Any dependencies or constraints mentioned

**CRITICAL:** If the description contains QUESTIONS (e.g., "What should we do?", "needs clarity", "Development team needs clarity on..."), this is a SPIKE/Investigation - state that clearly.

The input has already been cleaned and enhanced to focus on relevant requirements.
Keep your summary to 5-7 bullet points maximum.

Enhanced JIRA Story:
{text[:12000]}
"""
            categorize_prompt = f"""
You are analyzing an enhanced JIRA story for HIGH-LEVEL technical requirements ONLY.
The input has been preprocessed to remove irrelevant metadata and focus on core requirements.

**CRITICAL EXTRACTION RULES:**
1. **IGNORE Implementation Details:**
   - XML paths (e.g., /AppHdr/CreDt, /Document/FIToFICstmrCdtTrf/...)
   - XSD file locations and SharePoint URLs
   - Specific field paths in message structures
   - Test scenarios, test data, comments, sub-tasks
   - Merge request links and environment configurations
   - Code examples and detailed technical paths
   - System metadata and formatting artifacts

2. **EXTRACT ONLY High-Level Requirements:**
   - WHAT needs to change (e.g., "Support UTC+14 timezone offset")
   - WHY it's needed (business reason)
   - WHICH data type or validation rule changes (summary level only)
   - IMPACT (e.g., "affects Pacs.008 messages")
   - Business value and objectives

**SPIKE/INVESTIGATION DETECTION:**
IF the description contains QUESTIONS or uncertainties like:
- "What should be the behavior if..."
- "Development team needs clarity on..."
- "needs to decide", "pending discussion"
- Multiple questions with no answers

THEN return ONLY:
{{
  "Functional": [],
  "NonFunctional": [],
  "Constraints": []
}}
(DO NOT include a Note field - frontend cannot handle it)

**FOR CONCRETE REQUIREMENTS:**

**FUNCTIONAL Requirements (Business/User-facing changes):**
- What the system must DO (e.g., "Enable timezone offset up to UTC+14")
- New message formats to support (e.g., "Support hybrid address format in Pacs.002")
- Business rules to implement
- User-facing features or capabilities

**NON-FUNCTIONAL Requirements (Technical specifications):**
- Data type changes (e.g., "Update CBPR_DateTime regex pattern to allow +14 offset")
- Validation rule modifications
- Performance requirements
- Compliance or regulatory requirements
- Integration requirements

**CONSTRAINTS:**
- Limitations or restrictions
- Backward compatibility requirements
- Standards compliance (e.g., "Must comply with SWIFT SR2025 specification")
- Dependencies on other systems or changes

**OUTPUT FORMAT (STRICT):**
Return VALID JSON ONLY with these 3 keys (arrays must always be present, even if empty):
{{
  "Functional": ["high-level requirement 1", "high-level requirement 2"],
  "NonFunctional": ["technical spec 1", "technical spec 2"],
  "Constraints": ["constraint 1"]
}}

**EXAMPLE - CORRECT OUTPUT:**
For a story about UTC+14 timezone support:
{{
  "Functional": ["Enable timezone offset support up to UTC+14 for Pacs.008 messages"],
  "NonFunctional": ["Update CBPR_DateTime data type regex pattern from max +13 to max +14 offset"],
  "Constraints": ["Change must be applied to both inward and outward Pacs.008 processing"]
}}

**EXAMPLE - WRONG OUTPUT (DO NOT DO THIS):**
{{
  "Functional": ["/AppHdr/CreDt must support +14", "/Document/FIToFICstmrCdtTrf/GrpHdr/CreDtTm must support +14"],
  "Constraints": ["XSD location: https://sharepoint.com/..."]
}}
WHY WRONG: Lists XML paths instead of high-level requirement. Should say "Enable UTC+14 support for Pacs.008 DateTime fields".

Enhanced JIRA Story Content:
{text[:15000]}
"""
        else:
            print("📄 Analyzing as standard document...")
            summary_prompt = f"Summarize this requirements document in 5 bullet points:\n{text[:4000]}"
            categorize_prompt = f"""
Return VALID JSON only. Categorize these requirements:
- Functional
- NonFunctional
- Constraints

Format: {{ "Functional": [], "NonFunctional": [], "Constraints": [] }}

Text: {text[:4000]}
"""
        
        # Guard against AI failure
        try:
            summary_response = run_agent(summary_prompt)
            if not summary_response or "content" not in summary_response:
                raise ValueError("AI Agent returned empty response for Summary.")
            
            extracted_content = summary_response.get("content", "No summary generated.")
            usage1 = summary_response.get("usage", {})
            print("✅ Summary generated.")
        except Exception as ai_e:
            print(f"❌ AI Summary Failed: {ai_e}")
            extracted_content = "Summary extraction failed."
            usage1 = {}

        print("🤖 Categorizing requirements...")
        try:
            categorize_response = run_agent(categorize_prompt)
            if not categorize_response or "content" not in categorize_response:
                raise ValueError("AI Agent returned empty response for Categorization.")
                
            categorized_content = categorize_response.get("content", "{}")
            usage2 = categorize_response.get("usage", {})
            
            categorized_json = extract_json(categorized_content)
            print("✅ Categorization generated.")
        except Exception as ai_e:
            print(f"❌ AI Categorization Failed: {ai_e}")
            categorized_json = {"Functional": [], "NonFunctional": [], "Constraints": []}
            usage2 = {}

        # --- 3. UPDATE DB WITH RESULTS ---
        if doc_id:
            try:
                final_analysis = {
                    "summary": extracted_content,
                    "extracted_content": text,
                    "categorized_json": categorized_json
                }
                doc = db.session.get(Document, doc_id) # Safer than query.get
                if doc:
                    doc.analysis = json.dumps(final_analysis)
                    db.session.commit()
                    print("✅ Document Analysis updated in DB.")
            except Exception as e:
                db.session.rollback()
                print(f"⚠️ Failed to update document analysis record: {e}")

        # --- 4. LOG TOKENS ---
        try:
            total_input = (usage1.get("input_tokens", 0) or 0) + (usage2.get("input_tokens", 0) or 0)
            total_output = (usage1.get("output_tokens", 0) or 0) + (usage2.get("output_tokens", 0) or 0)
            
            if hasattr(g, 'user') and g.user:
                new_log = TokenUsageLog(
                    user_id=g.user.id,
                    project_id=project_id if project_id else None,
                    input_tokens=total_input,
                    output_tokens=total_output
                )
                db.session.add(new_log)
                db.session.commit()
                print("✅ Tokens logged.")
        except Exception as e:
            db.session.rollback()
            print(f"⚠️ Token logging failed: {e}")

        return jsonify({
            "extracted_content": extracted_content,
            "categorized_json": categorized_json
        })

    except Exception as e:
        print("❌ CRITICAL ERROR IN /analyze_document:")
        traceback.print_exc() # This prints the EXACT line number and error to your terminal
        return jsonify({"error": str(e)}), 500
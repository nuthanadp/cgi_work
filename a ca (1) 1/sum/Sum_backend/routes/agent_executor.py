# routes/agent_executor.py
import ast
from services.elysia_service import ElysiaWrapper
from flask import Blueprint, request, jsonify, Response, g
from services.ai_agent import run_agent_and_get_content, run_streaming_agent, run_agent
from routes.utils import token_required
from models import db, Project, DocumentVersion, User, TokenUsageLog, Document, Transcript
import json
import re 
import datetime
agent_executor_bp = Blueprint("agent_executor", __name__)

# --- (HELPER FUNCTIONS: extract_json, is_project_member, clean_preamble) ---

def extract_json(text: str) -> list | dict | None:
    """
    Robust JSON extractor.
    """
    if not text: 
        return None
    
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    try:
        match = re.search(r"```(?:json)?\s*([\sS]*?)\s*```", text, re.DOTALL)
        if match:
            return json.loads(match.group(1).strip())
    except json.JSONDecodeError:
        pass

    try:
        text = text.strip()
        start_brace = text.find('{')
        start_bracket = text.find('[')
        
        if start_brace != -1 and (start_bracket == -1 or start_brace < start_bracket):
            start = start_brace
            end = text.rfind('}') 
        elif start_bracket != -1 and (start_brace == -1 or start_bracket < start_brace):
            start = start_bracket
            end = text.rfind(']') 
        else:
            return None 

        if end == -1 or end < start:
             return None

        candidate = text[start : end+1]
        
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            try:
                return ast.literal_eval(candidate)
            except:
                pass
                
        return None
        
    except Exception as e:
        print(f"❌ extract_json failed: {e}. Text was: {text[:200]}")
        return None

def is_project_member(project, user):
    return project.owner_id == user.id or user in project.members

def clean_preamble(text: str) -> str:
    start_index = text.find("#")
    if start_index == -1: start_index = text.find(">")
    if start_index == -1: start_index = text.find("<p class=")
    return text[start_index:] if start_index != -1 else text

def strip_all_citations(text: str) -> str:
    """
    AGGRESSIVELY removes ALL existing citations from document.
    This runs BEFORE AI processing to ensure clean slate.
    """
    if not text:
        return text
    
    # Remove markdown bold citations: **[Edit: ...] **[Source: ...]**
    text = re.sub(r'\*\*\[Edit:[^\]]+\]\*\*', '', text)
    text = re.sub(r'\*\*\[Source:[^\]]+\]\*\*', '', text)
    
    # Remove emoji-based citations: ✍️ User Request, ✍️ description | filename.doc
    text = re.sub(r'✍️[^\n]+', '', text)
    
    # Remove any standalone citation markers
    text = re.sub(r'\[Edit:[^\]]+\]', '', text)
    text = re.sub(r'\[Source:[^\]]+\]', '', text)
    
    # Remove old "Last edit" lines (both formats)
    text = re.sub(r'_Last edit:[^_]+_', '', text)
    text = re.sub(r'Last edit:[^\n]+', '', text)
    
    # Remove leftover HTML comment markers
    text = re.sub(r'<!--\s*LATEST_CHANGE\s*-->', '', text)
    
    # Clean up multiple spaces and newlines created by removal
    text = re.sub(r'  +', ' ', text)  # Multiple spaces to single space
    text = re.sub(r'\n{3,}', '\n\n', text)  # Multiple newlines to max 2
    
    return text.strip()

# --- (ENDPOINT: EXECUTE INITIAL GOAL) ---
@agent_executor_bp.route("/projects/<int:project_id>/execute_goal", methods=["POST"])
@token_required
def execute_goal(project_id):
    project = Project.query.get_or_404(project_id)
    if not is_project_member(project, g.user): return jsonify({"error": "Unauthorized"}), 403
    data = request.json
    goal = data.get("goal")
    project_files_data = data.get("project_files_data")
    if not goal or not project_files_data: return jsonify({"error": "A goal and project files are required"}), 400
    master_prompt = f"""
    You are an expert-level Project Analyst and Technical Writer specializing in BSOL (Business Solution) and SR (System Requirements) documents.
    Your primary task is to achieve the user's goal by analyzing the provided project data.
    
    **DOCUMENT HANDLING RULES:**
    1. **Tables:** If source files contain tables (they will be in Markdown format), preserve table structure in your output.
    2. **Images:** If you see image references like `![](path)`, preserve them in your document.
    3. **Technical Details:** Extract ALL technical specifications, validation rules, message formats, and constraints from tables.
    
    **CRITICAL CITATION RULES:**
    1. For every requirement, feature, or constraint you list, you MUST provide inline citations indicating its source file(s).
    2. Citation format: `[Source: file_name.ext]` immediately after the content.
    3. If a single point comes from MULTIPLE source files, list each source in its *OWN SEPARATE* citation tag.
       Example: `Requirement text [Source: file1.txt][Source: file2.json]`
    4. DO NOT combine multiple filenames within a single `[Source: ...]` tag.
    5. When extracting from tables, cite the source file after each row or logical group.
    
    **OUTPUT FORMAT:**
    - Use GitHub Flavored Markdown
    - Preserve all tables using Markdown table syntax
    - Keep all images using `![alt](path)` format
    - Add citations after each requirement/constraint
    
    USER'S GOAL: "{goal}"
    
    Here is the project data to analyze: {json.dumps(project_files_data, indent=2)}
    """
    try:
        ai_response = run_agent_and_get_content(master_prompt)
        document_content = ai_response["content"]
        usage = ai_response["usage"]
        
        cleaned_content = clean_preamble(document_content)
        
        initial_version = DocumentVersion(
            content=cleaned_content, 
            change_description="Initial document generation", 
            project_id=project_id, 
            user_id=g.user.id
        )
        db.session.add(initial_version)

        if usage:
            new_log = TokenUsageLog(
                user_id=g.user.id,
                project_id=project_id,
                input_tokens=usage.get("input_tokens", 0),
                output_tokens=usage.get("output_tokens", 0)
            )
            db.session.add(new_log)

        db.session.commit()
        return jsonify({"content": cleaned_content})
    except Exception as e:
        db.session.rollback() 
        print(f"ERROR DURING AGENT EXECUTION: {e}")
        return jsonify({"error": str(e)}), 500

@agent_executor_bp.route("/projects/<int:project_id>/detect_changes", methods=["POST"])
@token_required
def detect_project_updates(project_id):
    project = Project.query.get_or_404(project_id)
    if not is_project_member(project, g.user):
        return jsonify({"error": "Unauthorized"}), 403

    data = request.json
    current_document = data.get("current_document")
    if not current_document:
        return jsonify({"error": "Current document content is required"}), 400

    latest_version = DocumentVersion.query.filter_by(project_id=project_id).order_by(DocumentVersion.timestamp.desc()).first()
    last_doc_update = latest_version.timestamp if latest_version else datetime.datetime.min.replace(tzinfo=None)

    recent_docs = Document.query.filter(
        Document.project_id == project_id,
        Document.upload_date > last_doc_update
    ).order_by(Document.upload_date.desc()).limit(5).all()

    new_file_names = [d.file_name for d in recent_docs] 

    if not recent_docs:
        return jsonify({
            "suggestion": "✅ No new source files found since the last update. Your document is up to date.",
            "new_files": []
        })

    new_files_context = ""
    for doc in recent_docs:
        raw_text = doc.content
        if not raw_text and doc.analysis:
            try:
                raw_text = json.loads(doc.analysis).get('extracted_content', '')
            except:
                raw_text = ""
        
        content_snippet = raw_text[:50000] if raw_text else "No text content."
        new_files_context += f"\n=== SOURCE FILE: {doc.file_name} ===\n{content_snippet}\n=== END SOURCE ===\n"

    prompt = f"""
You are a BSOL/SR Document Update Strategist. You understand SR (System Requirements) and BSOL (Business Solution) document structure.

**YOUR TASK:**
Analyze JIRA stories against the live SR document and suggest PRECISE, HIGH-LEVEL update instructions.

**CRITICAL RULES:**
1. **READ THE LIVE DOCUMENT FIRST** - Understand its current structure and section numbering
2. **FIND EXISTING SECTIONS** - If instruction mentions "Section 2.1", look for the EXISTING Section 2.1 in the document
3. **HIGH-LEVEL ONLY** - NO XML paths, NO XSD locations, NO implementation details
4. **BUSINESS LANGUAGE** - Describe WHAT changes, not HOW to implement it
5. **NO THINKING OUT LOUD** - Output ONLY the update instructions
6. **REFINE JIRA LANGUAGE** - Transform JIRA terminology (Acceptance Criteria, Story Points) into formal SR document language
7. **PROPER LINE BREAKS** - Use line breaks to make updates readable. Each update should be on multiple lines, not one long line.

**JIRA ANALYSIS PROCESS (INTERNAL - DO NOT OUTPUT):**
1. Is this a SPIKE/Investigation? (contains questions, "needs clarity") → Skip it
2. What is the BUSINESS requirement? (e.g., "Support UTC+14 timezone")
3. Which MESSAGE TYPE is affected? (e.g., Pacs.008, Pacs.002)
4. What VALIDATION RULE changes? (e.g., "regex pattern for DateTime")
5. Where in the SR document does this belong? (look at existing sections)

**OUTPUT FORMAT (CRITICAL - USE PROPER LINE BREAKS):**

**IMPORTANT - Add this note at the top of your output:**
```
📝 **Content Refinement Notice:** 
JIRA-specific terminology (Acceptance Criteria, Story Points, Given/When/Then) will be 
transformed into formal BSOL/SR document language (Validation Requirements, Test Conditions, 
The system shall...).

```

**For SPIKE stories:**
```
⚠️ [JIRA-ID] is a spike/investigation. 
No SR updates recommended until decisions are finalized.
```

**For CONCRETE requirements (USE THIS FORMAT WITH LINE BREAKS):**
```
✅ UPDATE [find existing section in document]: 
   [High-level change in business terms]
   **[Edit: [summary] | Source: [filename.doc]]**
```

**CORRECT EXAMPLES:**

Good ✅ (Notice the line breaks for readability):
```
📝 **Content Refinement Notice:** 
JIRA-specific terminology will be transformed into formal BSOL/SR document language.

✅ UPDATE existing DateTime validation section: 
   Expand CBPR_DateTime timezone offset support from UTC+13 to UTC+14 for Pacs.008 messages.
   This allows processing of messages from Pacific/Kiritimati timezone.
   **[Edit: UTC+14 timezone support | Source: APSMTN-15480.doc]**

✅ UPDATE Pacs.002 message configuration:
   Add support for hybrid address format in structured address fields.
   Both structured (street/city) and unstructured (single line) formats shall be accepted.
   **[Edit: Hybrid address support | Source: APSSE-487.doc]**
```
Why good: High-level, uses line breaks, references message type, describes the change clearly, NO XML paths

Bad ❌:
```
✅ UPDATE Section 2.1: Change regex from .*(+|-)((0[0-9])|(1[0-3])):[0-5][0-9] to .*(+|-)((0[0-9])|(1[0-4])):[0-5][0-9]
✅ ADD to Section 2.1: List XML paths: /AppHdr/CreDt, /Document/FIToFICstmrCdtTrf/GrpHdr/CreDtTm
```
Why bad: Includes implementation details (regex), lists XML paths (too technical), single long line, doesn't check if section exists

**LIVE SR DOCUMENT (Study this structure):**
{current_document[:50000]}

**NEW JIRA STORIES TO ANALYZE:**
{new_files_context}

**YOUR OUTPUT (High-level update instructions only):**
"""

    try:
        ai_response = run_agent_and_get_content(prompt)
        suggestion = ai_response["content"]
        
        if ai_response.get("usage"):
            new_log = TokenUsageLog(
                user_id=g.user.id,
                project_id=project_id,
                input_tokens=ai_response["usage"].get("input_tokens", 0),
                output_tokens=ai_response["usage"].get("output_tokens", 0)
            )
            db.session.add(new_log)
            db.session.commit()

        return jsonify({
            "suggestion": suggestion, 
            "new_files": new_file_names 
        })

    except Exception as e:
        print(f"❌ Error detecting changes: {e}")
        return jsonify({"error": str(e)}), 500
    

@agent_executor_bp.route("/projects/<int:project_id>/refine_document", methods=["POST"])
@token_required
def refine_document(project_id):
    project = Project.query.get_or_404(project_id)
    if not is_project_member(project, g.user):
        return jsonify({"error": "Unauthorized"}), 403

    data = request.json
    instruction = data.get("instruction")
    current_document = data.get("current_document")

    if not instruction or current_document is None:
        return jsonify({"error": "An instruction and the current document are required"}), 400

    user_display_name = g.user.username or g.user.email
    current_date = datetime.datetime.now().strftime('%b %d, %Y')
    
    # CRITICAL: Strip ALL old citations from document BEFORE AI sees it
    # This ensures AI starts with a clean document and only adds new citations
    clean_current_document = strip_all_citations(current_document)
    
    clean_instruction = instruction
    headers_to_remove = [
        "Update Proposal", "**Update Proposal**", "Based on the analysis", 
        "The following updates are proposed", "After reviewing the", 
        "Live Document", "source files", "proposed updates"
    ]
    for header in headers_to_remove:
        pattern = re.compile(re.escape(header), re.IGNORECASE)
        clean_instruction = pattern.sub("", clean_instruction)
    
    clean_instruction = clean_instruction.strip(" :-\n\t")

    # Create a brief, meaningful change note (max 150 chars for readability)
    if len(clean_instruction) <= 150:
        short_change_note = clean_instruction
    else:
        # Try to extract key action from instruction
        action_match = re.search(r'(update|add|remove|move|insert|delete|change)\s+(.+?)(?:\s+to\s+|\s+from\s+|\s+in\s+|$)', 
                                clean_instruction, re.IGNORECASE)
        if action_match:
            action = action_match.group(1).capitalize()
            target = action_match.group(2)[:100]  # Limit to 100 chars
            short_change_note = f"{action} {target}"
        else:
            # Fallback: use first 147 chars + "..."
            short_change_note = clean_instruction[:147] + "..."

    is_complex = len(clean_instruction) > 100 or "Section" in clean_instruction or instruction.startswith("UPDATE_FROM_FILE_CONTENT:")
    
    if is_complex:
        if instruction.startswith("UPDATE_FROM_FILE_CONTENT:"):
             clean_instruction = instruction.replace("UPDATE_FROM_FILE_CONTENT:", "").strip()

        # --- ENHANCED PROMPT FOR SR DOCUMENT COMPILATION FROM JIRA ---
        refinement_prompt = f"""
You are an **Intelligent SR Document Editor** with deep understanding of BSOL and SR document structures.

**CRITICAL UNDERSTANDING:**
- SR Documents have sections like: Introduction, Settlement Codes, Configuration, Cover Payments, etc.
- Sections are numbered: 1, 2, 2.1, 2.2, 2.3, etc.
- NEVER create duplicate sections - ALWAYS find and update existing ones
- NEVER output your thinking process - output ONLY the final updated document

**BEFORE MAKING ANY CHANGE:**
1. **READ the entire current document** to understand its structure
2. **IDENTIFY existing sections** by their numbers and headings
3. **LOCATE where changes belong** - find the matching section
4. **PLAN the update** - update existing content, don't append randomly

**INPUT INSTRUCTIONS:**
{clean_instruction[:25000]} 

**CRITICAL EXECUTION RULES:**

1. **INSTRUCTION PARSING:**
   - Each line starting with UPDATE/INSERT/ADD/REPLACE/MOVE is a separate instruction
   - Extract the section number (e.g., "Section 2.3.1")
   - Extract the action (update existing vs add new content)
   - Extract the technical content to add/modify
   - Extract the citation tag `**[Edit: ... | Source: ...]**`
   - **DETECT POSITIONAL KEYWORDS:** "after", "before", "at the top", "at the bottom", "move to"

2. **POSITIONAL INSTRUCTION HANDLING (CRITICAL):**
   - **"after [ELEMENT]"**: Place content IMMEDIATELY FOLLOWING the specified element
     * Example: "move Table of Contents after SR 2025 title" → Place TOC right after the title line, before any content
     * Do NOT place at end of document
   
   - **"before [ELEMENT]"**: Place content IMMEDIATELY PRECEDING the specified element
     * Example: "add warning before Section 1" → Insert warning paragraph right before "# 1. Section Title"
   
   - **"at the top"** or **"at the beginning"**: Place content after main document title, before any sections
     * Example: "move Revision History to the top" → Place after title but before section 1
   
   - **"at the bottom"** or **"at the end"**: Place content after last section, before legal notices if present
     * Example: "add glossary at the bottom" → Place after all sections
   
   - **"move [SECTION] to [POSITION]"**: Relocate entire section with all subsections
     * Example: "move Section 3 before Section 2" → Cut section 3 entirely and place it before section 2 starts
     * Preserve heading hierarchy and all content
   
   - **EXECUTION ORDER for MOVE operations:**
     1. Identify and extract the section/content to move (preserve formatting, subsections, tables, images)
     2. Find the target position (after X, before Y, etc.)
     3. Remove content from original location
     4. Insert at exact target position
     5. Do NOT duplicate - remove from old location when moving

3. **JIRA CONTENT REFINEMENT (CRITICAL - TRANSFORM JIRA LANGUAGE):**
   
   **YOU MUST TRANSFORM JIRA-SPECIFIC TERMINOLOGY INTO FORMAL BSOL/SR DOCUMENT LANGUAGE:**
   
   **JIRA Terms → SR Document Terms:**
   - "Acceptance Criteria" → "Validation Requirements" or "Test Conditions"
   - "Story Points" → DELETE (never include in document)
   - "Sub-Tasks" → DELETE (never include in document)
   - "As a user, I want..." → "The system shall..."
   - "Given/When/Then" → Formal requirement statements
   - "Story Description" → Technical specification
   - "Definition of Done" → DELETE or convert to validation rule
   - "Sprint" references → DELETE
   - "JIRA-12345" ticket IDs → Keep in citation only, not in main text
   
   **Content Transformation Examples:**
   
   ❌ WRONG (Raw JIRA copy):
   ```
   Acceptance Criteria:
   - Given a Pacs.008 message with timezone +14:00
   - When the system validates the DateTime field
   - Then the message should be accepted
   
   Story Points: 5
   Sub-Tasks: JIRA-456, JIRA-789
   ```
   
   ✅ CORRECT (Refined BSOL/SR):
   ```
   **Validation Requirements:**
   - All Pacs.008 messages with DateTime fields containing timezone offset +14:00 shall be accepted
   - The validation regex pattern shall support offsets from UTC-14:00 to UTC+14:00
   
   **Test Conditions:**
   - Verify message acceptance with DateTime value: 2025-03-01T22:00:00+14:00
   - Verify rejection of invalid offsets exceeding ±14:00
   ```
   
   **INTEGRATION RULES:**
   - For XML paths: Add them exactly as specified (e.g., /Document/FIToFICstmrCdtTrf/GrpHdr/CreDtTm)
   - For data types: Update patterns exactly (e.g., change regex from `(1[0-3])` to `(1[0-4])`)
   - For validation rules: Use formal language: "The system shall...", "Messages must..."
   - For JIRA "Acceptance Criteria": Convert to "Validation Requirements" or "Test Conditions"
   - DELETE all story management metadata (points, sprints, sub-tasks, assignees)

4. **TABLE CREATION (CRITICAL FOR JIRA REQUIREMENTS):**
   - **Field Specification Tables:** When instruction says "table with columns: Field Name, Data Type, Validation Rule, Mandatory"
     ```markdown
     | Field Name | Data Type | Validation Rule | Mandatory |
     |:-----------|:----------|:----------------|:----------|
     | CreDt | CBPR_DateTime | Pattern: .*(+|-)((0[0-9])|(1[0-4])):[0-5][0-9] | Yes |
     ```
   - **Message Format Tables:** For Pacs.008, Pacs.002 field mappings
   - **XML Path Tables:** For documenting affected message paths
   - Always include header row, separator row with alignment, then data rows
   - Extract actual values from instruction text - don't use placeholders

4. **SECTION MATCHING STRATEGY:**
   - **Exact Match:** Look for "## 2.3.1" or "### 2.3.1 Data Type Specifications"
   - **Fuzzy Match:** If "Section 2.3.1" doesn't exist, find "## 2.3 Data Types" 
   - **Parent Section:** If neither exists, find "## 2 Technical Specifications"
   - **Create New:** If no match, create new section in appropriate location
   - Maintain proper heading hierarchy (#, ##, ###, ####)

5. **TECHNICAL CONTENT EXTRACTION:**
   - **Validation Rules:** Extract patterns like `.*(+|-)((0[0-9])|(1[0-4])):[0-5][0-9]`
   - **Message Formats:** Extract Pacs.008, Pacs.002, BAH field specifications
   - **Data Types:** CBPR_DateTime, CBPR_Time, etc. with their constraints
   - **CR/Story References:** Include JIRA IDs, MR numbers, story links
   - **Acceptance Criteria:** Convert to testable requirement statements
   - **XSD Changes:** Note schema modifications and file locations

6. **CITATION RULES (CRITICAL - MANDATORY COMPLIANCE):**
   
   **STEP 1 - REMOVE OLD CITATIONS (DO THIS FIRST):**
   Before making ANY change, you MUST DELETE **ALL** existing citations in the affected area:
   - Remove ALL `**[Edit: ...]**` tags
   - Remove ALL `**[Source: ...]**` tags  
   - Remove ALL `✍️ User Request` occurrences
   - Remove ALL `✍️ UTC+14 timezone support | APSMTN-15480.doc` patterns
   - Remove ALL emoji-based citations (✍️, 📄, etc.)
   - Search the ENTIRE section you're modifying and clean it completely
   
   **EXAMPLES OF WHAT TO REMOVE:**
   - `INDA - Instructed Agent ✍️ User Request` → becomes `INDA - Instructed Agent`
   - `DateTime support ✍️ UTC+14 | APSMTN-15480.doc` → becomes `DateTime support`
   - `Copyright 2025 ✍️ User Request` → becomes `Copyright 2025`
   
   **STEP 2 - ADD NEW CITATION (PROPER FORMAT ONLY):**
   
   **MANDATORY CITATION FORMAT (CRITICAL - READ CAREFULLY):**
   - ALWAYS use MARKDOWN BOLD with square brackets: `**[Edit: ...]**`
   - NEVER EVER use emoji ✍️ or any other symbols
   - NEVER use plain text citations
   
   **FORMAT TEMPLATES:**
   
   **A) For changes WITH source file (JIRA-refined content):**
   ```
   Content here. **[Edit: brief description (refined from JIRA) | Source: filename.doc]**
   _Last edit: "change description" by {user_display_name} on {current_date}_
   ```
   
   **B) For changes WITHOUT source file:**
   ```
   Content here. **[Edit: User Request]**
   _Last edit: "change description" by {user_display_name} on {current_date}_
   ```
   
   **REAL EXAMPLES:**
   
   ✅ CORRECT (JIRA content refined):
   ```
   **Validation Requirements:**
   - All Pacs.008 messages with timezone offset +14:00 shall be accepted
   - The validation regex pattern shall support offsets from UTC-14:00 to UTC+14:00
   
   **[Edit: UTC+14 timezone validation (refined from JIRA) | Source: APSSE-487.doc]**
   _Last edit: "Pacs.002 DateTime requirements" by {user_display_name} on {current_date}_
   ```
   
   ❌ WRONG (Raw JIRA copy - DO NOT DO THIS):
   ```
   Acceptance Criteria:
   - Given a Pacs.008 message with timezone +14:00
   - When the system validates the DateTime
   - Then the message should be accepted
   
   ✍️ Hybrid address support | APSSE-487.doc
   ```
   **Why wrong:** Used raw JIRA terminology (Acceptance Criteria, Given/When/Then), used emoji instead of markdown citation

7. **BULK EXECUTION:**
   - Process ALL instructions in sequence
   - Don't stop after first instruction
   - If 10 instructions provided, apply all 10
   - Each instruction is independent - apply each one

8. **OUTPUT REQUIREMENTS (CRITICAL - NO THINKING):**
   - Return **COMPLETE SR DOCUMENT** with all changes integrated
   - Do NOT write "Step 1:", "Step 2:", or "The final answer is:"
   - Do NOT explain your reasoning or thinking process
   - Do NOT summarize - output ONLY the full updated document
   - Maintain existing structure: TOC, headers, images, tables
   - Preserve all content not mentioned in instructions
   - START directly with the document title (e.g., "SR 2025 Messages...")
   
   **AUTO-SCROLL MARKER AND CHANGE LOG (MANDATORY):**
   
   **FOR SINGLE CHANGE:**
   - After the citation, add change log:
     `_Last edit: "{short_change_note}" by {user_display_name} on {current_date}_`
   - After change log, add marker on OWN line:
     `<!-- LATEST_CHANGE -->`
   
   **FOR MULTIPLE CHANGES (BULK UPDATES):**
   - Add citation + change log after EACH change
   - Add the marker `<!-- LATEST_CHANGE -->` ONLY after the FIRST change (top of document)
   - This ensures auto-scroll takes user to the first/primary change
   
   Example with multiple changes:
   ```markdown
   2.3.4 Pacs.002 Message Configuration
   Address handling supports hybrid format. **[Edit: Hybrid address support | Source: APSSE-487.doc]**
   _Last edit: "Pacs.002 updates" by {user_display_name} on {current_date}_
   <!-- LATEST_CHANGE -->

   2.3.5 DateTime Validation for Pacs.002 Messages
   UTC+14 timezone now supported. **[Edit: DateTime UTC+14 support | Source: APSSE-487.doc]**
   _Last edit: "Pacs.002 updates" by {user_display_name} on {current_date}_

   2.3.6 Business Service Value
   BizSvc must be swift.cbprplus.03. **[Edit: BizSvc value update | Source: APSSE-487.doc]**
   _Last edit: "Pacs.002 updates" by {user_display_name} on {current_date}_
   ```

9. **STRUCTURE PRESERVATION:**
   - **Table of Contents:** Update if section names/numbers changed
   - **Existing Tables:** Keep unless explicitly told to replace
   - **Images:** Preserve all `![](path)` references
   - **Heading Hierarchy:** Maintain consistent ## ### #### levels
   - **Legal Notices:** Never modify unless explicitly instructed
   - **Document Header:** Do NOT add or modify ANY "Last edit" line in the header
   - Keep document title clean without any edit tracking information

**CURRENT SR DOCUMENT:**
{clean_current_document}
"""
        change_desc = "Integrated JIRA requirements from approved stories"

    else:
        refinement_prompt = f"""
        You are an expert document editor. Apply this edit: "{clean_instruction}"

        **CRITICAL OUTPUT RULE #1 - RETURN COMPLETE DOCUMENT:**
        - You MUST return the ENTIRE document from start to finish
        - Do NOT return only the changed section
        - Do NOT truncate or omit any sections
        - Keep ALL sections: 1, 1.1, 2, 2.1, 2.2, 2.3, 2.4, etc.
        - Preserve ALL content: tables, images, subsections, everything

        **CRITICAL OUTPUT RULE #2 - CITATION PLACEMENT:**
        - Find the section you modified (e.g., Section 1)
        - Apply your change to that section
        - Place citation AFTER the entire modified section (before next section starts)
        - Then continue with rest of document unchanged

        **CITATION FORMAT (MANDATORY - NO BOLD, NO EMOJI):**
        ```
        [Edit: User Request]
        _Last edit: "{short_change_note}" by {user_display_name} on {current_date}_
        <!-- LATEST_CHANGE -->
        ```

        **CORRECT EXAMPLE - Converting Section 1 to bullet points:**
        ```
        SR 2025 Messages Configuration

        TABLE OF CONTENTS
        - 1. SETTLEMENT CODES
        - 2. CONFIGURATION
        - 3. OTHER SECTIONS

        ## 1. SETTLEMENT CODES:

        - **INDA** – Instructed Agent
        - **INGA** – Instructing Agent  
        - **COVE** – Cover Method
        - **CLRG** – Not supported in Cross Border

        [Edit: User Request]
        _Last edit: "make the content of this section in bullet points" by {user_display_name} on {current_date}_
        <!-- LATEST_CHANGE -->

        ### 1.1 NOTE
        Settlement code decides whether transaction will be settled at instructing agent or Instructed agent.

        ## 2. CONFIGURATION BASED ON INDA & INGA
        (rest of Section 2 content preserved exactly as-is)

        ## 3. OTHER SECTIONS
        (all remaining content preserved)
        ```

        **WRONG - NEVER DO THIS:**
        ```
        ## 1. SETTLEMENT CODES:
        - INDA – Instructed Agent
        - CLRG – Not supported ✍️ User Request
        Last edit: "bullet points" by name

        ### 1.1 NOTE
        Settlement code decides...
        ```
        **Why wrong:** Uses emoji ✍️, citation after last bullet only, MISSING all sections after 1.1

        **STEP-BY-STEP EXECUTION:**
        1. Read the ENTIRE current document below
        2. Find the section mentioned in instruction (e.g., "Section 1")
        3. Apply the change ONLY to that section
        4. Place citation after that section (before next section)
        5. Return COMPLETE document with ALL sections preserved

        **CURRENT DOCUMENT (ALL OF IT - PRESERVE EVERYTHING):**
        {clean_current_document}
        """
        change_desc = clean_instruction

    try:
        ai_response = run_agent_and_get_content(refinement_prompt)
        document_content = ai_response["content"]
        usage = ai_response["usage"]

        cleaned_content = clean_preamble(document_content)
        
        # Extract scroll target BEFORE removing marker
        # For bulk updates with multiple changes, find the FIRST marker occurrence
        scroll_target = None
        marker = '<!-- LATEST_CHANGE -->'
        if marker in cleaned_content:
            scroll_target = 'LATEST_CHANGE'
            # Remove ALL occurrences of the marker from final content
            # (AI might add multiple, we want to clean them all)
            cleaned_content = cleaned_content.replace(marker, '')
        
        if usage:
            new_log = TokenUsageLog(
                user_id=g.user.id,
                project_id=project_id,
                input_tokens=usage.get("input_tokens", 0),
                output_tokens=usage.get("output_tokens", 0)
            )
            db.session.add(new_log)
            
        safe_description = (change_desc[:150] + '...') if len(change_desc) > 150 else change_desc

        new_version = DocumentVersion(
            content=cleaned_content, 
            change_description=safe_description, 
            project_id=project_id, 
            user_id=g.user.id
        )
        db.session.add(new_version)
        db.session.commit()
        
        # If scroll_target wasn't set by LATEST_CHANGE marker, try to extract from instruction
        if not scroll_target:
            # PRIORITY 2: Try to find section number with various formats: "Section 2.1", "section 2.4.1", "2.1"
            section_match = re.search(r'(?:section|Section)?\s*([\d.]+(?:\.\d+)*)', clean_instruction, re.IGNORECASE)
            if section_match:
                scroll_target = section_match.group(1)
            # PRIORITY 3: Try to find heading/keyword after UPDATE/ADD/INSERT/MOVE/REMOVE
            elif any(keyword in clean_instruction.upper() for keyword in ['UPDATE', 'ADD', 'INSERT', 'MOVE', 'REMOVE']):
                action_match = re.search(r'(?:UPDATE|ADD|INSERT|MOVE|REMOVE)\s+(?:existing\s+)?(?:the\s+)?([^:]+)', clean_instruction, re.IGNORECASE)
                if action_match:
                    content_desc = action_match.group(1).strip()
                    # Extract key content words (e.g., "table of contents", "legal notices")
                    scroll_target = re.sub(r'\\s+(section|subsection|heading|paragraph)\\s*$', '', content_desc, flags=re.IGNORECASE)
            # PRIORITY 4: Fallback - extract content keywords
            else:
                keyword_match = re.search(r'([A-Z][a-zA-Z]+(?:\\s+[A-Z][a-zA-Z]+)*)', clean_instruction)
                if keyword_match:
                    scroll_target = keyword_match.group(1)
        
        return jsonify({
            "content": cleaned_content,
            "scroll_target": scroll_target
        })

    except Exception as e:
        db.session.rollback()
        print(f"ERROR DURING REFINEMENT: {e}")
        return jsonify({"error": str(e)}), 500

@agent_executor_bp.route("/projects/<int:project_id>/ask_question", methods=["POST"])
@token_required
def ask_question(project_id):
    project = Project.query.get_or_404(project_id)
    if not is_project_member(project, g.user):
        return jsonify({"error": "Unauthorized"}), 403

    data = request.json
    question = data.get("question")
    current_document = data.get("current_document")

    if not question or current_document is None:
        return jsonify({"error": "A question and the current document are required"}), 400

    try:
        rag = ElysiaWrapper()
        rag_result = rag.rag_query(question, top_k=5)
        rag_text = ""
        if rag_result and "results" in rag_result:
            for item in rag_result["results"]:
                rag_text += f"- {item.get('text', '')}\n"
    except Exception as e:
        rag_text = ""
        print(f"Elysia RAG failed: {e}")

    prompt = f"""
    You are a smart Project Document Assistant.
    Your goal is to answer the user's question by synthesizing information from the **Current Document** and the **RAG Retrieved Context**.

    **INPUT DATA:**
    - QUESTION: "{question}"
    - DOCUMENT: {current_document[:20000]} (truncated if too long)
    - RAG CONTEXT: {rag_text}

    **OUTPUT FORMAT:**
    Return a single JSON object with these keys:
    {{
        "answer": "Your direct answer here.",
        "scrollToText": "Exact section heading to scroll to, or null if not applicable.",
        "suggestion": "An optional ACTIONABLE command to edit the document, or null."
    }}

    **LOGIC RULES FOR 'suggestion':**
    1. **If the user asks about a missing section:** (e.g., "Do I have a Security section?")
       - ANSWER: "No, that section is missing from the document."
       - SUGGESTION: "Create a 'Security' section detailing authentication and data protection." (This must be a clear command for the AI Editor).
    
    2. **If the user asks to change something:** (e.g., "Should we change the database?")
       - ANSWER: Explain the pros/cons based on context.
       - SUGGESTION: "Update the database section to use PostgreSQL instead of SQLite."

    3. **If the answer is found:**
       - ANSWER: Provide the answer directly from the document or RAG context.
       - SUGGESTION: null (unless there is a clear follow-up improvement).

    **DO NOT** return markdown code blocks (like ```json). Just return the JSON string.
    """
    
    try:
        ai_response = run_agent_and_get_content(prompt)
        ai_text = ai_response["content"]
        usage = ai_response["usage"]

        if usage:
            new_log = TokenUsageLog(
                user_id=g.user.id,
                project_id=project_id,
                input_tokens=usage.get("input_tokens", 0),
                output_tokens=usage.get("output_tokens", 0)
            )
            db.session.add(new_log)
            db.session.commit()

        json_data = extract_json(ai_text)

        if isinstance(json_data, dict) and "answer" in json_data:
            return jsonify({
                "answer": json_data.get("answer"),
                "scrollToText": json_data.get("scrollToText"),
                "suggestion": json_data.get("suggestion"),
                "rag_used": bool(rag_text.strip()),
            })

        return jsonify({
            "answer": ai_text,
            "scrollToText": None,
            "suggestion": None,
            "rag_used": bool(rag_text.strip()),
        })

    except Exception as e:
        error_msg = str(e)
        db.session.rollback()
        
        if "429" in error_msg or "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
            print(f"⏳ Rate Limit Hit: {error_msg}")
            return jsonify({
                "answer": "⚠️ **System Busy:** The AI model is currently experiencing high traffic (Rate Limit). Please wait 60 seconds and try again.",
                "scrollToText": None,
                "suggestion": None,
                "rag_used": False
            }), 200
            
        print(f"ERROR DURING Q&A: {e}")
        return jsonify({"error": str(e)}), 500

@agent_executor_bp.route("/projects/<int:project_id>/versions", methods=["GET"])
@token_required
def get_versions(project_id):
    project = Project.query.get_or_404(project_id)
    if not is_project_member(project, g.user): return jsonify({"error": "Unauthorized"}), 403
    versions = DocumentVersion.query.filter_by(project_id=project_id).order_by(DocumentVersion.timestamp.desc()).all()
    return jsonify([v.to_dict() for v in versions])

@agent_executor_bp.route("/projects/<int:project_id>/versions/<int:version_id>", methods=["PUT"])
@token_required
def update_version_description(project_id, version_id):
    project = Project.query.get_or_404(project_id)
    if not is_project_member(project, g.user):
        return jsonify({"error": "Unauthorized"}), 403
        
    version = DocumentVersion.query.get_or_404(version_id)
    if version.project_id != project.id:
        return jsonify({"error": "Version not found in this project"}), 404

    data = request.json
    new_description = data.get("description")
    
    if not new_description:
        return jsonify({"error": "New description cannot be empty"}), 400
        
    try:
        version.change_description = new_description
        db.session.commit()
        return jsonify(version.to_dict()), 200
    except Exception as e:
        db.session.rollback() 
        print(f"ERROR updating version description: {e}")
        return jsonify({"error": "Failed to update version"}), 500

@agent_executor_bp.route("/projects/<int:project_id>/versions", methods=["POST"])
@token_required
def save_version(project_id):
    project = Project.query.get_or_404(project_id)
    if not is_project_member(project, g.user): return jsonify({"error": "Unauthorized"}), 403
    data = request.json
    content = data.get("content")
    change_description = data.get("change_description")
    if not content or not change_description: return jsonify({"error": "Content and a change description are required"}), 400
    
    try:
        new_version = DocumentVersion(content=content, change_description=change_description, project_id=project_id, user_id=g.user.id)
        db.session.add(new_version)
        db.session.commit()
        return jsonify(new_version.to_dict()), 201
    except Exception as e:
        db.session.rollback() 
        print(f"ERROR saving new version: {e}")
        return jsonify({"error": "Failed to save new version"}), 500

@agent_executor_bp.route("/projects/<int:project_id>/versions", methods=["DELETE"])
@token_required
def delete_all_versions(project_id):
    project = Project.query.get_or_404(project_id)
    if not is_project_member(project, g.user): return jsonify({"error": "Unauthorized"}), 403
    try:
        num_deleted = DocumentVersion.query.filter_by(project_id=project_id).delete()
        db.session.commit()
        print(f"✅ Reset workspace for project {project_id}, deleted {num_deleted} versions.")
        return jsonify({"message": "Workspace reset successfully."}), 200
    except Exception as e:
        db.session.rollback() 
        print(f"❌ Error resetting workspace for project {project_id}: {e}")
        return jsonify({"error": "Internal error resetting workspace."}), 500

@agent_executor_bp.route("/projects/<int:project_id>/suggestions", methods=["POST"])
@token_required
def get_suggestions(project_id):
    project = Project.query.get_or_404(project_id)
    if not is_project_member(project, g.user):
        return jsonify({"error": "Unauthorized"}), 403

    data = request.json
    current_document = data.get("current_document")
    if not current_document:
        return jsonify([])

    prompt = f"""
    You are an AI assistant whose ONLY job is to generate a JSON array of strings.
    Your output MUST be a valid JSON array.

    Analyze the provided document and generate exactly 3 brief, actionable suggestions for specific improvements.

    RULES:
    - Keep suggestions concise (max 7 words).
    - **IMPORTANT:** If you need to quote a term inside a suggestion, USE SINGLE QUOTES ONLY. Do NOT use double quotes inside the string.
      - ❌ BAD: "Add "Data Model" section"
      - ✅ GOOD: "Add 'Data Model' section"
    - **Your FINAL response MUST be ONLY the JSON array and nothing else.**
    - Do NOT return an object, markdown, or any other text.
    - Example: ["Add 'Data Model' section", "Clarify non-functional requirements", "Reformat section 4"]

    DOCUMENT TO ANALYZE:
    {current_document[:4000]}
    """
    try:
        ai_response = run_agent(prompt)
        ai_text = ai_response["content"]
        usage = ai_response["usage"]

        if usage:
            new_log = TokenUsageLog(
                user_id=g.user.id,
                project_id=project_id,
                input_tokens=usage.get("input_tokens", 0),
                output_tokens=usage.get("output_tokens", 0)
            )
            db.session.add(new_log)
            db.session.commit()
        
        suggestions_json = extract_json(ai_text) 

        if isinstance(suggestions_json, list) and len(suggestions_json) > 0 and all(isinstance(s, str) for s in suggestions_json):
            return jsonify(suggestions_json[:3])
        else:
             if suggestions_json is None: log_msg = "extract_json returned None (parsing failed)."
             elif not isinstance(suggestions_json, list): log_msg = f"Parsed list is not a list (type: {type(suggestions_json)})."
             elif len(suggestions_json) == 0: log_msg = "Parsed list is empty."
             else: log_msg = "Parsed list contains non-string items."
             print(f"⚠️ Failed to get valid suggestions. Reason: {log_msg}. Raw AI: {ai_text[:200]}...")
             raise ValueError("AI did not return valid suggestions.")

    except Exception as e:
        db.session.rollback() 
        print(f"ERROR DURING SUGGESTION GENERATION or validation: {e}")
        return jsonify([
            "Review requirements for completeness",
            "Add 'Security' constraints",
            "Clarify scope details"
        ]), 200
from flask import Blueprint, request, jsonify, current_app
import pymupdf4llm
import tempfile
import os
import mammoth
from routes.utils import token_required
from services.ai_agent import run_agent # Import your existing agent service
import json
import uuid
import re
from bs4 import BeautifulSoup

extract_bp = Blueprint("extract", __name__)

# --- JIRA Ticket Enhancement Helper ---
def enhance_jira_ticket(raw_jira_content: str) -> str:
    """
    Uses AI to clean, structure, and enhance JIRA ticket content.
    Keeps only relevant information for requirements extraction.
    Discards metadata, formatting artifacts, and irrelevant details.
    """
    enhancement_prompt = """You are a requirements analyst. You have been given a JIRA ticket export that may contain:
- Excessive metadata (dates, timestamps, user IDs)
- Formatting artifacts from HTML conversion
- Irrelevant system information
- Poorly structured descriptions
- Redundant or duplicate information

Your task:
1. Extract and restructure ONLY the relevant information needed for requirements analysis
2. Focus on: Story Title, Description, Acceptance Criteria, Business Value, Technical Details
3. Remove: System metadata, timestamps, user IDs, HTML artifacts, navigation elements
4. Reorganize content into a clear, readable structure
5. Preserve all functional and non-functional requirements mentioned
6. Keep any constraints, assumptions, or dependencies
7. Discard irrelevant information

Return a clean, well-structured document that highlights the business requirements and technical specifications.

JIRA Content:
---
{content}
---

Enhanced Output (markdown format):"""

    try:
        result = run_agent(
            system_prompt="You are an expert at cleaning and structuring JIRA tickets for requirements analysis.",
            user_prompt=enhancement_prompt.format(content=raw_jira_content),
            max_tokens=4000
        )
        
        enhanced_content = result.get("content", "").strip()
        
        if enhanced_content and len(enhanced_content) > 100:
            print(f"✅ Enhanced JIRA ticket: {len(raw_jira_content)} chars → {len(enhanced_content)} chars")
            return enhanced_content
        else:
            print("⚠️ Enhancement failed, returning original content")
            return raw_jira_content
            
    except Exception as e:
        print(f"❌ Error enhancing JIRA ticket: {str(e)}")
        return raw_jira_content

# --- Helper to save images from Mammoth ---
def save_image(image):
    # 1. Generate a unique filename
    image_id = str(uuid.uuid4())
    content_type = image.content_type
    ext = ".jpg"
    if "png" in content_type: ext = ".png"
    elif "gif" in content_type: ext = ".gif"
    elif "svg" in content_type: ext = ".svg"
    
    filename = f"{image_id}{ext}"
    
    # 2. Define path (Ensure your config has static folder setup)
    static_images_dir = os.path.join(current_app.root_path, "static", "images")
    os.makedirs(static_images_dir, exist_ok=True)
    
    file_path = os.path.join(static_images_dir, filename)
    
    # 3. Save the image bytes to disk
    with image.open() as image_bytes:
        with open(file_path, "wb") as f:
            f.write(image_bytes.read())
    
    # 4. Return the src attribute for the HTML <img> tag
    return { "src": f"/static/images/{filename}" }

# --- Helper for .doc files (Jira Exports) ---
def extract_from_doc(file_path):
    """
    Handles .doc files. 
    Note: Many 'doc' files from web exports (like Jira) are actually HTML/XML.
    We try parsing as HTML first with AI-powered structuring for JIRA stories.
    """
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            # Heuristic: Check if it looks like HTML
            if "<html" in content.lower() or "<body" in content.lower() or "xmlns:" in content.lower():
                soup = BeautifulSoup(content, "html.parser")
                
                # Check if it's a JIRA story (common indicators)
                is_jira = any(keyword in content for keyword in ["JIRA", "jira", "Sub-Tasks:", "Acceptance Criteria", "Story Points"])
                
                if is_jira:
                    print("🎫 Detected JIRA story - extracting Description section only...")
                    
                    # --- EXTRACT ONLY THE DESCRIPTION SECTION ---
                    # Find the description area in JIRA HTML exports
                    description_area = soup.find(id="descriptionArea")
                    
                    if description_area:
                        # Get the text content from the description area
                        description_text = description_area.get_text(separator="\n", strip=True)
                        
                        # Clean up the description
                        description_text = re.sub(r'\n{3,}', '\n\n', description_text)
                        
                        # Build a structured output with JIRA metadata + Description ONLY
                        title = soup.find("title")
                        title_text = title.get_text(strip=True) if title else "JIRA Story"
                        
                        # Extract story type (Task, Spike, User Story, etc.)
                        story_type = "Unknown"
                        type_cell = soup.find("b", string="Type:")
                        if type_cell and type_cell.parent and type_cell.parent.find_next_sibling("td"):
                            story_type = type_cell.parent.find_next_sibling("td").get_text(strip=True)
                        
                        output = f"""# {title_text}

**Type:** {story_type}

## Description

{description_text}
"""
                        print(f"✅ Extracted Description section only ({len(description_text)} chars)")
                        
                        # --- ENHANCE JIRA TICKET WITH AI ---
                        print("🤖 Enhancing JIRA ticket with AI...")
                        enhanced_output = enhance_jira_ticket(output)
                        return enhanced_output
                    else:
                        # Fallback: If no description area found, return minimal info
                        print("⚠️ No description area found in JIRA export")
                        return "No description available in this JIRA export."
                else:
                    # Regular HTML extraction
                    return soup.get_text(separator="\n\n")
            else:
                # If it's actual binary content that was read as text, it will look like garbage.
                # Real binary .doc files require tools like 'antiword' or 'textract', 
                # but for Jira/Web exports, the HTML method covers 95% of cases.
                return content
    except Exception as e:
        return f"Error reading .doc file: {str(e)}"

def extract_structured_text(file, file_ext):
    """
    Extracts content based on file type. 
    Uses AI Reconstruction for DOCX to ensure BSOL structure is preserved.
    """
    try:
        # 1. TEXT / JSON
        if file.content_type == "text/plain" or file_ext in ['.txt', '.md']:
            file.stream.seek(0)
            return file.stream.read().decode("utf-8")
        
        elif file.content_type == "application/json" or file_ext == '.json':
            file.stream.seek(0)
            data = json.load(file.stream)
            if isinstance(data, list):
                return "\n".join([f"{t.get('speaker','Unknown')}: {t.get('text','')}" for t in data])
            elif isinstance(data, str):
                return data
            else:
                return json.dumps(data, indent=2)

        # 2. PDF (Use PyMuPDF4LLM)
        elif file.content_type == "application/pdf" or file_ext == '.pdf':
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
                file.stream.seek(0)
                temp_pdf.write(file.stream.read())
                temp_path = temp_pdf.name
            try:
                md_text = pymupdf4llm.to_markdown(temp_path)
                return md_text
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)

        # 3. DOC (Old Word / Jira Export)
        elif file_ext == '.doc' or file.content_type == "application/msword":
            with tempfile.NamedTemporaryFile(delete=False, suffix=".doc") as temp_doc:
                file.stream.seek(0)
                temp_doc.write(file.stream.read())
                temp_path = temp_doc.name
            try:
                # Use the HTML parser strategy for Jira exports
                return extract_from_doc(temp_path)
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)

        # 4. DOCX (AI-POWERED RECONSTRUCTION)
        elif file.content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document" or file_ext == '.docx':
            file.stream.seek(0)
            
            try:
                # A. Convert DOCX -> Raw HTML (Preserving Images)
                result = mammoth.convert_to_html(
                    file, 
                    convert_image=mammoth.images.img_element(save_image)
                )
                raw_html = result.value
                
                if not raw_html or not raw_html.strip():
                    return "# Error\n\nDocument appears empty after initial processing."

                # B. Construct the AI Prompt (ENHANCED FOR BSOL/SR DOCUMENTS)
                prompt = f"""
You are an expert document converter specializing in BSOL (Business Solution) and SR (System Requirements) documents.
I have converted a Word document to HTML. Your task is to reconstruct it into clean **GitHub Flavored Markdown (GFM)**.

**CRITICAL RULES:**
1.  **PRESERVE EVERYTHING:** Do NOT summarize. Do NOT skip sections. BSOL documents contain critical technical specifications.
2.  **LEGAL NOTICES:** Keep "Legal Notices", "Trademarks", and "Copyright" sections exactly as they appear.
3.  **REVISION HISTORY:** Keep the "Revision History" table. Format as Markdown table with proper column alignment.
4.  **TABLE OF CONTENTS (TOC) - CRITICAL PLACEMENT:**
    * **LOCATION:** Place TOC immediately after the document title and any subtitle/metadata
    * If the original document has a TOC, preserve it at the TOP (after title, before content sections)
    * **DO NOT** generate your own TOC - use the existing one from the document
    * **DO NOT** move TOC to the bottom or middle of the document
    * Format: `- [Title](#link)` with proper indentation for hierarchy
    * **REMOVE** page numbers (e.g., "1-3") and dot leaders (......)
    * Example structure:
      ```
      # Document Title
      
      ## Table of Contents
      - [Section 1](#section-1)
        - [Section 1.1](#section-11)
      - [Section 2](#section-2)
      
      ## Section 1
      Content...
      ```
5.  **TABLES (CRITICAL FOR BSOL):**
    * Convert ALL HTML tables to Markdown tables
    * Preserve all columns and rows - do NOT omit data
    * Maintain column alignment (use `:---` for left, `:---:` for center, `---:` for right)
    * Keep validation rules, message formats, field mappings intact
    * For complex tables with merged cells, use best-effort Markdown representation
6.  **IMAGES/DIAGRAMS:**
    * Convert `<img src="/static/images/..." />` to `![Description](/static/images/...)`
    * Keep exact paths - these may be flowcharts or architecture diagrams
7.  **TECHNICAL CONTENT:**
    * Preserve all: validation rules, data types, constraints, message formats, field definitions
    * Keep code blocks, XML/JSON examples, regex patterns intact
8.  **HEADINGS:** Use `#`, `##`, `###` based on document hierarchy
9.  **CLEAN UP:** Only remove footer artifacts like "Page X of Y" or "End of Document". Do NOT remove content.

**Input HTML:**
{raw_html}
"""
                # C. Call your AI Agent
                print("🤖 Sending document to AI for reconstruction...")
                ai_response = run_agent(prompt)
                markdown_output = ai_response.get("content", "")
                
                # D. DETECT AND ENHANCE JIRA TICKETS IN DOCX
                # Check if the content looks like a JIRA ticket
                is_jira_ticket = any(indicator in markdown_output[:2000] for indicator in [
                    "Story Metadata", "Sub-Tasks", "Acceptance Criteria", 
                    "JIRA-", "Story Points", "Sprint", "Assignee", "Reporter"
                ])
                
                if is_jira_ticket:
                    print("🎫 Detected JIRA ticket in DOCX - enhancing...")
                    markdown_output = enhance_jira_ticket(markdown_output)
                
                return markdown_output

            except Exception as e:
                print(f"❌ Extraction process failed: {e}")
                return f"# Error\n\nFailed to process document: {e}"

    except Exception as e:
        print(f"❌ General extraction failed: {e}")
        return ""

    return ""

@extract_bp.route("/extract_text", methods=["POST"])
@token_required
def extract_text_endpoint():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files["file"]
    filename = file.filename.lower()
    _, file_ext = os.path.splitext(filename)
    
    # Pass extension explicitly to handle mime-type inconsistencies
    markdown_text = extract_structured_text(file, file_ext)
    
    if not markdown_text.strip():
        return jsonify({"error": "Could not extract text from this file."}), 400

    print(f"📄 Extracted & Reconstructed {len(markdown_text)} chars from {file.filename}")

    return jsonify({
        "text": markdown_text,
        "pdf_preview_url": None 
    })
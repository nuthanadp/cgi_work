import os
import re
from docx import Document
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def sanitize_filename_keep_ext(filename):
    """
    Sanitize filename keeping extension.
    Example: "My Report V2.docx" -> "My_Report_V2.docx"
    """
    name, ext = os.path.splitext(filename)
    # Replace non-alphanumeric (except dots/dashes in name) with underscore
    name = re.sub(r'[^a-zA-Z0-9\.\-]', '_', name)
    # Clean multiple underscores
    name = re.sub(r'_+', '_', name)
    # Remove leading/trailing dots/underscores
    name = name.strip('._')
    return f"{name}{ext.lower()}"

def clean_text(text):
    """Clean extracted text."""
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove control characters but keep newlines
    text = re.sub(r'[\x00-\x09\x0b\x0c\x0e-\x1f\x7f]', '', text)
    return text.strip()

def doc_to_text_v2(file_path):
    """
    Extract text from DOCX files using python-docx.
    Handles headings, paragraphs, and tables in order.
    """
    try:
        doc = Document(file_path)
        full_text = []
        
        # Iterate through all elements in the document body
        for element in doc.element.body:
            if element.tag.endswith('p'):  # Paragraph
                para_text = ""
                for child in element.iter():
                    if child.tag.endswith('t'):  # Text run
                        if child.text:
                            para_text += child.text
                if para_text.strip():
                    full_text.append(para_text.strip())
                    
            elif element.tag.endswith('tbl'):  # Table
                # Find the table object corresponding to this element
                table = None
                for t in doc.tables:
                    if t._element == element:
                        table = t
                        break
                
                if table:
                    for row in table.rows:
                        row_text = []
                        for cell in row.cells:
                            cell_text = cell.text.strip()
                            if cell_text:
                                row_text.append(cell_text)
                        if row_text:
                            full_text.append(" | ".join(row_text))
                            
        return "\n\n".join(full_text)
        
    except Exception as e:
        logger.error(f"Error extracting text from {file_path}: {str(e)}")
        raise Exception(f"Failed to extract text: {str(e)}")
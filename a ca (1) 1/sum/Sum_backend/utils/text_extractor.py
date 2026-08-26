from PyPDF2 import PdfReader
from docx import Document

def extract_text(file):
    if file.content_type == "text/plain":
        return file.read().decode("utf-8")
    elif file.content_type == "application/pdf":
        pdf = PdfReader(file)
        text = ""
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text
    elif file.content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = Document(file)
        return "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
    return ""

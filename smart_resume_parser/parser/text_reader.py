import fitz  # PyMuPDF
import docx
from io import BytesIO
from typing import Union


def extract_text_from_pdf(file_bytes: bytes) -> str:
    text_chunks = []
    with fitz.open(stream=file_bytes, filetype="pdf") as doc:
        for page in doc:
            text_chunks.append(page.get_text("text"))
    return "\n".join(text_chunks)


def extract_text_from_docx(file_bytes: bytes) -> str:
    doc = docx.Document(BytesIO(file_bytes))
    lines = [para.text for para in doc.paragraphs]
    return "\n".join(lines)


def extract_text(file_name: str, file_bytes: bytes) -> str:
    file_name_lower = file_name.lower()
    if file_name_lower.endswith(".pdf"):
        return extract_text_from_pdf(file_bytes)
    elif file_name_lower.endswith(".docx"):
        return extract_text_from_docx(file_bytes)
    else:
        raise ValueError("Unsupported file type. Only PDF and DOCX are supported.")

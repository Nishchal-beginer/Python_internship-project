import re
from typing import Dict


def clean_text(text: str) -> str:
    # Normalize newlines, remove extra spaces
    text = text.replace("\r", "\n")
    text = re.sub(r"\n{2,}", "\n\n", text)        # collapse many blank lines
    text = re.sub(r"[ \t]+", " ", text)          # collapse multiple spaces
    return text.strip()


SECTION_REGEX = re.compile(
    r"(?im)^(education|work experience|experience|professional experience|"
    r"skills|technical skills|projects|certifications|summary|profile)\s*:?\s*$"
)


def split_into_sections(text: str) -> Dict[str, str]:
    """
    Split resume text into sections based on headings.
    Returns dict: {section_name_lower: section_text}
    """
    lines = text.split("\n")
    sections = {}
    current_section = "header"
    buffer = []

    def flush_buffer(sec_name):
        if buffer:
            sections[sec_name] = "\n".join(buffer).strip()

    for line in lines:
        match = SECTION_REGEX.match(line.strip())
        if match:
            # new section begins
            flush_buffer(current_section)
            current_section = match.group(1).lower()
            buffer = []
        else:
            buffer.append(line)

    flush_buffer(current_section)
    return sections

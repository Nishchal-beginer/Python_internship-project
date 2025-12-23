import re
from typing import List, Dict, Any, Optional
import spacy
from .utils import clean_text, split_into_sections

# Load spaCy model once
nlp = spacy.load("en_core_web_sm")

# Simple skills list; you can expand this or load from data/skills_list.txt
DEFAULT_SKILLS = {
    "python", "java", "c++", "javascript", "typescript", "react", "node.js",
    "django", "flask", "sql", "mysql", "postgresql", "mongodb", "aws",
    "azure", "gcp", "docker", "kubernetes", "git", "machine learning",
    "deep learning", "nlp", "pandas", "numpy", "tensorflow", "pytorch",
    "html", "css", "power bi", "tableau", "excel"
}

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_REGEX = re.compile(
    r"(\+?\d[\d\- ]{7,}\d)"
)
YEAR_REGEX = re.compile(r"(19|20)\d{2}")


def extract_email(text: str) -> Optional[str]:
    match = EMAIL_REGEX.search(text)
    return match.group(0) if match else None


def extract_phone(text: str) -> Optional[str]:
    match = PHONE_REGEX.search(text)
    return match.group(0) if match else None


def extract_name(doc) -> Optional[str]:
    """
    Very naive: take the first PERSON entity in the first 3 lines,
    or first line if nothing found.
    """
    lines = [l.strip() for l in doc.text.split("\n") if l.strip()]
    top_text = "\n".join(lines[:3])
    top_doc = nlp(top_text)

    persons = [ent.text for ent in top_doc.ents if ent.label_ == "PERSON"]
    if persons:
        return persons[0]

    return lines[0] if lines else None


def extract_skills(text: str, skills_vocab: Optional[set] = None) -> List[str]:
    if skills_vocab is None:
        skills_vocab = DEFAULT_SKILLS

    found = set()
    lower_text = text.lower()
    for skill in skills_vocab:
        if skill.lower() in lower_text:
            found.add(skill)
    return sorted(found)


def parse_education_section(section_text: str) -> List[Dict[str, Any]]:
    """
    Very simple heuristic parser for education entries.
    """
    entries = []
    for block in section_text.split("\n\n"):
        block = block.strip()
        if not block:
            continue

        entry = {"degree": None, "institution": None, "start_year": None, "end_year": None, "raw": block}

        # Degree keywords
        degree_match = re.search(
            r"(Bachelor|Master|B\.?Sc|M\.?Sc|B\.?Tech|M\.?Tech|B\.?Eng|M\.?Eng|Ph\.?D|MBA)[^,\n]*",
            block, re.IGNORECASE
        )
        if degree_match:
            entry["degree"] = degree_match.group(0).strip()

        # Years (take up to two)
        years = YEAR_REGEX.findall(block)
        # YEAR_REGEX.findall returns tuples like ('20','23'), so extract full years from re.finditer instead
        years = [m.group(0) for m in YEAR_REGEX.finditer(block)]

        if len(years) >= 1:
            entry["start_year"] = years[0]
        if len(years) >= 2:
            entry["end_year"] = years[1]

        # Institution: crude heuristic – line with a capitalized phrase not equal to degree line
        lines = [l.strip() for l in block.split("\n") if l.strip()]
        if lines:
            # try second line first
            if len(lines) > 1:
                entry["institution"] = lines[1]
            else:
                entry["institution"] = lines[0]

        entries.append(entry)

    return entries


DATE_RANGE_REGEX = re.compile(
    r"(?P<start_month>Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?\s+"
    r"(?P<start_year>(19|20)\d{2})"
    r"\s*[-–]\s*"
    r"(?P<end_month>Present|Current|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?\s*"
    r"(?P<end_year>(19|20)\d{2})?",
    re.IGNORECASE
)


def parse_experience_section(section_text: str) -> List[Dict[str, Any]]:
    """
    Simple parser splitting by blank lines; treats each block as a job.
    """
    entries = []
    for block in section_text.split("\n\n"):
        block = block.strip()
        if not block:
            continue

        lines = [l.strip() for l in block.split("\n") if l.strip()]
        if not lines:
            continue

        job = {
            "job_title": None,
            "company": None,
            "start_date": None,
            "end_date": None,
            "description": None,
            "raw": block
        }

        # First line as job/company line
        header_line = lines[0]

        # Try to split by " - " to separate title vs company
        if " - " in header_line:
            parts = [p.strip() for p in header_line.split(" - ", 1)]
            job["job_title"] = parts[0]
            job["company"] = parts[1]
        else:
            job["job_title"] = header_line

        # Find any date range in block
        m = DATE_RANGE_REGEX.search(block)
        if m:
            job["start_date"] = f"{m.group('start_month')} {m.group('start_year')}"
            if m.group('end_year'):
                job["end_date"] = f"{m.group('end_month')} {m.group('end_year')}"
            else:
                job["end_date"] = m.group('end_month')  # e.g., "Present"

        # Description as rest
        if len(lines) > 1:
            job["description"] = "\n".join(lines[1:])
        entries.append(job)

    return entries


def extract_summary(section_text: str) -> str:
    return section_text.strip()


def parse_resume(text: str) -> Dict[str, Any]:
    """
    Main entry point: raw text -> structured dict
    """
    cleaned = clean_text(text)
    doc = nlp(cleaned)
    sections = split_into_sections(cleaned)

    header_text = sections.get("header", cleaned)
    skills_text = sections.get("skills", sections.get("technical skills", cleaned))
    education_text = sections.get("education", "")
    experience_text = (
        sections.get("work experience")
        or sections.get("professional experience")
        or sections.get("experience", "")
    )
    summary_text = sections.get("summary", sections.get("profile", ""))

    result = {
        "name": extract_name(doc),
        "email": extract_email(cleaned),
        "phone": extract_phone(cleaned),
        "summary": extract_summary(summary_text) if summary_text else None,
        "skills": extract_skills(skills_text),
        "education": parse_education_section(education_text) if education_text else [],
        "experience": parse_experience_section(experience_text) if experience_text else [],
        "raw_sections": sections,  # useful for debugging
    }

    return result

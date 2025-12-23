import json
from io import StringIO
from typing import List, Dict, Any

import streamlit as st
import pandas as pd

from parser import extract_text, parse_resume


st.set_page_config(
    page_title="Smart Resume Parser",
    layout="wide",
)


def make_flat_row(file_name: str, parsed: Dict[str, Any]) -> Dict[str, Any]:
    """
    Flatten JSON into a single-row summary suitable for CSV.
    """
    skills = ", ".join(parsed.get("skills", []))

    # Join education entries into a concise string
    edu_parts = []
    for e in parsed.get("education", []):
        part = []
        if e.get("degree"):
            part.append(e["degree"])
        if e.get("institution"):
            part.append(f"@ {e['institution']}")
        if e.get("end_year"):
            part.append(f"({e.get('start_year', '')}-{e['end_year']})")
        edu_parts.append(" ".join(part).strip())
    edu_str = " | ".join(edu_parts)

    # Join experience entries into a concise string
    exp_parts = []
    for x in parsed.get("experience", []):
        header = []
        if x.get("job_title"):
            header.append(x["job_title"])
        if x.get("company"):
            header.append(f"@ {x['company']}")
        if x.get("start_date") or x.get("end_date"):
            header.append(f"({x.get('start_date', '')} - {x.get('end_date', '')})")
        exp_parts.append(" ".join(header).strip())
    exp_str = " | ".join(exp_parts)

    return {
        "file_name": file_name,
        "name": parsed.get("name"),
        "email": parsed.get("email"),
        "phone": parsed.get("phone"),
        "skills": skills,
        "education": edu_str,
        "experience": exp_str,
    }


def main():
    st.title("📄 Smart Resume Parser")
    st.markdown(
        " Please Upload PDF or DOCX resumes to extract **skills, education, experience, and contact info**."
    )

    uploaded_files = st.file_uploader(
        "Upload one or more resumes (PDF/DOCX)",
        type=["pdf", "docx"],
        accept_multiple_files=True,
    )

    if not uploaded_files:
        st.info("Upload some resumes to get started.")
        return

    parsed_results: List[Dict[str, Any]] = []
    flat_rows: List[Dict[str, Any]] = []

    for file in uploaded_files:
        file_bytes = file.read()
        try:
            text = extract_text(file.name, file_bytes)
        except Exception as e:
            st.error(f"Error reading {file.name}: {e}")
            continue

        parsed = parse_resume(text)
        parsed_results.append({"file_name": file.name, "parsed": parsed})
        flat_rows.append(make_flat_row(file.name, parsed))

    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["Summary Table", "Per-Resume JSON", "Raw Text / Sections"])

    with tab1:
        st.subheader("Summary Table")
        df = pd.DataFrame(flat_rows)
        st.dataframe(df, use_container_width=True)

        # Download aggregated CSV
        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index=False)
        st.download_button(
            label="⬇️ Download CSV (all resumes)",
            data=csv_buffer.getvalue(),
            file_name="parsed_resumes_summary.csv",
            mime="text/csv",
        )

    with tab2:
        st.subheader("Per-Resume JSON")
        for item in parsed_results:
            file_name = item["file_name"]
            parsed = item["parsed"]

            with st.expander(f"JSON: {file_name}", expanded=False):
                st.json(parsed)

                # Download JSON button
                json_str = json.dumps(parsed, indent=2)
                st.download_button(
                    label=f"Download JSON for {file_name}",
                    data=json_str,
                    file_name=f"{file_name}_parsed.json",
                    mime="application/json",
                )

    with tab3:
        st.subheader("Raw Sections (for debugging/tuning)")
        for item in parsed_results:
            file_name = item["file_name"]
            parsed = item["parsed"]
            raw_sections = parsed.get("raw_sections", {})

            with st.expander(f"Sections: {file_name}", expanded=False):
                for sec_name, sec_text in raw_sections.items():
                    st.markdown(f"**{sec_name.upper()}**")
                    st.text(sec_text)
                    st.markdown("---")


if __name__ == "__main__":
    main()
